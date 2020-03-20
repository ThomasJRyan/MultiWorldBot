import discord
from discord.ext import commands

from functions import *
import datetime

class MiscCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        type(self).__name__ = 'Help'

    @commands.command(name="listall")
    async def listall(self, ctx, role: discord.Role = None):
        if role == None:
            await ctx.send("No role supplied")
            return
        msg = "```\n"
        for member in ctx.guild.members:
            if role in member.roles:
                if len(msg) + len(member.name) > 1000:
                    msg += "```"
                    await ctx.send(msg)
                    msg = "```\n"
                msg += "{}\n".format(member.name)
        msg += "```"
        await ctx.send(msg)


def setup(bot):
    bot.add_cog(MiscCog(bot))
