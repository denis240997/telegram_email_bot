import os

import uvloop
from pyrogram import Client

from app.handlers import start, mailbox, sender


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


if __name__ == "__main__":
    app.mailbox = None
    app.futures = {}
    app.run()
