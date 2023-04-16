from pyrogram import Client
from pyrogram.types import Message

from app.db import MailboxNotExistsError
from app.handlers.mailbox import set_user_mailbox


def handle_mailbox_not_exists(func):
    async def wrapper(client: Client, message: Message):
        try:
            await func(client, message)
        except MailboxNotExistsError:
            await set_user_mailbox(client, message)
            await func(client, message)

    return wrapper
