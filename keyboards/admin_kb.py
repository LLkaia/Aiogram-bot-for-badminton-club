from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

b1 = KeyboardButton('Додати нове тренування')
b2 = KeyboardButton('Видалити тренування')
b3 = KeyboardButton('🛑 ВІДМІНА (я передумав це робити, а бот чекає)')
b4 = KeyboardButton('Розпочати новий тиждень')
b5 = KeyboardButton('⬅️ Назад')

button_case_admin = ReplyKeyboardMarkup(resize_keyboard=True).row(b1, b2).add(b4).add(b3).add(b5)
