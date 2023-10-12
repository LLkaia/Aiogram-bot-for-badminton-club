from aiogram import types, Dispatcher
from create_bot import dp, bot
from keyboards import kb_client
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from data_base import sqlite_db

class FSMClient(StatesGroup):
    gym = State()
    daytime = State()
    count = State()

class FSMLeave(StatesGroup):
    gym1 = State()
    daytime1 = State()
    count1 = State()

class FSMBooked(StatesGroup):
    gym = State()

async def in_chat(id):
    if (await bot.get_chat_member(-1001805175622, id))['status'] in ['left', 'kicked']:
        await bot.send_message(id, 'Спочатку ви маєте бути членом спільноти!', reply_markup=InlineKeyboardMarkup()
                             .add(InlineKeyboardButton('Я вже приєднався 🙃', callback_data='start again')))
        return False
    else:
        return True

async def commands_start(message : types.Message):
    if message.chat.type == 'private':
        if await in_chat(message.from_user.id):
            await message.answer('Вітаємо у нашому клубі!\n\n❗️Зверніть увагу, що, наразі, запис через БОТА здійснюється лише у '
                                 'Вінницький Національний Технічний Університет.\n❗️1 МІСЦЕ = ПАРА (2 ЛЮДИНИ)', reply_markup=kb_client)
            if not sqlite_db.user_exists(message.from_user.id):
                sqlite_db.add_user(message.from_user.id)
    else:
        await message.answer('Познайомтесь з нашим ботом: @vbsclub_bot')
        await message.delete()

async def callback_start(callback : types.CallbackQuery):
    if await in_chat(callback.from_user.id):
        await bot.send_message(callback.from_user.id, 'Вітаємо у нашому клубі!\n\n❗️Зверніть увагу, що, наразі, запис через БОТА здійснюється лише у '
                                 'Вінницький Національний Технічний Університет.\n❗️1 МІСЦЕ = ПАРА (2 ЛЮДИНИ)', reply_markup=kb_client)
        if not sqlite_db.user_exists(callback.from_user.id):
            sqlite_db.add_user(callback.from_user.id)

async def show_free(message: types.Message):
    if await in_chat(message.from_user.id):
        await sqlite_db.sql_show(message)

async def write_new(message : types.Message):
    if await in_chat(message.from_user.id):
        await FSMClient.gym.set()
        # await message.answer('Оберіть зал, у який Ви хочете записатись:', reply_markup=InlineKeyboardMarkup().\
        #                     row(InlineKeyboardButton('ВФЕУ', callback_data='vfeu'),\
        #                         InlineKeyboardButton('ВНТУ', callback_data='vntu')))
        await message.answer('Оберіть зал, у який Ви хочете записатись:', reply_markup=InlineKeyboardMarkup().\
                            row(InlineKeyboardButton('ВНТУ', callback_data='vntu')))

async def load_gym(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['gym'] = callback.data
        read = await sqlite_db.sql_read(data['gym'])
    if not read:
        await state.finish()
        await bot.send_message(callback.from_user.id, text='Поки що, тренування тут відсутні.')
        return
    await FSMClient.next()
    for ret in read:
        if ret[1]:
            text = f'{sqlite_db.dirday[ret[0][0]]} {ret[0][2:]} - {ret[1]} вільних місць - {ret[2]}'
        else:
            text = f'{sqlite_db.dirday[ret[0][0]]} {ret[0][2:]} - {ret[1]} вільних місць ({sum(int(memb.split("@")[2]) for memb in ret[4].split())} в черзі) - {ret[2]}'
        await bot.send_message(callback.from_user.id, text=text, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton(f'^^^Записатись^^^', callback_data=ret[0])))

async def load_daytime(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['daytime'] = callback.data
    await FSMClient.next()
    # await callback.message.answer('Скільки місць ви бажаєте забронювати?', reply_markup=InlineKeyboardMarkup().
    #                               row(InlineKeyboardButton('1', callback_data='1'), InlineKeyboardButton('2', callback_data='2'), InlineKeyboardButton('3', callback_data='3'), InlineKeyboardButton('4', callback_data='4'), InlineKeyboardButton('5', callback_data='5'), InlineKeyboardButton('6', callback_data='6'), InlineKeyboardButton('7', callback_data='7'), InlineKeyboardButton('8', callback_data='8')).
    #                               row(InlineKeyboardButton('9', callback_data='9'), InlineKeyboardButton('10', callback_data='10'), InlineKeyboardButton('11', callback_data='11'), InlineKeyboardButton('12', callback_data='12'), InlineKeyboardButton('13', callback_data='13'), InlineKeyboardButton('14', callback_data='14'), InlineKeyboardButton('15', callback_data='15'), InlineKeyboardButton('16', callback_data='16')))
    await callback.message.answer('Скільки місць ви бажаєте забронювати?', reply_markup=InlineKeyboardMarkup().
                                  row(InlineKeyboardButton('1', callback_data='1'), InlineKeyboardButton('2', callback_data='2'),
                                      InlineKeyboardButton('3', callback_data='3'), InlineKeyboardButton('4', callback_data='4')))

async def load_count(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['count'] = int(callback.data)
        await sqlite_db.sql_new_player(data['daytime'], data['gym'], data['count'],
                                       callback.from_user.username, callback.from_user.id, False)
    await state.finish()


async def location(message: types.Message):
    if await in_chat(message.from_user.id):
        # await message.answer('У нас є два спортивні зали.\n'
        #                      'Адреса першого (ВФЕУ) : вул. Пирогова, 71-А\n'
        #                      'Адреса другого (ВНТУ) : вул. Хмельницьке шосе, 95')
        await message.answer('На разі, запис у Telegram тестуємо в зал ВНТУ:\n'
                             '📍 вул. Хмельницьке шосе, 95\n\n'
                             'Запис у ВФЕУ здійснюється у Viber')

async def load_cencel(message: types.Message, state: FSMContext):
    if await in_chat(message.from_user.id):
        current_state = await state.get_state()
        if current_state is None:
            await message.reply('Та Ви й нічого не робили')
            return
        await state.finish()
        await message.reply('Окей')

async def signed_up_games(message: types.Message):
    if await in_chat(message.from_user.id):
        await sqlite_db.where_signed_up(message.from_user.id)

async def leave_train_gym(message: types.Message):
    if await in_chat(message.from_user.id):
        await FSMLeave.gym1.set()
        # await message.answer('Оберіть зал, з якого Ви хочете виписатись:', reply_markup=InlineKeyboardMarkup().\
        #                     row(InlineKeyboardButton('ВФЕУ', callback_data='vfeu'),\
        #                         InlineKeyboardButton('ВНТУ', callback_data='vntu')))
        await message.answer('Оберіть зал, з якого Ви хочете виписатись:', reply_markup=InlineKeyboardMarkup().\
                            row(InlineKeyboardButton('ВНТУ', callback_data='vntu')))

async def leave_train_load(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['gym'] = callback.data
    loaded = await sqlite_db.read_where_signed(callback.from_user.id, callback.data)
    if not loaded:
        await state.finish()
        await bot.send_message(callback.from_user.id, 'Ви не записані на якесь тренування в цьому залі.')
        return
    await FSMLeave.next()
    for train in loaded:
        count_memb, count_queue = 0, 0
        text = f'{sqlite_db.dirday[train[0][0]]} {train[0][2:]}'
        if str(callback.from_user.id) in train[1]:
            count_memb = int(
                [x for x in train[1].split(' ') if x.startswith(str(callback.from_user.id))][0].split('@')[2])
            text += f' - {count_memb} зайнято'
        if str(callback.from_user.id) in train[2]:
            count_queue = int(
                [x for x in train[2].split(' ') if x.startswith(str(callback.from_user.id))][0].split('@')[2])
            text += f' - {count_queue} в черзі'
        await bot.send_message(callback.from_user.id, text=text,
                                reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton(f'^^^Виписатись^^^', callback_data=f'{train[0]} {count_memb}_{count_queue}')))

async def leave_train_daytime(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['daytime'] = callback.data
    await FSMLeave.next()
    # await callback.message.answer('Скільки місць відмінити?', reply_markup=InlineKeyboardMarkup().
    #                               row(InlineKeyboardButton('1', callback_data='1'),
    #                                   InlineKeyboardButton('2', callback_data='2'),
    #                                   InlineKeyboardButton('3', callback_data='3'),
    #                                   InlineKeyboardButton('4', callback_data='4'),
    #                                   InlineKeyboardButton('5', callback_data='5'),
    #                                   InlineKeyboardButton('6', callback_data='6'),
    #                                   InlineKeyboardButton('7', callback_data='7'),
    #                                   InlineKeyboardButton('8', callback_data='8')).
    #                               row(InlineKeyboardButton('9', callback_data='9'),
    #                                   InlineKeyboardButton('10', callback_data='10'),
    #                                   InlineKeyboardButton('11', callback_data='11'),
    #                                   InlineKeyboardButton('12', callback_data='12'),
    #                                   InlineKeyboardButton('13', callback_data='13'),
    #                                   InlineKeyboardButton('14', callback_data='14'),
    #                                   InlineKeyboardButton('15', callback_data='15'),
    #                                   InlineKeyboardButton('16', callback_data='16')))
    await callback.message.answer('Скільки місць відмінити?', reply_markup=InlineKeyboardMarkup().
                                  row(InlineKeyboardButton('1', callback_data='1'),
                                      InlineKeyboardButton('2', callback_data='2'),
                                      InlineKeyboardButton('3', callback_data='3'),
                                      InlineKeyboardButton('4', callback_data='4')))

async def leave_train_count(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['count'] = int(callback.data)
        if data['count'] > sum(int(x) for x in data['daytime'].split()[2].split('_')):
            await state.finish()
            await callback.message.answer('Ви не займали так багато місць!')
            return
        await sqlite_db.leave_train(data['gym'], data['daytime'], data['count'], callback.from_user.id)
    await state.finish()

async def who_booked(message: types.Message):
    if await in_chat(message.from_user.id):
        await FSMBooked.gym.set()
        # await message.reply('В якому залі?', reply_markup=InlineKeyboardMarkup(). \
        #                         row(InlineKeyboardButton('ВФЕУ', callback_data='vfeu'), \
        #                             InlineKeyboardButton('ВНТУ', callback_data='vntu')))
        await message.reply('В якому залі?', reply_markup=InlineKeyboardMarkup(). \
                                row(InlineKeyboardButton('ВНТУ', callback_data='vntu')))

async def gym_booked(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['gym'] = callback.data
        read = await sqlite_db.sql_read(data['gym'])
    if not read:
        await state.finish()
        await bot.send_message(callback.from_user.id, text='Поки що, тренування тут відсутні.')
        return
    for ret in read:
        await bot.send_message(callback.from_user.id, text=f'{sqlite_db.dirday[ret[0][0]]} {ret[0][2:]} - {sum(int(player.split("@")[2]) for player in ret[3].split())} гравців ({sum(int(player.split("@")[2]) for player in ret[4].split())} в черзі)',
                                reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton(f'^^^Записані^^^', callback_data=f'booked {ret[0]}')))

async def booked_callback(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        await sqlite_db.booked_members(callback_query.data.replace('booked ', ''), data['gym'], callback_query.from_user.id)
    await state.finish()

async def next_queue(callback : types.CallbackQuery):
    await callback.message.delete()
    if callback.data.startswith('next_yes_'):
        load = callback.data.replace('next_yes_', '').split('/')
        await sqlite_db.sql_new_player(load[3], load[2], int(load[4]), load[1], int(load[0]), True)
    else:
        load = callback.data.replace('next_no_', '').split('/')
        await bot.send_message(int(load[2]), 'Окей. Дякую, що повідомили.')
        await sqlite_db.delete_from_queue(*load)
        await sqlite_db.move_next_queue(load[0], load[1], 0)

async def add_to_queue_what(callback : types.CallbackQuery):
    await callback.message.delete()
    load = callback.data.replace('addtoqueue ', '').split('/')
    if load[0] == 'yes':
        await sqlite_db.add_to_queue(callback.from_user.id, callback.from_user.username, load[1], load[2], load[3])
    else:
        await bot.send_message(callback.from_user.id, 'Окей. Дякую за розуміння')


def register_handlers_client(dp : Dispatcher):
    dp.register_message_handler(load_cencel, Text(equals='🛑 ВІДМІНА (я передумав це робити, а бот чекає)'), state="*", chat_type='private')
    dp.register_message_handler(commands_start, commands=['start', 'help'])
    dp.register_callback_query_handler(callback_start, Text('start again'))
    dp.register_message_handler(location, Text(equals='📍 Де нас знайти'))
    dp.register_message_handler(show_free, Text(equals='👟 Тренування на цьому тижні'), chat_type='private')
    dp.register_message_handler(write_new, Text(equals='📝 Записатись'), state=None, chat_type='private')
    dp.register_callback_query_handler(load_gym, state=FSMClient.gym)
    dp.register_callback_query_handler(load_daytime, state=FSMClient.daytime)
    dp.register_callback_query_handler(load_count, state=FSMClient.count)
    dp.register_message_handler(signed_up_games, Text(equals='✍️ Мої записи'), chat_type='private')
    dp.register_message_handler(leave_train_gym, Text(equals='🏃 Виписатись'), state=None, chat_type='private')
    dp.register_callback_query_handler(leave_train_load, state=FSMLeave.gym1)
    dp.register_callback_query_handler(leave_train_daytime, state=FSMLeave.daytime1)
    dp.register_callback_query_handler(leave_train_count, state=FSMLeave.count1)
    dp.register_message_handler(who_booked, Text(equals='🤓 Хто записаний на тренування'), state=None, chat_type='private')
    dp.register_callback_query_handler(booked_callback, Text(startswith='booked '), state=FSMBooked.gym)
    dp.register_callback_query_handler(gym_booked, state=FSMBooked.gym)
    dp.register_callback_query_handler(next_queue, Text(startswith='next_'))
    dp.register_callback_query_handler(add_to_queue_what, Text(startswith='addtoqueue '))