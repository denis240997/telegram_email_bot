import os
from collections import defaultdict

import uvloop
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram import Client
from pyrogram.types import BotCommand

from app.handlers import mail_tasks, mailbox, notifications, sender, start
from app.handlers.mailbox import upload_users_active_mailboxes

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
    # test.test_handler,
    mail_tasks.schedule_email_update_handler,
    mail_tasks.remove_scheduled_email_update_handler,
]

for handler in handlers:
    app.add_handler(handler)


notifications.register_notifications(app)


commands = [
    BotCommand("start", "Get started"),
    BotCommand("add_mailbox", "Add new mailbox"),
    BotCommand("choose_mailbox", "Choose mailbox"),
    BotCommand("remove_mailbox", "Remove mailbox"),
    # BotCommand("add_sender", "Add sender to mailbox"),
    
    BotCommand("schedule_email_update", "Schedule email update"),
    BotCommand("remove_scheduled_email_update", "Remove scheduled email update"),
]


if __name__ == "__main__":
    app.scheduler = AsyncIOScheduler()
    app.scheduler.start()
    app.users_mailboxes = defaultdict(lambda: None)
    app.email_update_jobs = {}
    upload_users_active_mailboxes(app)
    app.futures = {}    # персонализировать!
    app.commands = commands
    app.run()
