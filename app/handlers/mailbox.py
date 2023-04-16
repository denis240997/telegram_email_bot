import asyncio
from enum import Enum as PyEnum

from pyrogram import Client, filters
from pyrogram.handlers import CallbackQueryHandler, MessageHandler
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from app.crud import (
    create_mailbox,
    delete_mailbox_by_id,
    get_mailbox_by_id,
    get_or_create_user,
    get_user_active_mailbox,
    get_user_mailboxes,
    set_user_active_mailbox,
)
from app.db import get_users_db
from app.handlers.utils import field_request, get_field_handler
from app.mailing_tools import get_imap_server_by_email
from app.models import Mailbox, MailboxCreateSchema, MailboxSchema


class MailboxKeyboardMethods(PyEnum):
    CHOOSE = "choose"
    UPDATE = "update"
    DELETE = "delete"


def generate_mailbox_keyboard(mailbox_list: list[Mailbox], method: str) -> InlineKeyboardMarkup:
    print("generate_mailbox_keyboard")
    keyboard = []
    for mailbox in mailbox_list:
        keyboard.append([InlineKeyboardButton(mailbox.email, callback_data=f"mailbox_{method}_{mailbox.mailbox_id}")])

    return InlineKeyboardMarkup(keyboard)


async def choose_mailbox(client: Client, message: Message) -> MailboxSchema or None:
    print("choose_mailbox")
    user_choice = asyncio.Future()
    with get_users_db() as users_db:
        user = get_or_create_user(users_db, message.from_user.id)
        mailbox_list = get_user_mailboxes(user)
        if mailbox_list:
            sent_message = await message.reply_text(
                "Choose a mailbox:", reply_markup=generate_mailbox_keyboard(mailbox_list, MailboxKeyboardMethods.CHOOSE)
            )
            client.futures[sent_message.id] = user_choice
            chosen_mailbox = await user_choice
            return chosen_mailbox
        else:
            await message.reply_text("You don't have any mailboxes yet. Type /add_mailbox command to add one.")
            return None


choose_mailbox_handler = MessageHandler(choose_mailbox, filters.command("choose_mailbox") & filters.private)


async def remove_mailbox(client: Client, message: Message):
    print("remove_mailbox")
    with get_users_db() as users_db:
        user = get_or_create_user(users_db, message.from_user.id)
        mailbox_list = get_user_mailboxes(user)
        if mailbox_list:
            await message.reply_text(
                "Choose a mailbox to remove:", reply_markup=generate_mailbox_keyboard(mailbox_list, MailboxKeyboardMethods.DELETE)
            )
        else:
            await message.reply_text("You don't have any mailboxes yet. Type /add_mailbox command to add one.")


remove_mailbox_handler = MessageHandler(remove_mailbox, filters.command("remove_mailbox") & filters.private)


async def process_mailbox_choice(client: Client, callback_query: CallbackQuery):
    print("process_mailbox_choice")
    method = callback_query.data.split("_")[1]
    mailbox_id = int(callback_query.data.split("_")[2])
    with get_users_db() as users_db:
        user = get_or_create_user(users_db, callback_query.from_user.id)
        mailbox = get_mailbox_by_id(users_db, mailbox_id)
        selected_mailbox = MailboxSchema(**mailbox.to_dict())
        if method == MailboxKeyboardMethods.CHOOSE:
            client.user_mailbox = selected_mailbox
            set_user_active_mailbox(users_db, user, mailbox_id)

            message_id = callback_query.message.id
            client.futures[message_id].set_result(client.user_mailbox)
            del client.futures[message_id]

            await callback_query.answer(f"You have chosen {client.user_mailbox.email}")
            await callback_query.message.edit_text(f"You have chosen {client.user_mailbox.email}")

        elif method == MailboxKeyboardMethods.DELETE:
            if get_user_active_mailbox(users_db, user).mailbox_id == mailbox_id:
                client.user_mailbox = None
                set_user_active_mailbox(users_db, user, None)

            delete_mailbox_by_id(users_db, mailbox_id)
            await callback_query.answer(f"You have deleted {selected_mailbox.email}")
            await callback_query.message.edit_text(f"You have deleted {selected_mailbox.email}")


process_mailbox_choice_handler = CallbackQueryHandler(process_mailbox_choice, filters.regex("^mailbox_"))


async def add_mailbox(client: Client, message: Message):
    print("add_mailbox")
    email = await field_request(client, message, "email", "Enter your email address:")
    password = await field_request(client, message, "password", "Enter your password:")
    imap_server_url = get_imap_server_by_email(email)
    if not imap_server_url:
        imap_server_url = await field_request(client, message, "imap_server_url", "Enter your IMAP server URL:")

    new_mailbox = MailboxCreateSchema(email=email, password=password, imap_server_url=imap_server_url)

    with get_users_db() as users_db:
        user = get_or_create_user(users_db, message.from_user.id)
        mailbox = create_mailbox(users_db, user, new_mailbox).to_dict()
        client.user_mailbox = MailboxSchema(**mailbox)
        set_user_active_mailbox(users_db, user, client.user_mailbox.mailbox_id)

    await message.reply_text(f"You have added {client.user_mailbox.email} as your mailbox.")


create_mailbox_handler = MessageHandler(add_mailbox, filters.command("add_mailbox") & filters.private)


process_email_handler = get_field_handler("email")
process_password_handler = get_field_handler("password")
process_imap_server_handler = get_field_handler("imap_server_url")


async def set_user_mailbox(client: Client, message: Message):
    with get_users_db() as users_db:
        user = get_or_create_user(users_db, message.from_user.id)
        if user.active_mailbox_id:
            mailbox = get_user_active_mailbox(users_db, user).to_dict()
            client.user_mailbox = MailboxSchema(**mailbox)
            await message.reply_text(f"Your active mailbox is {client.user_mailbox.email}")
        else:
            client.user_mailbox = await choose_mailbox(client, message)
