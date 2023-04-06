import os
import asyncio

import uvloop
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

from app.db import get_users_db, get_mail_db
from app.crud import get_or_create_user, get_user_mailboxes, get_mailbox_by_id, set_user_active_mailbox
from app.models import Mailbox, MailboxSchema


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


user_mailbox = None


@app.on_message(filters.command("start") & filters.private)
async def start(client: Client, message: Message):
    global user_mailbox
    await message.reply_text(f"Hello! I'm your email bot!")
    if not user_mailbox:    
        with get_users_db() as users_db:
            user = get_or_create_user(users_db, message.from_user.id)
            if user.active_mailbox_id:
                mailbox = get_mailbox_by_id(users_db, user.active_mailbox_id).to_dict()
                user_mailbox = MailboxSchema(**mailbox)
            else:
                user_mailbox = await choose_mailbox(client, message)
                # It's needed to wait here choose_mailbox somehow

    await message.reply_text(f"Your active mailbox is {user_mailbox.email}")


def generate_mailbox_keyboard(mailbox_list: list[Mailbox]) -> InlineKeyboardMarkup:
    keyboard = []
    for mailbox in mailbox_list:
        keyboard.append([InlineKeyboardButton(mailbox.email, callback_data=f'mailbox_{mailbox.mailbox_id}')])

    return InlineKeyboardMarkup(keyboard)


@app.on_message(filters.command("choose_mailbox") & filters.private)
async def choose_mailbox(client: Client, message: Message) -> MailboxSchema or None:
    user_choice = asyncio.Future()
    with get_users_db() as users_db:
        user = get_or_create_user(users_db, message.from_user.id)
        mailbox_list = get_user_mailboxes(user)
        if mailbox_list:
            sent_message = await message.reply_text("Choose a mailbox:", reply_markup=generate_mailbox_keyboard(mailbox_list))
            app.user_choice_futures[sent_message.id] = user_choice
            chosen_mailbox = await user_choice
            return chosen_mailbox
        else:
            await message.reply_text("You don't have any mailboxes yet. Type /add_mailbox command to add one.")
            return None


@app.on_callback_query(filters.regex('^mailbox_'))
async def handle_mailbox_choice(client: Client, callback_query: CallbackQuery) -> MailboxSchema:
    global user_mailbox
    mailbox_id = int(callback_query.data.split('_')[1])
    with get_users_db() as users_db:
        mailbox = get_mailbox_by_id(users_db, mailbox_id).to_dict()
        user_mailbox = MailboxSchema(**mailbox)
        user = get_or_create_user(users_db, callback_query.from_user.id)
        set_user_active_mailbox(users_db, user, mailbox_id)

    message_id = callback_query.message.id
    app.user_choice_futures[message_id].set_result(user_mailbox)
    del app.user_choice_futures[message_id]

    await callback_query.answer(f'You have chosen {user_mailbox.email}')    # top panel alert
    await callback_query.message.edit_text(f'You have chosen {user_mailbox.email}')

    return user_mailbox


if __name__ == "__main__":
    app.user_choice_futures = {}
    app.run()
