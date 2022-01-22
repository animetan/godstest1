import os
import sys

from get_file import rdm

sys.path.append(os.path.abspath('../settings'))
from global_sets import *
from async_timeout import timeout
from discord.ext import commands


# Анекдот
@client.command(aliases = ['анекдот', 'Анекдот', 'Anekdot', 'Joke', 'anekdot', 'joke'])
async def __joke(ctx, type_c: str):
    if (right_channel(ctx)):
        joke_text = get_html('http://rzhunemogu.ru/RandJSON.aspx?CType=' + type_c).replace('Ошибка обращения к БД. Необходимо обратиться к разработчику: Support@RzhuNeMogu.ru', '')
        await ctx.send (joke_text)


# foot
@client.command(aliases = ['Ножки', 'ножки', 'Foot', 'foot'])
async def __foot(ctx):
    if (right_channel(ctx)):
        try:
            msg_content = {
                "file": discord.File(
                    LEGS_FOLDER + "/{}".format(rdm(LEGS_FOLDER))
                )
            }
        except FileNotFoundError:
            DISPLAY_ERROR("The folder `{}` was not found".format(LEGS_FOLDER))
            msg_content = {
                "content": "The folder with images is missing, sorry..."
            }
        except ValueError:
            DISPLAY_ERROR("The folder `{}` is empty".format(LEGS_FOLDER))
            msg_content = {"content": "The folder with images is totaly empty"}


    try:
        await ctx.send(**msg_content)
    except:
        DISPLAY_ERROR("Somethings went wrong")
        msg_content = {"content": "Somethings went wrons, sorry.\n┬─┬ ︵ /(.□. \）"}
        await ctx.send(**msg_content)
    
    
    

# ecchi
@client.command(aliases = ['ecchi', 'этти', 'Ecchi', 'Этти'])
async def __ecchi(ctx):
    if (right_channel(ctx)):
        try:
            msg_content = {
                "file": discord.File(
                    ECCHI_FOLDER + "/{}".format(rdm(ECCHI_FOLDER))
                )
            }
        except FileNotFoundError:
            DISPLAY_ERROR("The folder `{}` was not found".format(ECCHI_FOLDER))
            msg_content = {
                "content": "The folder with images is missing, sorry..."
            }
        except ValueError:
            DISPLAY_ERROR("The folder `{}` is empty".format(ECCHI_FOLDER))
            msg_content = {"content": "The folder with images is totaly empty"}


    try:
        await ctx.send(**msg_content)
    except:
        DISPLAY_ERROR("Somethings went wrong")
        msg_content = {"content": "Somethings went wrons, sorry.\n┬─┬ ︵ /(.□. \）"}
        await ctx.send(**msg_content)
    
