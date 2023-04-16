import re
from contextlib import contextmanager
from datetime import date

from bs4 import BeautifulSoup

# https://github.com/ikvk/imap_tools
from imap_tools import AND
from imap_tools import MailBox as MailboxClient
from imap_tools import MailMessage
from sqlalchemy.orm.session import Session

from app.crud import (
    add_items_to_order,
    add_cdek_number_to_order,
    assign_order_to_message,
    get_messages_by_sender_with_status,
    get_or_create_item,
    get_or_create_message,
    get_or_create_order,
    get_or_create_sender,
    get_order_by_number,
    mark_message_processed,
    message_exists,
)
from app.models import (
    ItemCreateSchema,
    MailboxSchema,
    Message,
    MessageCreateSchema,
    MessageStatus,
    OrderCreateSchema,
    OrderStatus,
    SenderCreateSchema,
)


def get_imap_server_by_email(email: str) -> str or None:
    imap_servers_table = {
        "gmail.com": "imap.gmail.com",
        "yandex.ru": "imap.yandex.ru",
        "mail.ru": "imap.mail.ru",  # fetch criteria is not supported by mail.ru))))
        "outlook.com": "imap-mail.outlook.com",
    }
    domain = email.split("@")[1]
    return imap_servers_table.get(domain, None)


@contextmanager
def get_mailbox(mailbox: MailboxSchema) -> MailboxClient:
    mb = MailboxClient(mailbox.imap_server_url, mailbox.imap_port)
    mb.login(mailbox.email, mailbox.password, mailbox.mail_folder)
    try:
        yield mb
    finally:
        mb.logout()


def get_unseen_messages(mb: MailboxClient) -> list[MailMessage]:
    return mb.fetch(criteria="UNSEEN", mark_seen=False)


def get_messages_since_date(mb: MailboxClient, date: date) -> list[MailMessage]:
    return mb.fetch(AND(date_gte=date), mark_seen=False)


def get_message_from_sender(mb: MailboxClient, sender_email: str) -> list[MailMessage]:
    return mb.fetch(AND(from_=sender_email), mark_seen=False)


def get_message_from_sender_since_date(mb: MailboxClient, sender_email: str, date: date) -> list[MailMessage]:
    return mb.fetch(AND(from_=sender_email, date_gte=date), mark_seen=False)

def parse_message(mail_db: Session, msg: MailMessage) -> Message:
    sender_schema = SenderCreateSchema(email=msg.from_values.email, name=msg.from_values.name)
    sender = get_or_create_sender(mail_db, sender_schema)

    message_schema = MessageCreateSchema(
        uid=msg.uid, 
        sender_id=sender.sender_id, 
        subject=msg.subject, 
        content=msg.text or msg.html, 
        date=msg.date, 
        status=MessageStatus.UNPROCESSED
    )
    message = get_or_create_message(mail_db, message_schema)
    return message


def gather_messages_since_date(mail_db: Session, mb: MailboxClient, date: date) -> None:
    for msg in get_messages_since_date(mb, date):
        if message_exists(mail_db, msg.uid):
            print(f"Message with uid {msg.uid} already exists in database. Skipping...")
            continue
        print(f"Processing message with uid {msg.uid}...")
        parse_message(mail_db, msg)


def wildberries_processor(mail_db: Session):
    WB_EMAIL = "noreply@tilda.ws"
    sender = get_or_create_sender(mail_db, SenderCreateSchema(email=WB_EMAIL))
    for message in get_messages_by_sender_with_status(mail_db, sender, MessageStatus.UNPROCESSED):
        if message.subject != "New order [inneme.ru]":
            continue

        soup = BeautifulSoup(message.content, "html.parser")

        title_regex = re.compile(r"(.+?)\s*\((.+)\)")
        order_regex = re.compile(r"Order\s*#(\d+)")
        price_regex = re.compile(r"(\d+)\s*RUB")
        phone_regex = re.compile(r"Phone:\s*(.+)")

        order_number = order_regex.search(soup.text).groups()[0]

        phone = tuple(soup.find(text="Purchaser information:").parent.next_siblings)[4].strip()
        phone = phone_regex.match(phone).groups()[0]

        items = []
        item_rows = soup.find("table").find_all("tr", valign="middle")[1:]
        for row in item_rows:
            title, price, amount = (td.text.strip() for td in row.find_all("td")[2:5])
            name, description = title_regex.match(title).groups()
            sku, *props = [s.strip() for s in description.split(",")]
            size, color = None, None
            for prop in props:
                prop_name, prop_value = [s.strip() for s in prop.split(":")]
                if prop_name == "Размер":
                    size = prop_value
                elif prop_name == "Цвет":
                    color = prop_value
                else:
                    raise Exception(f"Unknown property {prop_name}={prop_value}")

            price = int(price_regex.match(price).groups()[0])
            amount = int(amount)

            item_schema = ItemCreateSchema(
                sku=sku,
                name=name,
                size=size,
                color=color,
                price=price,
            )
            items.append((get_or_create_item(mail_db, item_schema), amount))

        order_schema = OrderCreateSchema(
            order_number=order_number,
            # cdek_number=,
            status=OrderStatus.CREATED,
            customer_phone=phone,
            # delivery_city=,
        )
        order = get_or_create_order(mail_db, order_schema)
        order = add_items_to_order(mail_db, order, items)

        message = assign_order_to_message(mail_db, message, order)
        message = mark_message_processed(mail_db, message)


def cdek_processor(mail_db: Session):
    CDEK_EMAIL = "noreply@cdek.ru"
    sender = get_or_create_sender(mail_db, SenderCreateSchema(email=CDEK_EMAIL))
    for message in get_messages_by_sender_with_status(mail_db, sender, MessageStatus.UNPROCESSED):

        # soup = BeautifulSoup(message.content, "html.parser")

        cdek_subject_regex = re.compile(r"Зарегистрирован заказ (\d+) \((.+)\)")
        subject_match = cdek_subject_regex.match(message.subject)
        if subject_match:
            cdek_number, order_number = subject_match.groups()
            # print(cdek_number, order_number)

            order = get_order_by_number(mail_db, order_number)
            if order is None:
                # print(f"Order with number {order_number} not found in database. Skipping...")
                continue

            order = add_cdek_number_to_order(mail_db, order, cdek_number)
            message = assign_order_to_message(mail_db, message, order)

        message = mark_message_processed(mail_db, message)


def process_messages(mail_db: Session):
    wildberries_processor(mail_db)
    cdek_processor(mail_db)
