import asyncio

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.handlers import MessageHandler, CallbackQueryHandler

from app.db import get_users_db
from app.crud import get_or_create_user, get_user_mailboxes, get_mailbox_by_id, set_user_active_mailbox, create_mailbox
from app.models import Mailbox, MailboxSchema, MailboxCreateSchema
from app.handlers.state import user_mailbox


user_futures = {}


def generate_mailbox_keyboard(mailbox_list: list[Mailbox]) -> InlineKeyboardMarkup:
    print("generate_mailbox_keyboard")
    keyboard = []
    for mailbox in mailbox_list:
        keyboard.append([InlineKeyboardButton(mailbox.email, callback_data=f'mailbox_{mailbox.mailbox_id}')])

    return InlineKeyboardMarkup(keyboard)


async def choose_mailbox(client: Client, message: Message) -> MailboxSchema or None:
    print("choose_mailbox")
    user_choice = asyncio.Future()
    with get_users_db() as users_db:
        user = get_or_create_user(users_db, message.from_user.id)
        mailbox_list = get_user_mailboxes(user)
        if mailbox_list:
            sent_message = await message.reply_text("Choose a mailbox:", reply_markup=generate_mailbox_keyboard(mailbox_list))
            user_futures[sent_message.id] = user_choice
            chosen_mailbox = await user_choice
            return chosen_mailbox
        else:
            await message.reply_text("You don't have any mailboxes yet. Type /add_mailbox command to add one.")
            return None
        

choose_mailbox_handler = MessageHandler(choose_mailbox, filters.command("choose_mailbox") & filters.private)


async def process_mailbox_choice(client: Client, callback_query: CallbackQuery) -> MailboxSchema:
    print("process_mailbox_choice")
    mailbox_id = int(callback_query.data.split('_')[1])
    with get_users_db() as users_db:
        mailbox = get_mailbox_by_id(users_db, mailbox_id).to_dict()
        user_mailbox.set(MailboxSchema(**mailbox))
        user = get_or_create_user(users_db, callback_query.from_user.id)
        set_user_active_mailbox(users_db, user, mailbox_id)

    message_id = callback_query.message.id
    user_futures[message_id].set_result(user_mailbox.get())
    del user_futures[message_id]

    await callback_query.answer(f'You have chosen {user_mailbox.get().email}')    # top panel alert
    await callback_query.message.edit_text(f'You have chosen {user_mailbox.get().email}')

    return user_mailbox.get()


process_mailbox_choice_handler = CallbackQueryHandler(process_mailbox_choice, filters.regex('^mailbox_'))


async def field_request(client: Client, message: Message, field_name: str, prompt: str):
    user_input = asyncio.Future()
    client.state[f'awaiting_{field_name}'] = True
    await message.reply_text(prompt)
    user_futures[f'awaiting_{field_name}'] = user_input
    field = await user_input
    print(f"{field_name.upper()}: {field}")

    return field


async def add_mailbox(client: Client, message: Message):
    print("add_mailbox")
    email = await field_request(client, message, 'email', "Enter your email address:")
    password = await field_request(client, message, 'password', "Enter your password:")

    new_mailbox = MailboxCreateSchema(
        email=email,
        password=password
    )

    with get_users_db() as users_db:
        user = get_or_create_user(users_db, message.from_user.id)
        mailbox = create_mailbox(users_db, user, new_mailbox).to_dict()
        user_mailbox.set(MailboxSchema(**mailbox))
        set_user_active_mailbox(users_db, user, user_mailbox.get().mailbox_id)

    await message.reply_text(f'You have added {user_mailbox.get().email} as your mailbox.')


create_mailbox_handler = MessageHandler(add_mailbox, filters.command("add_mailbox") & filters.private)


def awaiting_field_filter(field_name: str) -> filters.Filter:
    async def func(filter, client, _) -> bool:
        return client.state.get(f'awaiting_{filter.field_name}', False)

    return filters.create(func, field_name=field_name)


def get_field_handler(field_name: str) -> MessageHandler:

    async def func(client: Client, message: Message):
        print(f"process_{field_name}")
        del client.state[f'awaiting_{field_name}']
        user_futures[f'awaiting_{field_name}'].set_result(message.text)
        del user_futures[f'awaiting_{field_name}']

    return MessageHandler(func, awaiting_field_filter(field_name))


process_email_handler = get_field_handler('email')
process_password_handler = get_field_handler('password')
