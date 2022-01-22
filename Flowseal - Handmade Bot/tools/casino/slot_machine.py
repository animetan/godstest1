import os
import sys
import random
import asyncio

sys.path.append(os.path.abspath('../../settings'))
from global_sets import *
from discord.ext import commands
from collections.abc import Sequence

def seven_multiplier(argument):
    intarg = int(argument)
    switcher = {
        1: 1.5,
        2: 7,
        3: 343
    }
    return switcher.get(intarg, 0)

def get_multiplier(argument):
    intarg = int(argument)
    switcher = {
        000: 100,
        111: 10,
        333: 10,
        555: 50,
        999: 100,
        123: 123,
        666: 60,
        696: 5,
        969: 5,
        321: 5
    }
    return switcher.get(intarg, 0)


def roll_convert(argument):
    intarg = int(argument)
    switcher = {
        1: ":one:",
        2: ":two:",
        3: ":three:",
        4: ":four:",
        5: ":five:",
        6: ":six:",
        7: ":seven:",
        8: ":eight:",
        9: ":nine:",
        0: ":zero:"
    }
    return switcher.get(intarg, 0)

@client.command(aliases = ['slot', 'Slot', 'Слот', 'слот'])
async def __slot(ctx, bet=0):
    if (right_channel(ctx)):

        if bet < 2:
            await ctx.send('> {} \n Сумма ставки не может быть меньше 2 :dollar:'.format(ctx.message.author.name))
            return True

        with open('files/users.json', 'r') as f:
            table = json.load(f)

        mult = 0.0

        # получаем id автора сообщения
        user = str(ctx.message.author.id)

        check_reg(user, table, ctx.message.author.name)

        if (bet > table[user]['dollars']):
            await ctx.send('> {} \n У вас недостаточно средств на балансе ({}$)'.format(ctx.message.author.name, str(table[user]['dollars'])))
            return True

        table[user]['dollars'] -= bet

        random_int = random.randrange(0, 1000)
        random_string = str(random_int)

        if (len(random_string) < 3):
            random_string = ('0' * (3 - len(random_string))) + random_string

        if (random_string.count('7')):
            mult = seven_multiplier(random_string.count('7'))
        else:
            mult = get_multiplier(random_string)

        mes = '> {}\n\n:slot_machine: | **{}** :dollar:\n'.format(ctx.message.author.name, bet)
        
        for ch in random_string:
            mes += roll_convert(ch)

        mes += '\n\n> **{}** :negative_squared_cross_mark: **|** **{}** :dollar:'.format(mult, round(mult*bet, 2))

        table[user]['dollars'] += round(mult*bet, 2)

        await ctx.send(mes)

        # Обновляем запись
        with open('files/users.json', 'w') as f:
            json.dump(table, f)