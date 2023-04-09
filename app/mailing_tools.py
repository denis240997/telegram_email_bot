from contextlib import contextmanager
from datetime import date

# https://github.com/ikvk/imap_tools
from imap_tools import A, MailBox, MailMessage
from sqlalchemy.orm.session import Session

from app.crud import create_message, get_or_create_sender, message_exists
from app.models import Message, MessageCreateSchema, SenderCreateSchema


@contextmanager
def get_mailbox(imap_server_url: str, imap_port: int, email: str, password: str, mail_folder: str) -> MailBox:
    mb = MailBox(imap_server_url, imap_port)
    mb.login(email, password, mail_folder)
    try:
        yield mb
    finally:
        mb.logout()


def get_unseen_messages(mb: MailBox) -> list[MailMessage]:
    return mb.fetch(criteria="UNSEEN", mark_seen=False, reverse=True)


def get_messages_since_date(mb: MailBox, date: date) -> list[MailMessage]:
    return mb.fetch(A(date_gte=date), mark_seen=False, reverse=True)


def parse_message(mail_db: Session, msg: MailMessage) -> Message:
    # if message_exists(mail_db, msg.uid):
    #     return get_message_by_uid(mail_db, msg.uid)
    sender_schema = SenderCreateSchema(email=msg.from_values.email, name=msg.from_values.name)
    sender = get_or_create_sender(mail_db, sender_schema)
    message_schema = MessageCreateSchema(
        uid=msg.uid, sender_id=sender.sender_id, subject=msg.subject, content=msg.text or msg.html, date=msg.date
    )
    message = create_message(mail_db, message_schema)
    return message


def process_unseen_messages(mail_db: Session, mb: MailBox) -> None:
    for msg in get_unseen_messages(mb):
        if message_exists(mail_db, msg.uid):
            continue
        parse_message(mail_db, msg)


def process_messages_since_date(mail_db: Session, mb: MailBox, date: date) -> None:
    for msg in get_messages_since_date(mb, date):
        if message_exists(mail_db, msg.uid):
            continue
        parse_message(mail_db, msg)
