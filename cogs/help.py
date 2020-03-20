import discord
from discord.ext import commands

from functions import *
import datetime

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        type(self).__name__ = 'Help'
        self.userCommands = [
            ['plan', 'Plan a Multiworld'],
            ['start', 'Start your Multiworld\'s timer (optional)'],
            ['stop', 'Stop your Multiworld'],
            ['close', 'Close your Multiworld to new participants'],
            ['open', 'Open your Multiworld to new participants'],
            ['kick', 'Kick someone from your Multiworld'],
            ['list', 'List Multiworlds in the server'],
            ['listp', 'List the players in your Multiworld'],
            ['info', 'List specific information about your Multiworld'],
            ['join', 'Join a Multiworld'],
            ['leave', 'Leave your current Multiworld'],
            ['finish', 'Signal that you\'ve beaten Ganon']
        ]
        self.extraCommands = [
            ['suggest', 'Leave a suggestion to the bot maker'],
            ['report', 'Something wrong? Report it please'],
            ['url', 'In case you wanna add this bot to your server'],
            ['listall', 'List all members with a role']
        ]

    @commands.command(name="help", description="Show the help info")
    async def help(self, ctx):
        conn = Connection(ctx.guild.id)
        prefix = conn.query("SELECT flag FROM settings WHERE parameter='prefix'").fetchone()[0]
        msg = '```\n'
        msg += "MultiWorldBot Version 1.1.0 (This number is pretty arbitrary tbh)\n"
        if ctx.author.guild_permissions.administrator:
            msg += "\nAdmin Commands:\n"
            msg += "    {}{:10} | {}\n".format(prefix, "adminhelp", "Display administrator commands")
        msg += "\nMultiworld Commands:\n"
        for command in self.userCommands:
            msg += "    {}{:10} | {}\n".format(prefix, command[0], command[1])

        msg += "\nExtra Commands:\n"
        role = conn.query("SELECT flag FROM settings WHERE parameter='toggleRole'").fetchone()
        if role != None:
            msg += "    {}{:10} | {}\n".format(prefix, "toggle", "Toggle whether you are or aren't looking to play")
        for command in self.extraCommands:
            msg += "    {}{:10} | {}\n".format(prefix, command[0], command[1])

        msg += "```"
        await ctx.send(msg)

    @commands.command(name="suggest", description="Suggest a change")
    async def suggest(self, ctx, *, suggestion):
        owner = self.bot.get_user(160941453671923722)
        conn = Connection("Admin")
        conn.queryWithValues("INSERT INTO suggestions VALUES(?, ?, ?)", (ctx.author.id, suggestion, datetime.datetime.now()))
        await ctx.send("Your suggestion has been received")
        await owner.send("Suggestion received:\n```{}```".format(suggestion))

    @commands.command(name="report", description="Report an error")
    async def error(self, ctx, *, error):
        owner = self.bot.get_user(160941453671923722)
        conn = Connection("Admin")
        conn.queryWithValues("INSERT INTO errors VALUES(?, ?, ?)", (ctx.author.id, error, datetime.datetime.now()))
        await ctx.send("Your error has been reported")
        await owner.send("Error received:\n```{}```".format(error))

    @commands.command(name='url')
    async def url(self, ctx):
        await ctx.send("https://discordapp.com/api/oauth2/authorize?client_id=564280741547081729&permissions=402730064&scope=bot")

    @commands.command(name="toggle")
    async def toggle(self, ctx):
        conn = Connection(ctx.guild.id)
        role = conn.query("SELECT flag FROM settings WHERE parameter='toggleRole'").fetchone()
        if role == None:
            await ctx.send("There is no role set up to toggle")
            return
        try:
            role = ctx.guild.get_role(int(role[0]))
            if role in ctx.author.roles:
                await ctx.author.remove_roles(role)
            else:
                await ctx.author.add_roles(role)
            await ctx.send("Your willingness to play has been toggled")
        except Exception as e:
            print(e)
            await ctx.send("Something has gone wrong. You've not been toggled")

def setup(bot):
    bot.add_cog(HelpCog(bot))
