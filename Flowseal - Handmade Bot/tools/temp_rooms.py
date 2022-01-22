import os
import sys

sys.path.append(os.path.abspath('../settings'))
from global_sets import *
from discord.ext import commands

# https://discordpy.readthedocs.io/en/latest/api.html#discord.abc.GuildChannel.delete
async def delete_channel(guild, channel_id):
        channel = guild.get_channel(channel_id)
        await channel.delete()

# https://discordpy.readthedocs.io/en/latest/api.html#discord.Guild.create_voice_channel
async def create_voice_channel(guild, channel_name, room_category):
        channel = await guild.create_voice_channel(channel_name, category=room_category)
        return channel


@client.command(aliases = ['temp_category_set'])
async def __temp_category_set (ctx, id):
    with open('files/servers.json', 'r') as f:
        table = json.load(f)

    if (not str(ctx.message.guild.id) in table):
        table[str(ctx.message.guild.id)] = {}

    category_channel = client.get_channel(int(id))
    if category_channel:
        table[str(ctx.message.guild.id)]['room_category'] = str(id)
        await ctx.send('Successful :white_check_mark:')
    else:
        await ctx.send('Wrong ID :red_circle:')

    with open('files/servers.json', 'w') as f:
        json.dump(table, f)


@client.command(aliases = ['temp_rooms_set'])
async def __temp_rooms_set (ctx, id):
    with open('files/servers.json', 'r') as f:
        table = json.load(f)

    if (not str(ctx.message.guild.id) in table):
        table[str(ctx.message.guild.id)] = {}

    create_channel = client.get_channel(int(id))
    if create_channel:
        table[str(ctx.message.guild.id)]['room_creator'] = str(id)
        await ctx.send('Successful :white_check_mark:')
    else:
        await ctx.send('Wrong ID :red_circle:')

    with open('files/servers.json', 'w') as f:
        json.dump(table, f)


# https://discordpy.readthedocs.io/en/latest/api.html#discord.on_voice_state_update
@client.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return False

    with open('files/servers.json', 'r') as f:
        table = json.load(f)

    guild_id = str(after.channel.guild.id)
    
    # Write new guild to servers settings
    if (not guild_id in table):
        table[guild_id] = {}

        with open('files/servers.json', 'w') as f:
            json.dump(table, f)

        return False

    # If we have not added temp room settings yet
    if (not 'room_creator' in table[guild_id]) or (not 'room_category' in table[guild_id]):
        return False

    room_creator = client.get_channel(int(table[guild_id]['room_creator']))
    room_category = client.get_channel(int(table[guild_id]['room_category']))

    if (not room_creator) or (not room_category):
        return False

    # If user joined to the room creator channel
    if after.channel == room_creator:
        channel = await create_voice_channel(after.channel.guild, f'{member.name} room', room_category) # create new voice channel in temp rooms category
        if channel is not None: # if we successfully created our new voice room
            await member.move_to(channel) # move member to new room
            await channel.set_permissions(member, manage_channels=True) # set perm-s to the member
    
    # If user leaved temp room
    if before.channel is not None:
        if before.channel != room_creator and before.channel.category == room_category:
            if len(before.channel.members) == 0:
                await delete_channel(before.channel.guild, before.channel.id)