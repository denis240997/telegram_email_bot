from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

from app.handlers.decorators import handle_mailbox_not_exists


@handle_mailbox_not_exists
async def start(client: Client, message: Message):
    await client.set_bot_commands(client.commands)
    await message.reply_text("Hello! I'm your email bot!")


start_handler = MessageHandler(start, filters.command("start") & filters.private)
