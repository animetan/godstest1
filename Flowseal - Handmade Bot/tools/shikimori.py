import os
import sys

sys.path.append(os.path.abspath('../settings'))
from global_sets import *
from async_timeout import timeout
from discord.ext import commands

import urllib.request
from bs4 import BeautifulSoup as soup
from time import sleep


def get_html(url):
    response = urllib.request.urlopen(url)
    return response.read()

def parse(html, emb: discord.Embed):
    soup_about = soup(html, 'html.parser')
    table = soup_about.find('tbody', class_='entries')
    i = 0
    for row in table.find_all('tr'):    
        i = i + 1
        if i == 20:
            break

        cols = row.find_all('td')
        emb.add_field( name = cols[1].a.find_all('span')[1].text, value = (':heart: `' + cols[2].span.text + '`' + ' [Click](' + 'https://shikimori.one' + cols[1].a.get('href') + ')'), inline=False)


@client.command(aliases = ['Шикимори', 'Шики', 'шики', 'шикимори', 'Shiki', 'shiki', 'anime', 'Anime', 'Аниме', 'аниме'])
async def __shikimori(ctx, nickname = ''):
    if (right_channel(ctx)):    
        if not nickname:
            await ctx.send(f'Не хватает никнейма shikimori: {prefix}anime `NICKNAME` (Пример использования: {prefix}anime Loli) (Соблюдайте регистр!)')
        else:
            emb = discord.Embed( title = 'Список топ просмотренного аниме ' + nickname, description = '', colour = discord.Color.magenta() )  
            nickname = urllib.parse.quote(nickname)
            parse(get_html(f'http://shikimori.one/' + nickname + '/list/anime/mylist/completed/order-by/my'), emb)
            emb.set_thumbnail(url = "https://icons.iconarchive.com/icons/designbolts/free-multimedia/128/Film-icon.png") # иконка справа
            await ctx.send ( embed = emb)
    else:
        await ctx.send("Этот канал не предназначен для меня, используйте канал `handmade-bot`, пожалуйста!")
