import discord
from discord.ext import commands
import traceback
import datetime

from functions import *

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        type(self).__name__ = 'Admin commands'
        self.adminCommands = [
            ['setprefix', 'Sets the command prefix for the server'],
            ['settoggle', 'Sets the role you want to use as a "willing-to-play" toggle'],
            ['remove', 'Remove a Multiworld from the server'],
            ['ping', 'Ping MultiWorldBot to ensure it\'s working']
        ]

    async def is_admin(ctx):
        # print(ctx.author.guild_permissions.administrator)
        return ctx.author.guild_permissions.administrator

    # Display commands for administrators
    @commands.command(name="adminhelp", description="Commands for administrators")
    @commands.check(is_admin)
    async def adminhelp(self, ctx):
        conn = Connection(ctx.guild.id)
        prefix = conn.query("SELECT flag FROM settings WHERE parameter='prefix'").fetchone()[0]
        msg = '```\n'
        msg += "MultiWorldBot Version 1.0.0\n"
        msg += "Protip: Move my role up a couple pegs to have numbers automatically assigned to player names\n\n"
        msg += "Admin Commands:\n"
        for command in self.adminCommands:
            msg += "    {}{:10} | {}\n".format(prefix, command[0], command[1])
        msg += "```"
        await ctx.send(msg)

    @commands.command(name='settoggle')
    @commands.check(is_admin)
    async def settoggle(self, ctx, role: discord.Role = None):
        if role == None:
            await ctx.send("Format: `settoggle <@role>`")
            return
        bot = ctx.guild.get_member(564280741547081729)
        if role.position >= bot.top_role.position:
            await ctx.send("That role is above me and won't work as a toggle")
            return
        try:
            conn = Connection(ctx.guild.id)
            conn.query("DELETE FROM settings WHERE parameter='toggleRole'")
            conn.queryWithValues("INSERT INTO settings VALUES(?, ?)", ("toggleRole", role.id))
            await ctx.send("Toggle role has been set")
        except:
            await ctx.send("Something has gone wrong, please try again")

    # Remove a multiworld in the server
    @commands.command(name="remove")
    @commands.check(is_admin)
    async def stop(self, ctx, gameId: int = None):
        conn = Connection(ctx.guild.id)
        game = conn.queryWithValues("SELECT roleId, voiceChannelId, gameId, textChannelId FROM worlds WHERE gameId=? AND finished=?", (gameId, False)).fetchone()
        if game == None:
            await ctx.send("That Multiworld doesn't exist {}".format(ctx.author.display_name))
            return
        try:
            role = ctx.guild.get_role(game[0])
            await role.delete()
        except Exception as e:
            print(traceback.format_exc())
            print(e)
        try:
            voiceChannel = ctx.guild.get_channel(game[1])
            await voiceChannel.delete()
        except Exception as e:
            print(traceback.format_exc())
            print(e)
        try:
            textChannel = ctx.guild.get_channel(game[3])
            await textChannel.delete()
        except Exception as e:
            print(traceback.format_exc())
            print(e)
        players = conn.queryWithValues("SELECT userId FROM players WHERE gameId=?", (game[2],))
        for player in players:
            member = ctx.guild.get_member(player[0])
            try:
                await member.edit(nick=None)
            except Exception as e:
                print(traceback.format_exc())
                print(e)
        conn.queryWithValues("DELETE FROM players WHERE gameId=?", (game[2],))
        conn.queryWithValues("UPDATE worlds SET stopTime=?, finished=? WHERE gameId=? AND finished=?", (datetime.datetime.now(), True, gameId, False))
        await ctx.send("Multiworld {} has ended".format(gameId))

    # Tests that the bot works
    @commands.command(name="ping", description="Make sure MultiWorldBot is working")
    @commands.check(is_admin)
    async def ping(self, ctx):
        await ctx.send("Pong!")

    # Allows each server to set their prefix
    @commands.command(name="setprefix", description="Set prefix for server")
    @commands.check(is_admin)
    async def setprefix(self, ctx, prefix:str = None):
        conn = Connection(ctx.guild.id)
        conn.query("DELETE FROM settings WHERE parameter='prefix'")
        if prefix == None:
            conn.queryWithValues("INSERT INTO settings VALUES(?, ?)", ("prefix", "~"))
            await ctx.send("No prefix specified, defaulted to ~")
        else:
            conn.queryWithValues("INSERT INTO settings VALUES(?, ?)", ("prefix", prefix))
            await ctx.send("Prefix set to {}".format(prefix))

def setup(bot):
    bot.add_cog(AdminCog(bot))
