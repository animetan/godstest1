import os
import sys
import random
import asyncio

sys.path.append(os.path.abspath('../../settings'))
from global_sets import *
from discord.ext import commands
from collections.abc import Sequence

DECK_AMOUNT = 2

# удаление канала по id
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
# Проверка сообщения для wait
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

# Получение карты по номеру
def get_card(number):
    card = {
        1 : '2',
        2 : '3',
        3 : '4',
        4 : '5',
        5 : '6',
        6 : '7',
        7 : '8',
        8 : '9',
        9 : '10',
        10 : 'J',
        11 : 'Q',
        12 : 'K',
        13 : 'A'
    }
    return card.get(number, 'error')

# Получение вэлью карты
def valuery(card):
    value = {
        '2': 2,
        '3': 3,
        '4': 4,
        '5': 5,
        '6': 6,
        '7': 7,
        '8': 8,
        '9': 9,
        '10': 10,
        'J': 10,
        'Q': 10,
        'K': 10,
        'A': 11,
        '?': 0
    }
    return value.get(card, 0)

# Подсчитывание кол-ва очков карт. (Учёт: у дилера туз=11; у игрока с тузом 2 разных счёта, если ни один не превышает 20)
def summup(deck, diler=False, stopped=False):
    summ1 = 0 # сумма без учёта туза
    summ2 = 0 # сумма с учётом туза(=1)
    summ = [] # Общий счёт

    # проверяем кажду карту в руке
    for card in deck:
        # если карте не туз или мы подсчитываем количество игрока дилера, то записываем в 2 суммы одинаковый вэлью
        if card != 'A' or diler:
            summ1 += valuery(card)
            summ2 += valuery(card)
        # В руке игрока оказался туз: в 2 разных счёта записываем 2 разных вэлью туза
        else:
            summ1 += valuery(card)
            summ2 += 1
    
    # Если один из счётов набирает 21, то записываем только его
    if (summ2 == 21):
        summ.append(summ2)
        return(tuple(summ))
    elif (summ1 == 21):
        summ.append(summ1)
        return(tuple(summ))

    # если игра не окончена:
    if (not stopped):
        # добавляем меньший в общий счёт
        summ.append(summ2)
        # Если у нас 2 разных счёта и больший не превысил 20 (== 21 проверяли ранее)
        if (summ1 < 21) and (summ1 != summ2):
            summ.append(summ1)

    # игра окончена:
    else:
        # если 2 счёта равны - добавляем любой
        if summ1 == summ2:
            summ.append(summ1)
            return(tuple(summ))
        else:
            # если оба счёта превысили 21, то добавляем меньший из них
            if (summ1 > 21) and (summ2 > 21):
                summ.append(min(summ1, summ2))
                return(tuple(summ))
            # если больший счёт превысил 21, то 2 точно не превысил первый - добавляем второй
            elif (summ1 > 21):
                summ.append(summ2)
                return(tuple(summ))
            # если оба счёта не превысили 21, то добавляем наибольший
            elif (summ1 <= 21 and summ2 <= 21):
                summ.append(max(summ1, summ2))
                return(tuple(summ))

    # возвращаем итоговый счёт
    return tuple(summ)


class BLACKJACK:
    def __init__(self, client, channel, member, bet, can_ins, guild):
        self.client = client # бот
        self.channel = channel # созданный канал текущей игры
        self.player = member # игрок
        self.guild = guild # сервер
        self.bet = bet # ставка
        self.msg = None # embed-поле
        self.player_cards = [] # рука игрока
        self.bot_cards = [] # рука дилера
        self.deck = [] # основаная колода
        self.win = bet * 2 # итоговый выигрыш
        self.ins = False # страховка
        self.can_ins = can_ins # есть ли деньги на страховку
        self.stage = 0 # текущий ход
        self.stop = False # команда хватит
        self.blackjack = False # блекджек
        self.diler_blackjack = False # блекджек дилера

    # создание embed-сообщения; создание колоды и раздача карт
    async def start(self):
        # Создание embed-поля
        emb = discord.Embed( title = 'Blackjack:', description = '', colour = discord.Color.magenta() )
    
        emb.set_author(name = self.player.name, icon_url = self.player.avatar_url)

        emb.add_field( name = f'Ваша рука', value = f'-', inline=True)
        emb.add_field( name = f'Рука диллера', value = f'-', inline=True)
        emb.add_field( name = f'Процесс', value = f'> Раздача карт', inline=False)
        emb.add_field( name = f'Команды', value = f'-', inline=False)

        emb.set_thumbnail(url = "https://icons.iconarchive.com/icons/designcontest/casino/96/Ace-of-Hearts-icon.png")

        # Записываем этот embed для последующих изменений
        self.msg = await self.channel.send(embed = emb)

        # Заполняем колоду картами
        temp_deck = []
        for i in range(1, 14):
            for j in range(0, 4 * DECK_AMOUNT):
                self.deck.append(get_card(i))

        # перемешиваем колоду
        random.shuffle(self.deck)

        # Выдаём по 2 карты игроку и дилеру из колоды, попутно убирая первую карту колоды
        self.player_cards.append(self.deck.pop(0))
        self.bot_cards.append(self.deck.pop(0))

        self.player_cards.append(self.deck.pop(0))
        self.bot_cards.append(self.deck.pop(0))

        # таймаут
        await asyncio.sleep(2)

        return await self.game()

    # Процесс игры
    async def game(self):
        stop_stage = 0
        while True:
            # Обозначаем новый ход
            self.stage += 1

            # Колода игрока
            player_deck = '`' + ' '.join(self.player_cards) + '`'

            # Колода дилера с закрытой последней картой
            bot_cards = []
            for card in self.bot_cards:
                bot_cards.append(card)
            if (not self.stop):
                bot_cards[len(self.bot_cards) - 1] = '?'
            bot_deck = '`' + ' '.join(bot_cards) + '`'

            # Сумма карт игрока
            player_values = summup(self.player_cards, False, self.stop)

            # Сумма карт дилера
            true_bot_values = summup(self.bot_cards, True)
            bot_values = summup(bot_cards, True)

            # Если у нас блекджек с 1-го хода
            if (not self.blackjack) and (self.stage == 1) and (player_values[0] == 21):
                self.blackjack = True

            # Если у дилера блекджек с 1-го хода
            if (not self.diler_blackjack) and (self.stage == 1) and (true_bot_values[0] == 21) and (bot_cards[0] == 'A'):
                self.diler_blackjack = True

            # Если игра окончена и не хватает очков - берём ещё(+обновляем); иначе объявляем итоги
            if (self.stop) and (bot_values[0] < 17):
                self.bot_cards.append(self.deck.pop(0))
                bot_values = summup(self.bot_cards, True)
                true_bot_values = summup(self.bot_cards, True)
                bot_deck = '`' + ' '.join(self.bot_cards) + '`'
            elif (self.stop) and (bot_values[0] >= 17) and (stop_stage != self.stage):
                # 2 блекджека без страховки           
                if (self.blackjack and self.diler_blackjack and (not self.ins)):
                    await self.channel.send('Ничья')
                    self.win = self.bet
                    break
                
                # 2 блекджека со страховкой
                elif (self.blackjack and self.diler_blackjack and self.ins):
                    await self.channel.send('Выигрыш x2 от ставки')
                    self.win = self.bet * 2
                    break
                    
                # блекджек игрока со страховкой
                elif (self.blackjack and (not self.diler_blackjack) and self.ins):
                    await self.channel.send('Выигрыш x2 от ставки')
                    self.win = self.bet * 2
                    break

                # блекджек игрока без страховки
                elif (self.blackjack and (not self.diler_blackjack) and (not self.ins)):
                    await self.channel.send('Выигрыш x2.5 от ставки')
                    self.win = round(self.bet * 2.5, 2)
                    break
                
                # нет блекджеков и без страховки
                elif ((not self.blackjack) and (not self.ins)):
                    # блекджек у дилера
                    if (self.diler_blackjack):
                        await self.channel.send('Вы проиграли!')
                        self.win = 0
                        break

                    # ничья
                    if (player_values[0] == true_bot_values[0]) or (player_values[0] > 21 and true_bot_values[0] > 21):
                        await self.channel.send('Ничья')
                        self.win = self.bet
                        break
                    # у нас больше 21 - проиграли
                    elif (player_values[0] > 21):
                        await self.channel.send('Вы проиграли!')
                        self.win = 0
                        break
                    # у дилера больше 21 - выиграли
                    elif (true_bot_values[0] > 21):
                        await self.channel.send('Выигрыш x2 от ставки')
                        self.win = self.bet * 2
                        break
                    # выигрыш
                    elif (player_values[0] > true_bot_values[0]):
                        await self.channel.send('Выигрыш x2 от ставки')
                        self.win = self.bet * 2
                        break
                    #проигрыш
                    else:
                        await self.channel.send('Вы проиграли!')
                        self.win = 0
                        break

                # нет блекджеков и есть страховка    
                elif ((not self.blackjack) and self.ins):
                    # блекджек у дилера
                    if (self.diler_blackjack):
                        await self.channel.send('Вы проиграли!')
                        self.win = -(round(self.bet * 0.5, 2))
                        break

                    # ничья
                    if (player_values[0] == true_bot_values[0]) or (player_values[0] > 21 and true_bot_values[0] > 21):
                        await self.channel.send('Ничья (x0.5 от ставки с учётом страховки)')
                        self.win = round(self.bet * 0.5, 2)
                        break
                    # у нас больше 21 - проиграли
                    elif (player_values[0] > 21):
                        await self.channel.send('Вы проиграли!')
                        self.win = -(self.bet * 0.5)
                        break
                    # у дилера больше 21 - выиграли
                    elif (true_bot_values[0] > 21):
                        await self.channel.send('Выигрыш x2 от ставки')
                        self.win = round(self.bet * 1.5, 2)
                        break
                    # выигрыш
                    elif (player_values[0] > true_bot_values[0]):
                        await self.channel.send('Выигрыш x1.5 от ставки (с учётом страховки)')
                        self.win = round(self.bet * 1.5, 2)
                        break
                    #проигрыш
                    else:
                        await self.channel.send('Вы проиграли!')
                        self.win = -(round(self.bet * 0.5, 2))
                        break

            # Рендер суммы игрока
            if (len(player_values) > 1):
                player_deck += '\n{}/{}'.format(str(player_values[0]), str(player_values[1]))
            else:
                player_deck += '\n{}'.format(str(player_values[0]))

            # Рендер суммы дилера
            bot_deck += '\n{}'.format(str(bot_values[0]))

            # Список команд
            commands = ''
            commands_list = []
            if (not self.stop):
                if (bot_cards[0] == 'A') and (not self.ins) and (self.stage == 1) and self.can_ins:
                    commands += '`Страховка`({}$)'.format(str(round(self.bet * 0.5, 2)))
                    commands_list.append('страховка')
                    commands_list.append('Страховка')
                    commands += ' `Пропуск` '
                    commands_list.append('Пропуск')
                    commands_list.append('пропуск')

                elif (len(player_values) > 1) or ((player_values[0] < 21) and len(player_values) == 1):
                    if not self.diler_blackjack:
                        commands += '`Ещё` `Стоп` '
                        commands_list.append('ещё')
                        commands_list.append('Ещё')
                        commands_list.append('еще')
                        commands_list.append('Еще')
                        commands_list.append('Стоп')
                        commands_list.append('стоп')               
                    
            
                # Убираем пробел в конце
                if (len(commands) > 0):
                    commands = commands[:-1]

            # Создаём новое embed-поле для изменения со старого
            emb = discord.Embed( title = 'Blackjack:', description = '', colour = discord.Color.magenta() )

            emb.set_author(name = self.player.name, icon_url = self.player.avatar_url)
            emb.add_field( name = f'Ваша рука', value = player_deck, inline=True)
            emb.add_field( name = f'Рука дилера', value = bot_deck, inline=True)
            if (len(commands_list) > 0):
                emb.add_field( name = f'Процесс', value = f'> Ожидание игрока', inline=False)
            else:
                emb.add_field( name = f'Процесс', value = f'> Конец игры', inline=False)
            if (len(commands_list) > 0):
                emb.add_field( name = f'Команды', value = commands, inline=False)
            else: # emb.field не поддерживает пустой value
                emb.add_field( name = f'Команды', value = '-', inline=False)

            emb.set_thumbnail(url = "https://icons.iconarchive.com/icons/designcontest/casino/96/Ace-of-Hearts-icon.png")

            # Изменяем поле
            await self.msg.edit(embed = emb)

            # Если имееются команды:
            if (len(commands_list) > 0):
                try:
                    # ожидаем 2 минуты, иначе - автоматический стоп(пропуск)
                    command_wait = await self.client.wait_for("message", timeout=120.0, check=message_check(channel=self.channel, author=self.player, content=commands_list))
                    command = command_wait.content

                    if (command.lower() == 'ещё') or (command.lower() == 'еще'):
                        self.player_cards.append(self.deck.pop(0))
                    elif (command.lower() == 'страховка'):
                        self.ins = True
                    elif (command.lower() == 'стоп'):
                        self.stop = True
                        if (stop_stage == 0):
                            stop_stage = self.stage + 1
                    elif (command.lower() == 'пропуск'):
                        pass
                
                except asyncio.TimeoutError:
                    self.stop = True
                    if (stop_stage == 0):
                        stop_stage = self.stage + 1
                
            else:
                if ('пропуск' in commands_list):
                    pass
                else:
                    self.stop = True
                    if (stop_stage == 0):
                        stop_stage = self.stage + 1
            
            await asyncio.sleep(2)
            continue
        
        
        # отправляем сумму выигрыша
        await self.channel.send('**{}** :dollar:'.format(str(self.win)))

        # таймаут 5 секунд
        await asyncio.sleep(5)

        # удаляем канал
        await self.game_stop()

        # возвращаем выигрыш
        return self.win

    async def game_stop(self):
        await delete_channel(self.guild, self.channel.id)


# Получаем сообщение о создании игры
@client.command(aliases = ['blackjack', '21', 'Blackjack', 'Блекджек', 'блекджек'])
async def __blackjack(ctx, bet=0):
    if not right_channel(ctx):
        return True

    if bet < 2:
        await ctx.send('> {} \n Сумма ставки не может быть меньше 2 :dollar:'.format(ctx.message.author.name))
        return True

    with open('files/users.json', 'r') as f:
        table = json.load(f)

     # получаем id автора сообщения
    user = str(ctx.message.author.id)

    check_reg(user, table, ctx.message.author.name)

    if (bet > table[user]['dollars']):
        await ctx.send('> {} \n У вас недостаточно средств на балансе ({}$)'.format(ctx.message.author.name, str(table[user]['dollars'])))
        return True

    channel_name = (ctx.message.author.name + '-blackjack').lower()
    channel = get_channel_by_name(ctx.message.channel.guild, channel_name)

    if not channel:
        # Вычитаем ставку
        table[user]['dollars'] -= bet

        # Обновляем запись
        with open('files/users.json', 'w') as f:
            json.dump(table, f)

        # создаём канал
        new_channel = await create_text_channel(ctx.message.channel.guild, channel_name)

        # создаём новую игру
        game = BLACKJACK(client, new_channel, ctx.message.author, bet, table[user]['dollars'] >= round((bet+1) * 0.5, 2), ctx.message.channel.guild)

        # переходим к началу игры
        result = await game.start()

        # добавляем выигрыш

        with open('files/users.json', 'r') as f:
            table = json.load(f)
        
        table[user]['dollars'] += result

        # Обновляем запись
        with open('files/users.json', 'w') as f:
            json.dump(table, f)
    else:
        await ctx.send('Уже идёт активная игра')
        return True

    

    
