import os

import uvloop
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram import Client
from pyrogram.types import BotCommand

from app.handlers import mailbox, sender, start, mail_tasks, test


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
    mailbox.remove_mailbox_handler,
    mailbox.process_email_handler,
    mailbox.process_password_handler,
    mailbox.process_imap_server_handler,
    sender.add_sender_handler,
    sender.process_sender_email_handler,
    test.test_handler,
    mail_tasks.schedule_email_update_handler,
    mail_tasks.remove_scheduled_email_update_handler,
]

for handler in handlers:
    app.add_handler(handler)

commands = [
    BotCommand("start", "Get started"),
    BotCommand("add_mailbox", "Add new mailbox"),
    BotCommand("choose_mailbox", "Choose mailbox"),
    BotCommand("remove_mailbox", "Remove mailbox"),
    BotCommand("add_sender", "Add sender to mailbox"),
    
    BotCommand("test", "Test"),
    BotCommand("schedule_email_update", "Schedule email update"),
    BotCommand("remove_scheduled_email_update", "Remove scheduled email update"),
]


if __name__ == "__main__":
    app.scheduler = AsyncIOScheduler()
    app.scheduler.start()
    app.user_mailbox = None
    app.futures = {}
    app.commands = commands
    app.run()
