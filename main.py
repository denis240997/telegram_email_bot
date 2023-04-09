import os

import uvloop
from pyrogram import Client
from pyrogram.types import BotCommand

from app.handlers import mailbox, sender, start

# Pyrogram Client credentials
API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Pyrogram Client
uvloop.install()
app = Client(
    "AAtgmailBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)


handlers = [
    start.start_handler,
    mailbox.choose_mailbox_handler,
    mailbox.process_mailbox_choice_handler,
    mailbox.create_mailbox_handler,
    mailbox.process_email_handler,
    mailbox.process_password_handler,
    sender.add_sender_handler,
    sender.process_sender_email_handler,
]

for handler in handlers:
    app.add_handler(handler)

commands = [
    BotCommand("start", "Get started"),
    BotCommand("choose_mailbox", "Choose mailbox"),
    BotCommand("add_mailbox", "Add new mailbox"),
    BotCommand("add_sender", "Add sender to mailbox"),
]


if __name__ == "__main__":
    app.mailbox = None
    app.futures = {}
    app.commands = commands
    app.run()
