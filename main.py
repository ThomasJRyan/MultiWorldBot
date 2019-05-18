import discord
from discord.ext import commands
import asyncio

import os
from functions import *

# Checks the prefix for each guild
def prefixes_for(guild):
    conn = Connection(guild.id)
    return conn.query("SELECT flag FROM settings WHERE parameter='prefix'").fetchone()

# Bot Prefix
def get_prefix(bot, message):
    if message.author.id == 160941453671923722:
        prefixes = ["~"]
        return commands.when_mentioned_or(*prefixes)(bot, message)
    prefixes = prefixes_for(message.guild)
    return commands.when_mentioned_or(*prefixes)(bot, message)

# Bot description
description = "MultiWorldBot - For organizing OoT Mutliworlds"

# Bot cogs
cogs = [
    "cogs.owner",
    "cogs.admin",
    "cogs.planner",
    "cogs.help",
]

# Global check
def global_check(ctx):
    return ctx.message.author.bot == False

# Create the bot
bot = commands.Bot(
    command_prefix=get_prefix,
    owner_id=160941453671923722,
    description=description,
    # activity=discord.Game("Preparing the Multiworld")
    activity=discord.Game("Use ~help for commands")
)

# Start the show
if __name__ == '__main__':
    bot.add_check(global_check)
    bot.remove_command('help')
    for cog in cogs:
        try:
            bot.load_extension(cog)
        except Exception as e:
            print("Failed to load cog: {}".format(e))

# When everything is ready
@bot.event
async def on_ready():
    print("The bot is ready")
    # conn = Connection("Admin")
    #
    # for guild in bot.guilds:
    #     conn.queryWithValues("INSERT INTO guilds VALUES(?, ?, ?, ?, ?, ?)", (guild.id, guild.name, guild.owner_id, guild.owner.name, guild.large, guild.member_count))


# Creates databases for a guild upon joining it
@bot.event
async def on_guild_join(guild):
    try:
        os.remove("databases/{}.db".format(guild.id))
    except:
        pass
    conn = Connection(guild.id)
    conn.query("CREATE TABLE settings(parameter, flag)")
    conn.query("INSERT INTO settings VALUES('prefix', '~')")
    conn.query("CREATE TABLE worlds(gameId INTEGER PRIMARY KEY AUTOINCREMENT, gameOwner int, maxPlayers int, open bool, finished bool, startTime timestamp, stopTime timestamp, connectionType text, connectionDetails text, seedSettings text, roleId int, voiceChannelId int, textChannelId int)")
    conn.query("INSERT INTO worlds (gameId) VALUES (999)")
    conn.query("CREATE TABLE players(gameId int, userId int, playerNum int, isCreator bool)")
    try:
        category = await guild.create_category_channel("Multiworlds")
        conn.queryWithValues("INSERT INTO settings VALUES('categoryId', ?)", (category.id, ))
    except:
        conn.query("INSERT INTO settings VALUES('categoryId', NULL)")
    try:
        owner = bot.get_user(160941453671923722)
        msg = "I've joined a new guild:\n```\n"
        msg += "Name: {}\nID: {}\nOwner ID: {}\nOwner Name: {}\nNumber of Members: {}\n```".format(guild.name, guild.id, guild.owner_id, guild.owner.name, guild.member_count)
        await owner.send(msg)
    except Exception as e:
        print(e)
    conn = Connection("Admin")
    conn.queryWithValues("INSERT INTO guilds VALUES(?, ?, ?, ?, ?, ?)", (guild.id, guild.name, guild.owner_id, guild.owner.name, guild.large, guild.member_count))

# Run the bot
bot.run('NTY0MjgwNzQxNTQ3MDgxNzI5.XKllnQ.b_gY9oJdf2TRilmh6kAIwP4v8Qk', bot=True, reconnect=True)
