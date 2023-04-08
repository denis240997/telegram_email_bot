from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler

from app.db import get_users_db
from app.crud import get_or_create_user, get_mailbox_by_id
from app.models import MailboxSchema
from app.handlers.mailbox import choose_mailbox
from app.handlers.setup import user_mailbox


async def start(client: Client, message: Message):
    global user_mailbox
    await message.reply_text(f"Hello! I'm your email bot!")
    if not user_mailbox.data:    
        with get_users_db() as users_db:
            user = get_or_create_user(users_db, message.from_user.id)
            if user.active_mailbox_id:
                mailbox = get_mailbox_by_id(users_db, user.active_mailbox_id).to_dict()
                user_mailbox.data = MailboxSchema(**mailbox)
            else:
                user_mailbox.data = await choose_mailbox(client, message)
                # It's needed to wait here choose_mailbox somehow

    await message.reply_text(f"Your active mailbox is {user_mailbox.data.email}")


start_handler = MessageHandler(start, filters.command("start") & filters.private)