import os
import sys

sys.path.append(os.path.abspath('../settings'))
from global_sets import *
from discord.ext import commands
from collections.abc import Sequence

# удаление созданного канала по id
async def delete_channel(guild, channel_id):
        channel = guild.get_channel(channel_id)
        await channel.delete()

# создание нового канала в определённой категории
async def create_text_channel(guild, channel_name):
        category = get_category_by_name(guild, "Игровые комнаты") # Игровые комнаты - категория
        channel = await guild.create_text_channel(channel_name, category=category)
        return channel

# получение первого канала с заданным именем
def get_channel_by_name(guild, channel_name):
    channel = None
    for c in guild.channels:
        if c.name == channel_name:
            channel = c
            break
    return channel

# получение первой категории по заданному имени
def get_category_by_name(guild, category_name):
    category = None
    for c in guild.categories:
        if c.name == category_name:
            category = c
            break
    return category

def make_sequence(seq):
    if seq is None:
        return ()
    if isinstance(seq, Sequence) and not isinstance(seq, str):
        return seq
    else:
        return (seq,)

# https://stackoverflow.com/questions/55811719/adding-a-check-issue/55812442#55812442

def message_check(channel=None, author=None, content=None, ignore_bot=True, lower=True):
    channel = make_sequence(channel)
    author = make_sequence(author)
    content = make_sequence(content)
    if lower:
        content = tuple(c.lower() for c in content)
    def check(message):
        if ignore_bot and message.author.bot:
            return False
        if channel and message.channel not in channel:
            return False
        if author and message.author not in author:
            return False
        actual_content = message.content.lower() if lower else message.content
        if content and actual_content not in content:
            return False
        return True
    return check

def reaction_check(message=None, emoji=None, channel=None, ignore_bot=True):
    message = make_sequence(message)
    message = tuple(m.id for m in message)
    emoji = make_sequence(emoji)
    channel = make_sequence(channel)
    def check(reaction, user):
        if ignore_bot and user.bot:
            return False
        if message and reaction.message.id not in message:
            return False
        if channel and reaction.message.channel not in channel:
            return False
        if emoji and reaction.emoji not in emoji:
            return False

        return True
    return check

# Класс игры Камень-Ножницы-Бумага
class RPS:
    def __init__(self, client, channel_orig, channel, member1, member2, guild):
        self.client = client
        self.channel_orig = channel_orig # канал, в котором мы начинали новую игру
        self.channel = channel # созданный канал текущей игры
        self.member1 = member1 # первый игрок
        self.member2 = member2 # второй игрок
        self.m1_choice = 0 # выбор первого игрока
        self.m2_choice = 0 # выбор второго игрока
        self.guild = guild
        self.winner = None # будущий победитель
        # 0 - nothing; 1 - rock; 2 - paper; 3 - si.
    
    async def pre_start(self):
        msg = await self.member2.send('{} бросил вам вызов в игре камень-ножницы-бумага. Выберите соответствующий эмоджи для принятия или отказа от вызова. У вас есть 15 секунд.'.format(self.member1))
        await msg.add_reaction(emoji='\u2705')
        await msg.add_reaction(emoji='\u274C')
        
        check = reaction_check(message=msg, channel=self.member2.dm_channel, emoji=('\u2705', '\u274C'))
        try: 
            reaction, user = await self.client.wait_for('reaction_add', timeout=15.0, check=check)
            if reaction.emoji == '\u2705':
                await self.start()
            elif reaction.emoji == '\u274C':
                await self.shutdown()
        except asyncio.TimeoutError:
            await self.shutdown()
        

    async def start(self):
        # Начало игры - пишем в лс игрокам
        await self.channel_orig.send('Началась новая игра между {} и {} !'.format(self.member1.name, self.member2.name))
        await self.member1.send('{} - {} | Введите номер фигуры: 1 - камень; 2 - ножницы; 3 - бумага.'.format(self.member1.name, self.member2.name))
        await self.member2.send('{} - {} | Ждём ход первого игрока..'.format(self.member1.name, self.member2.name))
        await self.play()
    
    async def end(self):
        # Выбор лузера
        loser = ''
        if (self.winner != self.member1):
            loser = self.member1
        else:
            loser = self.member2

        # Проверяем на ничью
        if (self.winner != '='):
            # объявляем победителя
            await self.channel_orig.send('{} победил в игре против {}'.format(self.winner, loser))
            await self.winner.send('Поздаравляю, вы победили!')

            if (self.winner != self.member1):
                await self.member1.send('К сожалению, вы проиграли :(')
            else:
                await self.member2.send('К сожалению, вы проиграли :(')
        else:
            # объявляем ничью
            await self.channel_orig.send('Ничья в игре {} против {}'.format(self.member1, self.member2))
            await self.member1.send('Ничья!')
            await self.member2.send('Ничья!')
        
        # удаляем созданный ранее канал
        await delete_channel(self.guild, self.channel.id)

    async def shutdown(self):
        await self.member1.send('{} - {} | Игра была отменена'.format(self.member1.name, self.member2.name))
        await self.member2.send('{} - {} | Игра была отменена'.format(self.member1.name, self.member2.name))
        await delete_channel(self.guild, self.channel.id)

    async def play(self):
        played = False
        while played == False:
            
            # что будем ожидать в ответ на ПМ от бота
            content = ('1', '2', '3')

            # ожидание ответа от первого игрока
            msg1_wait = await self.client.wait_for("message", check=message_check(channel=self.member1.dm_channel, content=content))
            # получили ответ от первого игрока, начинаем ждать 2 игрока
            await self.member1.send('{} - {} | Ждём ход второго игрока..'.format(self.member1.name, self.member2.name))
            
            # ждём ответ от 2 игрока
            await self.member2.send('{} - {} | Введите номер фигуры: 1 - камень; 2 - ножницы; 3 - бумага.'.format(self.member1.name, self.member2.name))
            msg2_wait = await self.client.wait_for("message", check=message_check(channel=self.member2.dm_channel, content=content))

            # преваращаем сообщения игроков в текст
            msg1 = msg1_wait.content
            msg2 = msg2_wait.content

            # превращаем выбор(string) игроков в выбор(int)
            self.m1_choice = int(msg1)
            self.m2_choice = int(msg2)

            # shitcode meme, case for losers, yeah
            # можете попробовать сами придумать формулу для определения победителя, мне порядком лень :c

            if (self.m1_choice == self.m2_choice):
                self.winner = '='
            if (self.m1_choice == 1) and (self.m2_choice == 2):
                self.winner = self.member1
            if (self.m2_choice == 1) and (self.m1_choice == 2):
                self.winner = self.member2
            if (self.m1_choice == 2) and (self.m2_choice == 3):
                self.winner = self.member1
            if (self.m2_choice == 2) and (self.m1_choice == 3):
                self.winner = self.member2
            if (self.m1_choice == 3) and (self.m2_choice == 1):
                self.winner = self.member1
            if (self.m2_choice == 3) and (self.m1_choice == 1):
                self.winner = self.member2

            # выходим из цикла (while not played...)
            played = True
        
        # переходим к завершению игры
        await self.end()

# Получаем сообщение о создании игры
@client.command(aliases = ['rps', 'камень ножницы бумага', 'кнб', 'RPS', 'Rps', 'Кнб', 'КНБ'])
async def __rps(ctx, member_name='', member_tag=''):
    if (not right_channel(ctx)):
        return 0

    if member_name == '' or member_tag == '':
        await ctx.send('Укажите никнейм оппонента и его хештег (!rps Nickname(or part of nickname) Tag)')
        return 0
   
    # ищем игрока по маске (nickname + tag)
    member = None
    async for mem in ctx.guild.fetch_members(limit=None):
        if ((mem.name.lower()).find(member_name.lower()) > -1) and (mem.discriminator.find(member_tag) > -1):
            member = mem
            break

    # сообщаем, что не нашли пользователя
    if not member:
        await ctx.send('Не удалось найти пользователя')
        return 0
    
    # member == author
    if member == ctx.message.author:
        await ctx.send('Вы не можете учавствовать в игре с самим собой')
        return 0

    # member == bot
    if member.bot:
        await ctx.send('Бот не может участвовать в играх')
        return 0
    
    # 2 чаннела для проверки активной игры между двумя игрокам с разных сторон
    channel_name = ctx.message.author.name + '-' + member.name
    channel_name = channel_name.replace(' ', '-')
    channel_name = channel_name.lower()
    channel = get_channel_by_name(ctx.message.channel.guild, channel_name)

    channel_name2 = member.name + '-' + ctx.message.author.name
    channel_name2 = channel_name2.replace(' ', '-')
    channel_name2 = channel_name2.lower()
    channel2 = get_channel_by_name(ctx.message.channel.guild, channel_name2)

    # если ни один из каналов не существует (нет активной игры), то создаём
    if (not channel) and (not channel2):
        # создаём канал
        new_channel = await create_text_channel(ctx.message.channel.guild, channel_name)
        game = RPS(client, ctx.message.channel, new_channel, ctx.message.author, member, ctx.message.channel.guild)

        # переходим к началу игры
        await game.pre_start()
    else:
        await ctx.send('Уже идёт активная игра')
        return 0

    