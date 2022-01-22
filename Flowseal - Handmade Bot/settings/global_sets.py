import discord # Импорт главной библиотеки discord.py
import json # Работа с файлами
import requests # Работа с запросами
import asyncio # Работа с музыкой
import youtube_dl # Скачивание музыки с yt
import functools # Вспомогательный функционал
import itertools # Вспомогательный функционал
import math # Математика
import random # Рандом
import ffmpeg # Проигрывание музыки
import colorsys # Система цветов
import glob
import os

from discord.ext import commands # Импорт из библиотеки discord.py библиотеки commands
from config import settings # Импорт из файла config.py настроек
from github import Github # Импорт библиотеки pygithub

# Чтение файла env.json с путями
with open("files/env.json", "r") as env:
    ENV = json.load(env)

# Получение пути из env.json
ECCHI_FOLDER = ENV["ecchi_folder"]
LEGS_FOLDER = ENV["legs_folder"]

# Чё-то новое для прав | https://discordpy.readthedocs.io/en/latest/intents.html
intents = discord.Intents.all()

# Префикс ваших команд
prefix = settings['PREFIX']

# Определяем переменную для работы с ботом
client = commands.Bot(command_prefix=prefix, intents=intents)

# Убираем вывод лишних логов с библиотеки youtube_dl
youtube_dl.utils.bug_reports_message = lambda: ''

# Инициализируем гитхаб
g = Github(settings['GITHUB'])

# Парсинг контента определенного сайта
def get_html(url):
    r = requests.get(url)
    return (r.text.replace('{"content":"', '').replace('"}', ''))

# Проверка правильности канала
def right_channel(ctx):
    if (not settings['CUSTOM_CHANNEL']):
        return True

    if (
        str(ctx.message.channel.name) == settings['CHANNEL_NAME'] and (
        str(ctx.message.channel.type) == "private" or
        ctx.message.channel.is_nsfw())
    ):
        return True
    return False
   
# Обновление плейлистов с гитхаба
def playlists_update_ext(ctx):
    if (right_channel(ctx)):      
        files = glob.glob('playlists/*')
        for f in files:
            os.remove(f)
        
        for rep in g.get_user().get_repos():
            if rep.name == 'playlists':
                repo = rep
                
        contents = repo.get_contents("")
        while contents:
            file_content = contents.pop(0)
            if file_content.type != "dir":
                with open("playlists/{}".format(file_content.name), 'w') as f:
                    f.write(file_content.decoded_content.decode())

# Export файла с гитхаба
def github_export(file, repos_name, rep_file):
        os.remove(file)
        
        for rep in g.get_user().get_repos():
            if rep.name == repos_name:
                repo = rep
                
        with open(file, 'w') as f:
            contents = repo.get_contents(rep_file, ref="main")
            f.write(contents.decoded_content.decode())

# Import файла с гитхаба
def github_import(file, repos_name, rep_file):
        for rep in g.get_user().get_repos():
            if rep.name == repos_name:
                repo = rep
                
        with open(file, 'r') as f:
                contents = repo.get_contents(rep_file, ref="main")
                s = f.read()
                repo.update_file(contents.path, "update", s, contents.sha, branch="main")


def check_reg(user, table, name):
    if not (user in table):
        table[user] = {}
        table[user]['name'] = name
        table[user]['dollars'] = 0
        table[user]['diamonds'] = 0
        table[user]['rating'] = 0
        table[user]['events'] = {}
        return False
    return True
