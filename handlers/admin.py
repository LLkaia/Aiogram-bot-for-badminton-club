from aiogram import types, Dispatcher
from create_bot import dp, bot
from keyboards import admin_kb, kb_client
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from data_base import sqlite_db

ID = [382690791, 5394569401, 612548655]

class FSMAdmin(StatesGroup):
    gym = State()
    day = State()
    time = State()
    free = State()
    des = State()

class FSMDelete(StatesGroup):
    gym = State()

class FSMStart(StatesGroup):
    answer = State()
    data = State()

async def admin_in(message : types.Message):
    if message.from_user.id in ID:
        await message.answer('Бот уважно слухає адміна!', reply_markup=admin_kb.button_case_admin)
    else:
        await message.answer('У Вас немає прав доступу!')

async def back_menu(message : types.Message):
    await message.answer('Окей', reply_markup=kb_client)

async def add_new(message : types.Message):
    if message.from_user.id in ID:
        await FSMAdmin.gym.set()
        # await message.reply('В який зал Ви бажаєте додати тренування?', reply_markup=InlineKeyboardMarkup().\
        #                 row(InlineKeyboardButton('ВФЕУ', callback_data='vfeu'),\
        #                     InlineKeyboardButton('ВНТУ', callback_data='vntu')))
        await message.reply('В який зал Ви бажаєте додати тренування?', reply_markup=InlineKeyboardMarkup().\
                        row(InlineKeyboardButton('ВНТУ', callback_data='vntu')))

async def gym_new(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id in ID:
        async with state.proxy() as data:
            data['gym'] = callback.data
        await FSMAdmin.next()
        await callback.message.answer('Оберіть день тижня, куди додати нове тренування:',
                                      reply_markup=InlineKeyboardMarkup(). \
                                      row(InlineKeyboardButton('Понеділок', callback_data='1'), \
                                          InlineKeyboardButton('Вівторок', callback_data='2'), \
                                          InlineKeyboardButton('Середа', callback_data='3')). \
                                      row(InlineKeyboardButton('Четвер', callback_data='4'), \
                                          InlineKeyboardButton("П'ятниця", callback_data="5"), \
                                          InlineKeyboardButton('Субота', callback_data='6'), \
                                          InlineKeyboardButton('Неділя', callback_data='7')))

async def day_new(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id in ID:
        async with state.proxy() as data:
            data['daytime'] = callback.data
        await FSMAdmin.next()
        await callback.message.answer('Вкажіть час, о котрій тренування буде проводитись:')

async def time_new(message: types.Message, state: FSMContext):
    if message.from_user.id in ID:
        async with state.proxy() as data:
            data['daytime'] += ' ' + message.text
        await FSMAdmin.next()
        await message.answer('Вкажіть кількість вільних місць:')

async def free_new(message: types.Message, state: FSMContext):
    if message.from_user.id in ID:
        async with state.proxy() as data:
            data['free'] = message.text
        await FSMAdmin.next()
        await message.answer('Додайте опис до тренування (можна нічого не вказувати):')

async def des_new(message: types.Message, state: FSMContext):
    if message.from_user.id in ID:
        async with state.proxy() as data:
            data['des'] = message.text
        await sqlite_db.sql_add_command(state, message)
        await state.finish()

async def del_what(message: types.Message):
    if message.from_user.id in ID:
        await FSMDelete.gym.set()
        # await message.reply('В якому залі Ви бажаєте видалити тренування?', reply_markup=InlineKeyboardMarkup(). \
        #                     row(InlineKeyboardButton('ВФЕУ', callback_data='vfeu'), \
        #                         InlineKeyboardButton('ВНТУ', callback_data='vntu')))
        await message.reply('В якому залі Ви бажаєте видалити тренування?', reply_markup=InlineKeyboardMarkup(). \
                            row(InlineKeyboardButton('ВНТУ', callback_data='vntu')))

async def del_callback(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        await sqlite_db.sql_delete_command(callback_query.data.replace('del ', ''), data['gym'])
        await callback_query.answer(text=f'Тренування в {data["gym"]} в {sqlite_db.dirday[callback_query.data.replace("del ", "")[0]]}'
                                         f' {callback_query.data.replace("del ", "")[2:]} видалене.', show_alert=True)
    await state.finish()

async def del_gym(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id in ID:
        async with state.proxy() as data:
            data['gym'] = callback.data
            read = await sqlite_db.sql_read(data['gym'])
        if not read:
            await state.finish()
            await bot.send_message(callback.from_user.id, text='Тут й так немає тренувань =)')
            return
        for ret in read:
            await bot.send_message(callback.from_user.id, text=f'{sqlite_db.dirday[ret[0][0]]} {ret[0][2:]}', reply_markup=InlineKeyboardMarkup(). \
                                   add(InlineKeyboardButton(f'^^^Видалити^^^', callback_data=f'del {ret[0]}')))

async def cencel_handler(message: types.Message, state: FSMContext):
    if message.from_user.id in ID:
        current_state = await state.get_state()
        if current_state is None:
            await message.reply('Та Ви й нічого не робили')
            return
        await state.finish()
        await message.reply('Окей')

async def start_new_week(message: types.Message):
    if message.from_user.id in ID:
        await FSMStart.answer.set()
        await message.reply('Ви впевнені в цьому?', reply_markup=InlineKeyboardMarkup().row(
            InlineKeyboardButton('ТАК', callback_data='yes'), InlineKeyboardButton('НІ', callback_data='no')
        ))

async def ofc_new_week(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == 'yes':
        await bot.send_message(callback.from_user.id, 'Вкажіть, будь ласка, часовий проміжок наступного тижня.\nНаприклад: 01.01.23-07.01.23')
        await FSMStart.next()
    else:
        await bot.send_message(callback.from_user.id, 'Окей, не хотілось би все стерти')
        await state.finish()

async def data_new_week(message : types.Message, state: FSMContext):
    await sqlite_db.clear_all_visitors(message.text)
    users = sqlite_db.get_users()
    for row in users:
        try:
            await bot.send_message(row[0], '❗️Розпочато новий тиждень❗️')
            if int(row[1]) != 1:
                sqlite_db.set_active(row[0], 1)
        except:
            sqlite_db.set_active(row[0], 0)
    await state.finish()

async def send_all(message: types.Message):
    if message.from_user.id in ID:
        text = message.text[6:]
        users = sqlite_db.get_users()
        for row in users:
            try:
                await bot.send_message(row[0], text)
                if int(row[1]) != 1:
                    sqlite_db.set_active(row[0], 1)
            except:
                sqlite_db.set_active(row[0], 0)
        await bot.send_message(message.from_user.id, 'Розіслано!')

def register_handlers_admin(dp: Dispatcher):
    dp.register_message_handler(cencel_handler, Text(equals='🛑 ВІДМІНА (я передумав це робити, а бот чекає)'), state="*", chat_type='private')
    dp.register_message_handler(admin_in, commands=['admin'], chat_type='private')
    dp.register_message_handler(add_new, Text(equals='Додати нове тренування'), state=None, chat_type='private')
    dp.register_callback_query_handler(gym_new, state=FSMAdmin.gym)
    dp.register_callback_query_handler(day_new, state=FSMAdmin.day)
    dp.register_message_handler(time_new, state=FSMAdmin.time)
    dp.register_message_handler(free_new, state=FSMAdmin.free)
    dp.register_message_handler(des_new, state=FSMAdmin.des)
    dp.register_message_handler(del_what, Text(equals='Видалити тренування'), state=None, chat_type='private')
    dp.register_callback_query_handler(del_callback, Text(startswith='del '), state=FSMDelete.gym)
    dp.register_callback_query_handler(del_gym, state=FSMDelete.gym)
    dp.register_message_handler(start_new_week, Text(equals='Розпочати новий тиждень'), state=None, chat_type='private')
    dp.register_callback_query_handler(ofc_new_week, state=FSMStart.answer)
    dp.register_message_handler(data_new_week, state=FSMStart.data)
    dp.register_message_handler(send_all, commands=['send'], chat_type='private')
    dp.register_message_handler(back_menu, Text(equals='⬅️ Назад'), chat_type='private')