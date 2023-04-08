from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler

from app.db import get_mail_db
from app.crud import get_or_create_sender
from app.models import SenderCreateSchema
from app.handlers.utils import field_request, get_field_handler



async def add_sender(client: Client, message: Message):
    print("add_sender")
    mailbox = client.user_mailbox
    if not mailbox:
        await message.reply_text("You don't have active mailbox yet. Type /choose_mailbox command to choose one.")
        return

    with get_mail_db(mailbox) as mail_db:
        sender_email = await field_request(client, message, "sender_email", "Enter sender email:")
        new_sender = SenderCreateSchema(email=sender_email)
        sender = get_or_create_sender(mail_db, new_sender)

        await message.reply_text(f"Sender {sender.email} has been added to mailbox {mailbox.email}.")


add_sender_handler = MessageHandler(add_sender, filters.command("add_sender") & filters.private)
process_sender_email_handler = get_field_handler("sender_email")
