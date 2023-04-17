from datetime import date

from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

from app.crud import update_mailbox
from app.db import get_mail_db, get_users_db
from app.handlers.decorators import handle_mailbox_not_exists
from app.mailing_tools import gather_messages_since_date, get_mailbox

LAST_UPDATE_DEFAULT = date(2023, 3, 20)


@handle_mailbox_not_exists
def update_email(client: Client, message: Message):
    print("update_email")
    mailbox_schema = client.users_mailboxes[message.from_user.id]
    with get_mailbox(mailbox_schema) as mb, get_mail_db(mailbox_schema) as mail_db:
        if mailbox_schema.last_update is None:
            mailbox_schema.last_update = LAST_UPDATE_DEFAULT

        last_update = mailbox_schema.last_update
        gather_messages_since_date(mail_db, mb, last_update)
        mailbox_schema.last_update = date.today()

    with get_users_db() as users_db:
        update_mailbox(users_db, mailbox_schema)


async def schedule_email_update(client: Client, message: Message):
    print("schedule_email_update")
    if hasattr(client, "email_update_job"):
        await message.reply_text("There is already an email update job scheduled.")
        return
    client.email_update_job = client.scheduler.add_job(update_email, args=[client, message], trigger="interval", seconds=60)
    await message.reply_text("Email update job scheduled.")


schedule_email_update_handler = MessageHandler(
    schedule_email_update, filters.command("schedule_email_update") & filters.private
)


async def remove_scheduled_email_update(client: Client, message: Message):
    print("remove_scheduled_email_update")
    if hasattr(client, "email_update_job"):
        client.email_update_job.remove()
        del client.email_update_job
        await message.reply_text("Email update job removed.")
    else:
        await message.reply_text("There is no email update job to remove.")


remove_scheduled_email_update_handler = MessageHandler(
    remove_scheduled_email_update, filters.command("remove_scheduled_email_update") & filters.private
)
