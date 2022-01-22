import os
import sys

sys.path.append(os.path.abspath('../settings'))
from global_sets import *
from async_timeout import timeout
from discord.ext import commands

# Есть ли права администратора у пользователя
def is_admin(ctx):
    return ctx.message.author.guild_permissions.administrator

# Может ли пользователь удалять или изменять сообщения
def manage_messages(ctx):
    return is_admin(ctx) or ctx.message.author.guild_permissions.manage_messages


# Очистка сообщений
@client.command(aliases = ['Clear', 'clear', 'Очистка', 'очистка'])
async def __clear(ctx):
    if (manage_messages(ctx)):
        await ctx.message.channel.purge()
        await ctx.send ('Канал очищен!')

    else:
        await ctx.send ('У вас недостаточно прав.')
