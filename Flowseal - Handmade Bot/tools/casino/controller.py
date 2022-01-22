import os
import sys
import time
import random

from blackjack import * # Blackjack
from slot_machine import * # Slots

sys.path.append(os.path.abspath('../../settings'))
from global_sets import *
from discord.ext import commands

# Система инкама, True для включения
income = False

# Раз в n-ое количество секунд получение бонуса
B_TIME = 900

# Количество алмазов при получении бонуса
B_DIAMONDS = 1

def add_bonus(table, user):
    chance = random.randrange(0, 101)
    if (chance < 90):
        money = 0

        if income: money += math.floor(int(table[user]['dollars']) * random.randrange(0.2, 0.4))
        else: money += random.randrange(21, 100)

        table[user]['dollars'] += money
        return 'Вы получили {} :dollar: !'.format(str(money))
    elif (chance < 95):
        rating = random.randrange(1, 11)
        table[user]['rating'] += rating
        return 'Вы получили {} :crown: !'.format(str(rating))
    else:
        table[user]['diamonds'] += B_DIAMONDS
        return 'Вы получили {} :large_blue_diamond: !'.format(str(B_DIAMONDS))

# Бонус каждые B_TIME минут
@client.command(aliases = ['bonus', 'Bonus', 'Бонус', 'бонус'])
async def __bonus(ctx):
    if not right_channel(ctx):
        return True
    
    with open('files/users.json', 'r') as f:
        table = json.load(f)
    
    # получаем id автора сообщения
    user = str(ctx.message.author.id)

    # проверяем регистрацию
    check_reg(user, table, ctx.message.author.name)

    if (not 'daily' in table[user]['events']):
        table[user]['events']['daily'] = time.time()
        response = add_bonus(table, user)
        await ctx.send('> {} \n {} \n Следующий бонус вы сможете получить через {} секунд(ы)'.format(ctx.message.author.name, response, str(B_TIME)))

    else:
        if (time.time() - table[user]['events']['daily'] >= B_TIME):
            table[user]['events']['daily'] = time.time()
            response = add_bonus(table, user)
            await ctx.send('> {} \n {} \n Следующий бонус вы сможете получить через {} секунд(ы)'.format(ctx.message.author.name, response, str(B_TIME)))
        else:
            await ctx.send('> {} \n До получения бонуса: {} секунд(ы)'.format(ctx.message.author.name, str(math.floor(B_TIME - (time.time() - table[user]['events']['daily'])))))

     
    # обновляем запись
    with open('files/users.json', 'w') as f:
        json.dump(table, f)


# Статистика (профиль)
@client.command(aliases = ['Профиль', 'профиль', 'баланс', 'Баланс', 'Profile', 'profile', 'balance', 'Balance'])
async def __balance(ctx):
    if not right_channel(ctx):
        return True

    with open('files/users.json', 'r') as f:
        table = json.load(f)
    
    # получаем id автора сообщения
    user = str(ctx.message.author.id)

    # проверяем регистрацию
    check_reg(user, table, ctx.message.author.name)

    emb = discord.Embed( title = 'Profile:', description = '', colour = discord.Color.magenta() )

    emb.set_author(name = ctx.message.author.name, icon_url = ctx.message.author.avatar_url)

    emb.add_field( name = f'Ваш баланс', value = '**{}** :dollar:'.format(str(table[user]['dollars'])), inline=False)
    emb.add_field( name = f'Ваш рейтинг', value = '**{}** :crown:'.format(str(table[user]['rating'])), inline=True)
    emb.add_field( name = f'Алмазы', value = '**{}** :small_blue_diamond:'.format(str(table[user]['diamonds'])), inline=True)

    emb.set_thumbnail(url = "https://icons.iconarchive.com/icons/tooschee/misc/128/Games-icon.png")

    await ctx.send(embed = emb)


# Топ-10 пользователей + личный топ по рейтингу
@client.command(aliases = ['top', 'Top', 'Топ', 'топ'])
async def __top(ctx):
    if not right_channel(ctx):
            return True

    with open('files/users.json', 'r') as f:
        table = json.load(f)

    # получаем id автора сообщения
    user = str(ctx.message.author.id)

    # проверяем регистрацию
    check_reg(user, table, ctx.message.author.name)

    # создаём новый словарь типа ('id':rating)
    users = {}
    for p_user in table:
        users.update({p_user : table[p_user]['rating']})

    # сортируем от большего новый словарь
    rated = dict(sorted(users.items(), key=lambda item: item[1], reverse=True))
    rating = list(rated.values())
    rated = list(rated)

    # формируем рейтинг
    emb = discord.Embed( title = 'Top 10 users:', description = '', colour = discord.Color.magenta() )
    emb.set_author(name = ctx.message.author.name, icon_url = ctx.message.author.avatar_url)

    for i in range(0, min(10, len(table))):
        emb.add_field( name = (str(i + 1) + '. ' + table[rated[i]]['name']), value = '**{}** :crown:'.format(str(rating[i])), inline=False)

    emb.add_field( name = 'You', value = '`{}` :crown:'.format(str(table[user]['rating'])), inline=False)

    emb.set_thumbnail(url = "https://icons.iconarchive.com/icons/pelfusion/christmas-shadow-2/128/Crown-icon.png")

    await ctx.send(embed = emb)

    # обновляем запись
    with open('files/users.json', 'w') as f:
        json.dump(table, f)

