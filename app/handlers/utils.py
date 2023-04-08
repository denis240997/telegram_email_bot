import asyncio

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler



async def field_request(client: Client, message: Message, field_name: str, prompt: str):
    user_input = asyncio.Future()
    client.futures[f'awaiting_{field_name}'] = user_input
    await message.reply_text(prompt)
    field = await user_input
    print(f"{field_name.upper()}: {field}")

    return field


def awaiting_field_filter(field_name: str) -> filters.Filter:
    async def func(filter, client, _) -> bool:
        return bool(client.futures.get(f'awaiting_{filter.field_name}'))

    return filters.create(func, field_name=field_name)


def get_field_handler(field_name: str) -> MessageHandler:

    async def func(client: Client, message: Message):
        print(f"process_{field_name}")
        client.futures[f'awaiting_{field_name}'].set_result(message.text)
        del client.futures[f'awaiting_{field_name}']

    return MessageHandler(func, awaiting_field_filter(field_name))