from aiogram import Bot
from aiogram.dispatcher import Dispatcher
import os
from aiogram.contrib.fsm_storage.memory import MemoryStorage

storage = MemoryStorage()

bot = Bot(token='5452871047:AAEYq4XgeLe0ykBqkQA1iiEL0zN3Sc2zDdY')
dp = Dispatcher(bot, storage=storage)