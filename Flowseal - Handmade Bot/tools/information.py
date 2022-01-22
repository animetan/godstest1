import os
import sys

sys.path.append(os.path.abspath('../settings'))
from global_sets import *
from async_timeout import timeout
from discord.ext import commands

# Удаляем изначальную команду help
client.remove_command('help')

@client.command(aliases = ['Help', 'help', 'HELP', 'hELP', 'хелп', 'Хелп', 'ХЕЛП', 'хЕЛП'])
async def __help (ctx):
    if (right_channel(ctx)):
        emb = discord.Embed( title = 'Доступные команды:', description = '', colour = discord.Color.magenta() )
    
        emb.set_author(name = ctx.author.name, icon_url = ctx.author.avatar_url)

        emb.add_field( name = 'Информация', value = f'`{prefix}help` `{prefix}ping` `{prefix}anime`', inline=False)
        emb.add_field( name = 'Развлечение', value = f' `{prefix}ecchi` `{prefix}foot` `{prefix}joke 1-18` ', inline=False)
        emb.add_field( name = 'Модерирование', value = f' `{prefix}clear` `{prefix}temp_category_set` `{prefix}temp_rooms_set`', inline=False)
        emb.add_field( name = 'Музыка', value = f' `{prefix}play` `{prefix}loop` `{prefix}remove` `{prefix}shuffle` `{prefix}volume` `{prefix}queue` `{prefix}skip` `{prefix}stop` `{prefix}pause` `{prefix}resume` `{prefix}current` `{prefix}leave` `{prefix}playlist_help` ', inline=True)
        emb.add_field( name = 'Рандом', value = f' `{prefix}roll` `{prefix}coin`', inline=False)
        emb.add_field( name = 'Игры', value = f' `{prefix}кнб NICK TAG` `{prefix}casino_help` ', inline=False)
        
        emb.set_thumbnail(url = "https://icons.iconarchive.com/icons/alecive/flatwoken/128/Apps-Help-icon.png")
        await ctx.send ( embed = emb)

# Помощь по casino
@client.command(aliases = ['casino_help', 'Casino_help', 'CASINO_HELP'])
async def __casino_help (ctx):
    if (right_channel(ctx)):
        emb = discord.Embed( title = 'Casino:', description = '', colour = discord.Color.magenta() )
    
        emb.set_author(name = ctx.author.name, icon_url = ctx.author.avatar_url)

        emb.add_field( name = f'{prefix}profile', value = f'Статистика вашего профиля', inline=False)
        emb.add_field( name = f'{prefix}top', value = f'Рейтинг пользователей', inline=False)
        emb.add_field( name = f'{prefix}bonus', value = f'Получение бонуса', inline=False)
        emb.add_field( name = f'{prefix}blackjack `bet`', value = f'Игра в blackjack(21)', inline=False)
        emb.add_field( name = f'{prefix}slot `bet`', value = f'Игра в слот', inline=False)

        emb.set_thumbnail(url = "https://icons.iconarchive.com/icons/neiio/prime-dock-2/128/Games-alt-icon.png")
        await ctx.send ( embed = emb)

# Помощь по плейлистам
@client.command(aliases = ['playlist_help', 'Playlist_help'])
async def __playlist_help (ctx):
    if (right_channel(ctx)):
        emb = discord.Embed( title = 'Плейлисты:', description = '', colour = discord.Color.magenta() )
    
        emb.set_author(name = ctx.author.name, icon_url = ctx.author.avatar_url)

        emb.add_field( name = f'{prefix}playlist_help', value = f'Вывод помощи по плейлистам', inline=False)
        emb.add_field( name = f'{prefix}playlist `name`', value = f'Информация о плейлисте', inline=False)
        emb.add_field( name = f'{prefix}playlist_create `name`', value = f'Создать новый плейлист', inline=False)
        emb.add_field( name = f'{prefix}playlist_delete `name`', value = f'Удалить плейлист', inline=False)
        emb.add_field( name = f'{prefix}playlist_add `playlist` `name`', value = f'Добавить трек в плейлист', inline=False)
        emb.add_field( name = f'{prefix}playlist_play `playlist`', value = f'Добавить плейлист в очередь', inline=False)
        emb.add_field( name = f'{prefix}playlist_remove `playlist` `index`', value = f'Удалить трек из плейлиста', inline=False)
        emb.add_field( name = f'{prefix}playlist_rename `playlist` `new_name`', value = f'Переименовать плейлист', inline=False)
        emb.add_field( name = f'{prefix}playlists `page`', value = f'Вывод доступных плейлистов', inline=False)
        emb.add_field( name = f'{prefix}playlists_my', value = f'Вывод доступных плейлистов созданных вами', inline=False)  
        emb.add_field( name = f'{prefix}playlists_update', value = f'Обновление плейлистов', inline=False)   

        emb.set_thumbnail(url = "https://icons.iconarchive.com/icons/dtafalonso/yosemite-flat/128/Music-icon.png")
        await ctx.send ( embed = emb)



# Ping
@client.command(aliases = ['Ping', 'PING', 'pING', 'ping', 'пинг', 'Пинг', 'пИНГ'])
async def __ping(ctx):
    if (right_channel(ctx)):
        ping = client.ws.latency
    
        ping_emoji = '🟩🔳🔳🔳🔳'
    
        if ping > 0.10:
            ping_emoji = '🟧🟩🔳🔳🔳'
    
        if ping > 0.15:
            ping_emoji = '🟥🟧🟩🔳🔳'
    
        if ping > 0.20:
            ping_emoji = '🟥🟥🟧🟩🔳'
    
        if ping > 0.25:
            ping_emoji = '🟥🟥🟥🟧🟩'
    
        if ping > 0.30:
            ping_emoji = '🟥🟥🟥🟥🟧'
    
        if ping > 0.35:
            ping_emoji = '🟥🟥🟥🟥🟥'
    
        message = await ctx.send('Погоди, мужик. . .')
        await message.edit(content = f'Пинг сервера: {ping_emoji} `{ping * 1000:.0f}ms`')
