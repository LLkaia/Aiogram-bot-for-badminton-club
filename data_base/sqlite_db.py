import sqlite3 as sq
from create_bot import bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

week_data = '02.04.23-09.04.23'.center(34, "*") + '\n'

dirday = {'1' : 'Понеділок',
          '2' : 'Вівторок',
          '3' : 'Середа',
          '4' : 'Четвер',
          '5' : "П'ятниця",
          '6' : 'Субота',
          '7' : 'Неділя'}

def sql_start():
    global base, cur
    base = sq.connect('gym_base.db')
    cur = base.cursor()
    if base:
        print('Data base connected OK')
    base.commit()

def user_exists(userid):
    user = cur.execute('SELECT * FROM users WHERE userid = ?', (userid,)).fetchmany(1)
    return bool(len(user))

def add_user(userid):
    cur.execute('INSERT INTO users VALUES (?, ?)', (userid, 1))
    base.commit()

def get_users():
    return cur.execute('SELECT * FROM users').fetchall()

def set_active(user, active):
    cur.execute('UPDATE users SET active == ? WHERE userid == ?', (active, user))
    base.commit()

async def sql_add_command(state, message):
    try:
        async with state.proxy() as data:
            cur.execute(f'INSERT INTO {tuple(data.values())[0]} VALUES (?, ?, ?, ?, ?)', tuple(data.values())[1:]+('',''))
            base.commit()
        await message.answer('Тренування додано.')
    except sq.IntegrityError:
        await message.answer('Таке тренування вже існує!')

async def sql_show(message):
    # tab1 = cur.execute('SELECT * FROM vfeu ORDER BY daytime').fetchall()
    tab2 = cur.execute('SELECT * FROM vntu ORDER BY daytime').fetchall()
    global week_data
    text_answer = week_data
    # text_answer = '---------------ВФЕУ---------------\n' \
    #               '------------------------------------\n'
    # day = ''
    # for x in tab1:
    #     if day != dirday[x[0][0]]:
    #         day = dirday[x[0][0]]
    #         text_answer += f'{day}\n'
    #     text_answer += f'{x[0][2:]} - {x[1]} вільних місць ({x[2]})\n'
    text_answer += f'{"ВНТУ".center(34, "*")}\n' \
                   '❗️Бронь парами, 1 місце = 2 людини❗️\n\n'
    day = ''
    for y in tab2:
        if day != dirday[y[0][0]]:
            day = dirday[y[0][0]]
            text_answer += f'{day}\n'
        text_answer += f'{y[0][2:]} - {y[1]} вільних місць'
        if y[1] == 0 and y[4]:
            text_answer += f' ({sum(int(memb.split("@")[2]) for memb in y[4].split())} в черзі) -  ️{y[2]}\n'
        else:
            text_answer += f' - {y[2]}\n'
    await message.answer(text_answer)

async def sql_read(callback):
    return cur.execute(f'SELECT * FROM {callback} ORDER BY daytime').fetchall()

async def sql_delete_command(data, gym):
    cur.execute(f'DELETE FROM {gym} WHERE daytime == ?', (data,))
    base.commit()

async def add_to_queue(userid, username, when, gym, count):
    queue = cur.execute(f'SELECT queue FROM {gym} WHERE daytime == ?', (when,)).fetchone()[0]
    members = cur.execute(f'SELECT memb FROM {gym} WHERE daytime == ?', (when,)).fetchone()[0]

    if str(userid) not in queue:
        if queue: queue += ' '
        queue += f'{userid}@{username}@{count}'
        if str(userid) not in members:
            await bot.send_message(userid,
                                   f'{dirday[when[0]].upper()} {when[2:]}!\n'
                                   f'В черзі: {count}')
        else:
            player_count_memb = int([x for x in members.split(' ') if x.startswith(str(userid))][0].split('@')[2])
            await bot.send_message(userid,
                                   f'{dirday[when[0]].upper()} {when[2:]}!\n'
                                   f'Заброньовано: {player_count_memb}\n'
                                   f'В черзі: {count}')
    else:
        player_count = int([x for x in queue.split(' ') if x.startswith(str(userid))][0].split('@')[2])
        queue = queue.replace(f'{userid}@{username}@{player_count}',
                              f'{userid}@{username}@{player_count + count}')
        if str(userid) not in members:
            await bot.send_message(userid,
                                   f'{dirday[when[0]].upper()} {when[2:]}!\n'
                                   f'В черзі: {player_count + count}')
        else:
            player_count_memb = int([x for x in members.split(' ') if x.startswith(str(userid))][0].split('@')[2])
            await bot.send_message(userid,
                                   f'{dirday[when[0]].upper()} {when[2:]}!\n'
                                   f'Заброньовано: {player_count_memb}\n'
                                   f'В черзі: {player_count + count}')
    cur.execute(f'UPDATE {gym} SET queue == ? WHERE daytime == ?', (queue, when))
    base.commit()

async def sql_new_player(when, gym, count, username, userid, bool_queue):
    count_free = cur.execute(f'SELECT free FROM {gym} WHERE daytime == ?', (when,)).fetchone()[0]
    members = cur.execute(f'SELECT memb FROM {gym} WHERE daytime == ?', (when,)).fetchone()[0]
    queue = cur.execute(f'SELECT queue FROM {gym} WHERE daytime == ?', (when,)).fetchone()[0]

    if count_free and queue and not bool_queue:
        await bot.send_message(userid, 'Наразі, на це вільне місце просувається черга. Бажаєте, щоб вас додали у неї?',
                               reply_markup=InlineKeyboardMarkup().row(
                                   InlineKeyboardButton('ТАК', callback_data=f'addtoqueue yes/{when}/{gym}/{count}'),
                                   InlineKeyboardButton('НІ', callback_data=f'addtoqueue no')))
        return

    if bool_queue:
        if count_free == 0:
            await bot.send_message(userid, 'Нажаль, якимось чином, на це тренування вже немає вільних місць =(')
            return
        elif count <= count_free:
            queue = ' '.join([x for x in queue.split() if not x.startswith(f'{userid}')])
            cur.execute(f'UPDATE {gym} SET queue == ? WHERE daytime == ?', (queue, when))

    if count_free - count >= 0:
        count_free -= count
        if str(userid) not in members:
            if members: members += ' '
            members += f'{userid}@{username}@{count}'
            await bot.send_message(userid,
                                   f'{dirday[when[0]].upper()} {when[2:]}!\n'
                                   f'Заброньовано: {count}')
        else:
            player_count = int([x for x in members.split(' ') if x.startswith(str(userid))][0].split('@')[2])
            members = members.replace(f'{userid}@{username}@{player_count}', f'{userid}@{username}@{player_count+count}')
            await bot.send_message(userid,
                                   f'{dirday[when[0]].upper()} {when[2:]}!\n'
                                   f'Заброньовано: {player_count+count}.')
        cur.execute(f'UPDATE {gym} SET free == ? WHERE daytime == ?', (count_free, when))
        cur.execute(f'UPDATE {gym} SET memb == ? WHERE daytime == ?', (members, when))
    else:
        if count_free == 0:
            if str(userid) not in queue:
                if queue: queue += ' '
                queue += f'{userid}@{username}@{count}'
                if str(userid) not in members:
                    await bot.send_message(userid,
                                           f'{dirday[when[0]].upper()} {when[2:]}!\n'
                                           f'В черзі: {count}')
                else:
                    player_count_memb = int([x for x in members.split(' ') if x.startswith(str(userid))][0].split('@')[2])
                    await bot.send_message(userid,
                                           f'{dirday[when[0]].upper()} {when[2:]}!\n'
                                           f'Заброньовано: {player_count_memb}\n'
                                           f'В черзі: {count}')
            else:
                player_count = int([x for x in queue.split(' ') if x.startswith(str(userid))][0].split('@')[2])
                queue = queue.replace(f'{userid}@{username}@{player_count}',
                                          f'{userid}@{username}@{player_count + count}')
                if str(userid) not in members:
                    await bot.send_message(userid,
                                           f'{dirday[when[0]].upper()} {when[2:]}!\n'
                                           f'В черзі: {player_count + count}')
                else:
                    player_count_memb = int([x for x in members.split(' ') if x.startswith(str(userid))][0].split('@')[2])
                    await bot.send_message(userid,
                                           f'{dirday[when[0]].upper()} {when[2:]}!\n'
                                           f'Заброньовано: {player_count_memb}\n'
                                           f'В черзі: {player_count + count}')
            cur.execute(f'UPDATE {gym} SET queue == ? WHERE daytime == ?', (queue, when))
        elif count_free > 0:
            count_memb = count_free
            count_queue = count - count_free
            count_free = 0
            if str(userid) not in members:
                if members: members += ' '
                members += f'{userid}@{username}@{count_memb}'
                if str(userid) not in queue:
                    if queue: queue += ' '
                    queue += f'{userid}@{username}@{count_queue}'
                else:
                    player_count_already = int(
                        [x for x in queue.split(' ') if x.startswith(str(userid))][0].split('@')[2])
                    queue = queue.replace(f'{userid}@{username}@{player_count_already}',
                                              f'{userid}@{username}@{count_queue}')
                await bot.send_message(userid,
                                       f'{dirday[when[0]].upper()} {when[2:]}!\n'
                                       f'Заброньовано: {count_memb}\n'
                                       f'В черзі: {count_queue}')
            else:
                player_count_already = int([x for x in members.split(' ') if x.startswith(str(userid))][0].split('@')[2])
                members = members.replace(f'{userid}@{username}@{player_count_already}',
                                          f'{userid}@{username}@{player_count_already + count_memb}')
                if str(userid) not in queue:
                    if queue: queue += ' '
                    queue += f'{userid}@{username}@{count_queue}'
                else:
                    player_count_already_queue = int(
                        [x for x in queue.split(' ') if x.startswith(str(userid))][0].split('@')[2])
                    queue = queue.replace(f'{userid}@{username}@{player_count_already_queue}',
                                          f'{userid}@{username}@{count_queue}')
                await bot.send_message(userid,
                                       f'{dirday[when[0]].upper()} {when[2:]}!\n'
                                       f'Заброньовано: {count_memb + player_count_already}\n'
                                       f'В черзі: {count_queue}')
            cur.execute(f'UPDATE {gym} SET queue == ? WHERE daytime == ?', (queue, when))
            cur.execute(f'UPDATE {gym} SET free == ? WHERE daytime == ?', (count_free, when))
            cur.execute(f'UPDATE {gym} SET memb == ? WHERE daytime == ?', (members, when))

    if bool_queue:
        count_free = cur.execute(f'SELECT free FROM {gym} WHERE daytime == ?', (when,)).fetchone()[0]
        queue = cur.execute(f'SELECT queue FROM {gym} WHERE daytime == ?', (when,)).fetchone()[0]
        if count_free and queue:
            await move_next_queue(gym, when, count_free)

    base.commit()

async def clear_all_visitors(data):
    global week_data
    week_data = f'{data.center(34, "*")}\n'
    # vfeu = cur.execute('SELECT * FROM vfeu ORDER BY daytime').fetchall()
    vntu = cur.execute('SELECT * FROM vntu ORDER BY daytime').fetchall()
    # for train in vfeu:
    #     if train[3]:
    #         places = train[1] + sum(int(memb.split('@')[2]) for memb in train[3].split())
    #         cur.execute('UPDATE vfeu SET free == ?, memb == ? WHERE daytime == ?', (places, '', train[0]))
    for train in vntu:
        if train[3]:
            places = train[1] + sum(int(memb.split('@')[2]) for memb in train[3].split())
            cur.execute('UPDATE vntu SET free == ?, memb == ?, queue == ? WHERE daytime == ?', (places, '', '', train[0]))
    base.commit()

async def where_signed_up(userid):
    # vfeu = cur.execute(f"SELECT daytime, memb FROM vfeu WHERE memb LIKE '%{userid}%' ORDER BY daytime").fetchall()
    vntu = cur.execute(f"SELECT daytime, memb, queue FROM vntu WHERE memb LIKE '%{userid}%' "
                            f"OR queue LIKE '%{userid}%' ORDER BY daytime").fetchall()
    if not vntu:
         await bot.send_message(userid, 'Ви ще не записались!')
    else:
         answer = ''
    #     for train in vfeu:
    #         count = int([x for x in train[1].split(' ') if x.startswith(str(userid))][0].split('@')[2])
    #         answer += f'ВФЕУ {dirday[train[0][0]]} {train[0][2:]} -- {count} місць(-я)\n'
         for train in vntu:
             answer += f'ВНТУ {dirday[train[0][0]]} {train[0][2:]}'
             if str(userid) in train[1]:
                count_memb = int([x for x in train[1].split(' ') if x.startswith(str(userid))][0].split('@')[2])
                answer += f' - {count_memb} зайнято'
             if str(userid) in train[2]:
                count_queue = int([x for x in train[2].split(' ') if x.startswith(str(userid))][0].split('@')[2])
                answer += f' - {count_queue} в черзі'
             answer += '\n'
         await bot.send_message(userid, text=answer)

async def read_where_signed(userid, gym):
    return cur.execute(f"SELECT daytime, memb, queue FROM {gym} WHERE memb LIKE '%{userid}%' "
                            f"OR queue LIKE '%{userid}%' ORDER BY daytime").fetchall()

async def delete_from_queue(gym, daytime, userid):
    queue = cur.execute(f'SELECT queue FROM {gym} WHERE daytime == ?', (daytime,)).fetchone()[0]
    queue = ' '.join([x for x in queue.split() if not x.startswith(userid)])
    cur.execute(f'UPDATE {gym} SET queue == ? WHERE daytime == ?', (queue, daytime))
    base.commit()

async def move_next_queue(gym, daytime, free):
    queue = cur.execute(f'SELECT queue FROM {gym} WHERE daytime == ?', (daytime,)).fetchone()[0]
    if not queue:
        return
    userid = int(queue.split()[0].split('@')[0])
    username = queue.split()[0].split('@')[1]
    count = int(queue.split()[0].split('@')[2])
    if free == 0:
        free = cur.execute(f'SELECT free FROM {gym} WHERE daytime == ?', (daytime,)).fetchone()[0]
        if free == 0:
            await bot.send_message(userid, 'Нажаль, якимось чином, на це тренування вже немає вільних місць =(')
            return
    await bot.send_message(userid, f'Звільнилось {free} місце на тренування'
                                       f' в {gym} {dirday[daytime[0]].lower()} {daytime[2:]}. Записатись?\n\n❗️Відповідь обов*язкова, натисніть "НІ", якщо не маєте можливості прийти.',
                           reply_markup=InlineKeyboardMarkup()
                           .row(InlineKeyboardButton('ТАК', callback_data=f'next_yes_{userid}/{username}/{gym}/{daytime}/{count}'),
                                InlineKeyboardButton('НІ', callback_data=f'next_no_{gym}/{daytime}/{userid}'))
                           )

async def leave_train(gym, daytime, count_leave, user):
    count_booked_by_user = int(daytime.split()[2].split('_')[0])
    count_queue_by_user = int(daytime.split()[2].split('_')[1])
    daytime = ' '.join(daytime.split()[0:2])
    count_free = cur.execute(f'SELECT free FROM {gym} WHERE daytime == ?', (daytime,)).fetchone()[0]
    members = cur.execute(f'SELECT memb FROM {gym} WHERE daytime == ?', (daytime,)).fetchone()[0].split()
    queue = cur.execute(f'SELECT queue FROM {gym} WHERE daytime == ?', (daytime,)).fetchone()[0].split()
    answer = ''

    if count_queue_by_user:
        if count_leave >= count_queue_by_user:
            count_leave -= count_queue_by_user
            queue = ' '.join(list(filter(lambda m: str(user) not in m, queue)))
        else:
            count_queue_by_user -= count_leave
            count_leave = 0
            for i in range(len(queue)):
                if queue[i].startswith(str(user)):
                    queue[i] = queue[i].split('@')
                    queue[i][2] = str(count_queue_by_user)
                    queue[i] = '@'.join(queue[i])
            queue = ' '.join(queue)
            answer += f'\nВ черзі: {count_queue_by_user} місць.'
    else:
        queue = ' '.join(queue)
    cur.execute(f'UPDATE {gym} SET queue == ? WHERE daytime == ?', (queue, daytime))
    base.commit()

    if count_leave:
        count_booked_by_user -= count_leave

        if count_free == 0 and queue:
            await move_next_queue(gym, daytime, count_leave)

        count_free += count_leave
        if count_booked_by_user:
            for i in range(len(members)):
                if members[i].startswith(str(user)):
                    members[i] = members[i].split('@')
                    members[i][2] = str(count_booked_by_user)
                    members[i] = '@'.join(members[i])
            members = ' '.join(members)
            answer = f'\nЗайнято: {count_booked_by_user} місць.' + answer
        else:
            members = ' '.join(list(filter(lambda m: str(user) not in m, members)))
    elif count_booked_by_user:
        members = ' '.join(members)
        answer = f'\nЗайнято: {count_booked_by_user} місць.' + answer
    else:
        members = ' '.join(members)

    if answer:
        answer = f'В {dirday[daytime[0]].lower()} {daytime[2:]} дані оновлено:' + answer
    else:
        answer = 'Ви виписались з тренування!'

    cur.execute(f'UPDATE {gym} SET free == ?, memb == ? WHERE daytime == ?',
                (count_free, members, daytime))
    await bot.send_message(user, text=answer)
    base.commit()

async def booked_members(daytime, gym, id):
    members = cur.execute(f'SELECT memb FROM {gym} WHERE daytime == ?', (daytime,)).fetchone()[0].split()
    if members:
        for m in members:
            user = await bot.get_chat(m.split("@")[0])
            await bot.send_message(id, f'{user.first_name} {user.last_name} {m.split("@")[2]} місця')
    else:
        await bot.send_message(id, f'На це тренування ніхто не записаний.')