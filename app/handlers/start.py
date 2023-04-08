from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler

from app.db import get_users_db
from app.crud import get_or_create_user, get_user_active_mailbox
from app.models import MailboxSchema
from app.handlers.mailbox import choose_mailbox


async def start(client: Client, message: Message):
    await message.reply_text(f"Hello! I'm your email bot!")
    with get_users_db() as users_db:
        user = get_or_create_user(users_db, message.from_user.id)
        if user.active_mailbox_id:
            mailbox = get_user_active_mailbox(users_db, user).to_dict()
            client.user_mailbox = MailboxSchema(**mailbox)
            await message.reply_text(f"Your active mailbox is {client.user_mailbox.email}")
        else:
            client.user_mailbox = await choose_mailbox(client, message)


start_handler = MessageHandler(start, filters.command("start") & filters.private)