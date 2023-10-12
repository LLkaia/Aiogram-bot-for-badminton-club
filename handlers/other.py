from aiogram import types, Dispatcher
from create_bot import dp, bot
from keyboards import kb_client
from handlers.client import in_chat
from data_base import sqlite_db

async def other_message(message : types.Message):
    if message.chat.type == 'private':
        if await in_chat(message.from_user.id):
            await message.answer('Бот виконує задачі при натисканні на кнопки.', reply_markup=kb_client)
            if not sqlite_db.user_exists(message.from_user.id):
                sqlite_db.add_user(message.from_user.id)

def register_handlers_other(dp : Dispatcher):
    dp.register_message_handler(other_message)