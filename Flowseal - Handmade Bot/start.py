import os
import sys

sys.path.append(os.path.abspath('settings'))
from global_sets import * # Импорт основных настроек
from config import settings

# Переходим в папку со вторичными функциями бота
sys.path.append(os.path.abspath('tools'))
from music import * # музыкальный бот
from information import * # комманды с информацией
from entertainment import * # комманды для развлечений
from moderation import * # комманды для модерации
from shikimori import * # комманды для парса шики
from temp_rooms import * # временные комнаты
from random_tools import * # команды для рандома
from rps import * # команды для камень-ножницы-бумага

# Переходим в папку с азартными играми
sys.path.append(os.path.abspath('tools/casino'))
from controller import * # Система управления казино

from async_timeout import timeout
from discord.ext import commands


# Убираем вывод лишних логов с библиотеки youtube_dl
youtube_dl.utils.bug_reports_message = lambda: ''

# Музыка
client.add_cog(Music(client))

# Объявляем событие начало работы бота
@client.event
async def on_ready():
    print (f"{client.user.name} | Ready")
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="PornHub.com"))

    # users.json
    github_export('files/users.json', 'users', 'users.json')
    client.loop.create_task(update_user_table())

    # servers.json
    github_export('files/servers.json', 'users', 'servers.json')
    client.loop.create_task(update_servers_table())


# Объявляем событие присоединения нового мембера
@client.event
async def on_member_join(member):
    await member.create_dm()
    await member.dm_channel.send(
        f'Welcome, {member.name}, have a good cum!'
    )

# Обновление таблицы юзеров каждую минуту (Импорт на гитхаб)
async def update_user_table():
    while True:
        github_import('files/users.json', 'users', 'users.json')
        await asyncio.sleep(60)

# Обновление таблицы серверов каждую минуту (Импорт на гитхаб)
async def update_servers_table():
    while True:
        github_import('files/servers.json', 'users', 'servers.json')
        await asyncio.sleep(60)


# Запуск бота
client.run (settings['TOKEN'])