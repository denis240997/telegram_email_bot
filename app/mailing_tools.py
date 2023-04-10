import re
from contextlib import contextmanager
from datetime import date

from bs4 import BeautifulSoup

# https://github.com/ikvk/imap_tools
from imap_tools import AND
from imap_tools import MailBox as MailboxClient
from imap_tools import MailMessage
from sqlalchemy.orm.session import Session

from app.crud import get_or_create_message, get_or_create_sender, message_exists
from app.models import (
    MailboxSchema,
    Message,
    MessageCreateSchema,
    Sender,
    SenderCreateSchema,
)

MIN_DATE = date(2023, 1, 1)
WB_EMAIL = "noreply@tilda.ws"
CDEK_EMAIL = "noreply@cdek.ru"


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
    return mb.fetch(criteria="UNSEEN", mark_seen=False, reverse=True)


def get_messages_since_date(mb: MailboxClient, date: date) -> list[MailMessage]:
    return mb.fetch(AND(date_gte=date), mark_seen=False, reverse=True)


def get_message_from_sender(mb: MailboxClient, sender_email: str) -> list[MailMessage]:
    return mb.fetch(AND(from_=sender_email), mark_seen=False, reverse=True)


def get_message_from_sender_since_date(mb: MailboxClient, sender_email: str, date: date) -> list[MailMessage]:
    return mb.fetch(AND(from_=sender_email, date_gte=date), mark_seen=False, reverse=True)


def parse_message(mail_db: Session, msg: MailMessage, sender: Sender = None) -> Message:
    # if message_exists(mail_db, msg.uid):
    #     return get_message_by_uid(mail_db, msg.uid)
    if not sender:
        sender_schema = SenderCreateSchema(email=msg.from_values.email, name=msg.from_values.name)
        sender = get_or_create_sender(mail_db, sender_schema)

    message_schema = MessageCreateSchema(
        uid=msg.uid, sender_id=sender.sender_id, subject=msg.subject, content=msg.text or msg.html, date=msg.date
    )

    if sender.email == WB_EMAIL:
        print("#############################################")
        print(sender.email)
        soup = BeautifulSoup(message_schema.content, "html.parser")

        order_regex = re.compile(r"Order\s*#(\d+)")
        price_regex = re.compile(r"(\d+)\s*RUB")
        phone_regex = re.compile(r"Phone:\s*(.+)")

        order = order_regex.search(soup.text).groups()[0]
        print(order)

        phone = tuple(soup.find(text="Purchaser information:").parent.next_siblings)[4].strip()
        phone = phone_regex.match(phone).groups()[0]
        print(phone)

        item_rows = soup.find("table").find_all("tr", valign="middle")[1:]
        for row in item_rows:
            name, price, amount = (td.text.strip() for td in item_rows[0].find_all("td")[2:5])
            price = int(price_regex.match(price).groups()[0])
            amount = int(amount)

            print(name, price, amount, sep="\n")
            print()

    elif sender.email == CDEK_EMAIL:
        cdek_subject_regex = re.compile(r"Зарегистрирован заказ (\d+) \((.+)\)")
        subject_match = cdek_subject_regex.match(message_schema.subject)
        if subject_match:
            print("#############################################")
            print(sender.email)
            cdek_order, order = subject_match.groups()
            print(cdek_order, order)
            print()

    return

    message = get_or_create_message(mail_db, message_schema)

    return message


def process_unseen_messages(mail_db: Session, mb: MailboxClient) -> None:
    for msg in get_unseen_messages(mb):
        if message_exists(mail_db, msg.uid):
            continue
        parse_message(mail_db, msg)


def process_messages_since_date(mail_db: Session, mb: MailboxClient, date: date) -> None:
    for msg in get_messages_since_date(mb, date):
        if message_exists(mail_db, msg.uid):
            continue
        parse_message(mail_db, msg)
