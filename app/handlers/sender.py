from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

from app.crud import get_or_create_sender
from app.db import get_mail_db
from app.handlers.decorators import handle_mailbox_not_exists
from app.handlers.utils import field_request, get_field_handler
from app.models import SenderCreateSchema


@handle_mailbox_not_exists
async def add_sender(client: Client, message: Message):
    print("add_sender")
    mailbox_schema = client.users_mailboxes[message.from_user.id]
    with get_mail_db(mailbox_schema) as mail_db:
        sender_email = await field_request(client, message, "sender_email", "Enter sender email:")
        new_sender = SenderCreateSchema(email=sender_email)
        sender = get_or_create_sender(mail_db, new_sender)

        await message.reply_text(f"Sender {sender.email} has been added to mailbox {mailbox_schema.email}.")


add_sender_handler = MessageHandler(add_sender, filters.command("add_sender") & filters.private)
process_sender_email_handler = get_field_handler("sender_email")
