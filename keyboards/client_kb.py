from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

b1 = KeyboardButton('📍 Де нас знайти')
b2 = KeyboardButton('📝 Записатись')
b3 = KeyboardButton('👟 Тренування на цьому тижні')
b4 = KeyboardButton('🛑 ВІДМІНА (я передумав це робити, а бот чекає)')
b5 = KeyboardButton('✍️ Мої записи')
b6 = KeyboardButton('🏃 Виписатись')
b7 = KeyboardButton('🤓 Хто записаний на тренування')
#b4 = KeyboardButton('Поділитись номером', request_contact=True)
#b5 = KeyboardButton('Показати де я', request_location=True)

kb_client = ReplyKeyboardMarkup(resize_keyboard=True)  #клава по размеру текста, one_time_keyboard = True клавиатура прячется после нажатия

# .add() - с новой строки, .insert() - в строку, если есть место, .row() - все аргументы в одну строку
kb_client.row(b3, b2).add(b4).row(b5, b6).row(b7, b1)