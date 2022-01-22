import os
import sys
import random

sys.path.append(os.path.abspath('../settings'))
from global_sets import *
from discord.ext import commands

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
    return switcher.get(intarg, "what")

# Рандомное число
@client.command(aliases = ['random', 'рандом', 'Random', 'Рандом', 'Roll', 'roll', 'Ролл', 'ролл'])
async def __roll(ctx):
    if (right_channel(ctx)):
        r = str(random.randrange(1, 101))
        mes = ''
        for m in r:
            mes += roll_convert(m)

        await ctx.send(mes)


# Коинфлип
@client.command(aliases = ['coin', 'Coin', 'Монетка', 'монетка', 'орёл решка'])
async def __coin(ctx):
    if (right_channel(ctx)):
        r = random.randrange(1, 101)
        if r > 5:
            d = random.randrange(1, 3)
            if d == 1:
                await ctx.send(':full_moon:')
            else:
                await ctx.send(':new_moon:')
        else:
            await ctx.send(':last_quarter_moon:')
