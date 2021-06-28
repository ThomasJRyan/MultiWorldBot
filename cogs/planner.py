import discord
from discord.ext import commands
import asyncio

import datetime
import dateparser
import random
import traceback
from functions import *

class PlannerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        type(self).__name__ = 'Multiworld Planning commands'

    # Lets a player announce they are finished
    @commands.command(name="finish", aliases=["done"])
    async def finish(self, ctx):
        conn = Connection(ctx.guild.id)
        player = conn.queryWithValues("SELECT isFinished, gameId FROM players WHERE userId=?", (ctx.author.id,)).fetchone()
        if player == None:
            await ctx.send("You don't have a Multiworld in progress {}".format(ctx.author.display_name))
            return
        if player[0] == True:
            await ctx.send("You've already finished!")
            return
        try:
            conn.queryWithValues("UPDATE players SET isFinished=?, finishTime=? WHERE userId=?", (True, datetime.datetime.now(), ctx.author.id))
            name = ctx.author.name
            if len(ctx.author.name) + 5 > 30:
                name = ctx.author.name[:26]
            await ctx.author.edit(
                nick="[F] {}".format(name)
            )
        except Exception as e:
            print(traceback.format_exc())
            print(e)
        finally:
            game = conn.queryWithValues('SELECT startTime FROM worlds WHERE gameId=?', (player[1],)).fetchone()
            await ctx.send("Congrats on beating Ganon! It took you: {}".format(datetime.datetime.now() - game[0]))

    # Start the Multiworld timer
    @commands.command(name="start", description="Start your Multiworld's timer")
    async def start(self, ctx):
        conn = Connection(ctx.guild.id)
        game = conn.queryWithValues("SELECT roleId FROM worlds WHERE gameOwner=? AND finished=?", (ctx.author.id, False)).fetchone()
        if game == None:
            await ctx.send("You don't have a Multiworld in progress {}".format(ctx.author.display_name))
            return
        conn.queryWithValues('UPDATE worlds SET startTime=? WHERE gameOwner=? AND finished=?', (datetime.datetime.now(), ctx.author.id, False))
        await ctx.send('<@&{}> has started! Good luck everyone!'.format(game[0]))

    # Stop a Multiworld
    @commands.command(name="stop", aliases=["end"], description="Stop your Multiworld")
    async def stop(self, ctx):
        conn = Connection(ctx.guild.id)
        game = conn.queryWithValues("SELECT roleId, voiceChannelId, gameId, textChannelId FROM worlds WHERE gameOwner=? AND finished=?", (ctx.author.id, False)).fetchone()
        if game == None:
            await ctx.send("You don't have a Multiworld in progress {}".format(ctx.author.display_name))
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
        conn.queryWithValues("UPDATE worlds SET stopTime=?, finished=? WHERE gameOwner=? AND finished=?", (datetime.datetime.now(), True, ctx.author.id, False))
        await ctx.send("Your Multiworld has ended!")

    # Join a Multiworld
    @commands.command(name="join", description="Join a Multiworld")
    async def join(self, ctx, multiworld: int = None):
        if multiworld == None:
            await ctx.send("You must supply a Multiworld to join")
            return
        conn = Connection(ctx.guild.id)
        world = conn.queryWithValues("SELECT maxPlayers, open, finished, roleId FROM worlds WHERE gameId=?", (multiworld,)).fetchone()
        if world == None:
            await ctx.send("That Multiworld doesn't exist")
            return
        if world[2] == True:
            await ctx.send("That Multiworld is finished")
            return
        isInit = conn.queryWithValues("SELECT gameId FROM players WHERE userId=?", (ctx.author.id,)).fetchone()
        if isInit != None:
            await ctx.send("You are already in **Multiworld {}**".format(isInit[0]))
            return
        if world[1] == False:
            await ctx.send("That Multiworld isn't accepting any new players")
            return
        playerCount = conn.queryWithValues("SELECT COUNT(*) FROM players WHERE gameId=?", (multiworld,)).fetchone()
        if world[0] != 0:
            if playerCount[0] >= world[0]:
                await ctx.send("That Multiworld has reached it's maximum")
                return

        conn.queryWithValues("INSERT INTO players (gameId, userId, playerNum, isCreator, isFinished) VALUES (?, ?, ?, ?, ?)", (multiworld, ctx.author.id, playerCount[0]+1, False, False))
        role = ctx.guild.get_role(world[3])
        await ctx.author.add_roles(role)
        numCount = 1
        if playerCount[0] + 1 > 9:
            numCount = 2
        if playerCount[0] + 1 > 99:
            numCount = 3
        name = ctx.author.name
        if len(ctx.author.name) + 5 > 30:
            name = ctx.author.name[:26]
        await ctx.send("You have joined the Multiworld!")
        try:
            await ctx.author.edit(
                nick="{:0{numCount}d}. {}".format((playerCount[0]+1), name, numCount=numCount)
            )
        except Exception as e:
            print(traceback.format_exc())
            print(e)
            await ctx.send("I wasn't able to change your name")


    # Close a Multiworld
    @commands.command(name="close", description="Close your Multiworld to new entrants")
    async def close(self, ctx):
        conn = Connection(ctx.guild.id)
        game = conn.queryWithValues("SELECT open FROM worlds WHERE gameOwner=? AND finished=?", (ctx.author.id, False)).fetchone()
        if game == None:
            await ctx.send("You have no Multiworld in progress")
            return
        if game[0] == False:
            await ctx.send("Your Multiworld is already closed to new entrants")
            return
        conn.queryWithValues("UPDATE worlds SET open=? WHERE gameOwner=?", (False, ctx.author.id,))
        await ctx.send("Your Multiworld has been closed to new entrants")

    # Open a Multiworld
    @commands.command(name="open", description="Open your Multiworld to new entrants")
    async def open(self, ctx):
        conn = Connection(ctx.guild.id)
        game = conn.queryWithValues("SELECT * FROM worlds WHERE gameOwner=? AND finished=?", (ctx.author.id, False)).fetchone()
        if game == None:
            await ctx.send("You have no Multiworld in progress")
            return
        if game[0] == True:
            await ctx.send("Your Multiworld is already open to new entrants")
            return
        conn.queryWithValues("UPDATE worlds SET open=? WHERE gameOwner=?", (True, ctx.author.id,))
        await ctx.send("Your Multiworld has been opened to new entrants")

    # Kick someone from your Multiworld
    @commands.command(name="kick", description="Kick someone from your Multiworld")
    async def kick(self, ctx, member: discord.Member = None):
        conn = Connection(ctx.guild.id)
        game = conn.queryWithValues("SELECT gameId, gameOwner, roleId FROM worlds WHERE gameOwner=? AND finished=?", (ctx.author.id, False)).fetchone()
        if game == None:
            await ctx.send("You have no game in progress")
            return
        if member == None:
            await ctx.send("You must choose a member to kick from this Multiworld")
            return
        if ctx.author.id == member.id:
            await ctx.send("You cannot kick yourself")
            return
        player = conn.queryWithValues("SELECT * FROM players WHERE userId=? AND gameID=?", (member.id, game[0])).fetchone()
        if player == None:
            await ctx.send("That player is not in your multiworld")
            return
        role = ctx.guild.get_role(game[2])
        await member.remove_roles(role)
        try:
            await ctx.author.edit(nick=None)
        except Exception as e:
            print(traceback.format_exc())
            print(e)
        conn.queryWithValues("DELETE FROM players WHERE gameId=? AND userId=?", (game[0], member.id))

        players = conn.queryWithValues("SELECT * FROM players WHERE gameId=? ORDER BY playerNum ASC", (game[0],)).fetchall()
        numCount = 1
        if len(players) > 9:
            numCount = 2
        if len(players) > 99:
            numCount = 3
        for num, player in enumerate(players):
            conn.queryWithValues("UPDATE players SET playerNum=? WHERE userId=?", (num+1, player[1]))
            memberChange = ctx.guild.get_member(player[1])
            name = memberChange.name
            if len(memberChange.name) + 5 > 30:
                name = memberChange.name[:26]
            try:
                await memberChange.edit(nick="{:0{numCount}d}. {}".format(num+1, name, numCount=numCount))
            except Exception as e:
                print(traceback.format_exc())
                print(e)

        await ctx.send("{} has been kicked from Multiworld {}".format(member.name, game[0]))

    # Leave a Multiworld
    @commands.command(name="leave", description="Leave a Multiworld")
    async def leave(self, ctx):
        conn = Connection(ctx.guild.id)
        currentPlayer = conn.queryWithValues("SELECT * FROM players WHERE userId=?", (ctx.author.id,)).fetchone()
        if currentPlayer == None:
            await ctx.send("You can't leave a Multiworld when you're not in one")
            return
        try:
            await ctx.author.edit(nick=None)
        except Exception as e:
            print(traceback.format_exc())
            print(e)
        try:
            role = conn.queryWithValues("SELECT roleId FROM worlds WHERE gameId=?", (currentPlayer[0],)).fetchone()
            role = ctx.guild.get_role(role[0])
            await ctx.author.remove_roles(role)
        except Exception as e:
            print(traceback.format_exc())
            print(e)
        conn.queryWithValues("DELETE FROM players WHERE userId=?", (ctx.author.id, ))
        players = conn.queryWithValues("SELECT * FROM players WHERE gameId=? ORDER BY playerNum ASC", (currentPlayer[0],)).fetchall()
        if len(players) == 0:
            await ctx.send("Nobody left in the Multiworld. Ending now")
            game = conn.queryWithValues("SELECT roleId, voiceChannelId, gameId FROM worlds WHERE gameId=?", (currentPlayer[0],)).fetchone()
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
            conn.queryWithValues("DELETE FROM players WHERE gameId=?", (game[2],))
            conn.queryWithValues("UPDATE worlds SET stopTime=?, finished=? WHERE gameOwner=? AND finished=?", (datetime.datetime.now(), True, ctx.author.id, False))
        numCount = 1
        if len(players) > 9:
            numCount = 2
        if len(players) > 99:
            numCount = 3
        for num, player in enumerate(players):
            conn.queryWithValues("UPDATE players SET playerNum=? WHERE userId=?", (num+1, player[1]))
            member = ctx.guild.get_member(player[1])
            name = member.name
            if len(member.name) + 5 > 30:
                name = member.name[:26]
            try:
                await member.edit(nick="{:0{numCount}d}. {}".format(num+1, name, numCount=numCount))
            except Exception as e:
                print(traceback.format_exc())
                print(e)
        await ctx.send("You have left **Multiworld {}**".format(currentPlayer[0]))

    # List the players in your Multiworld
    @commands.command(name="listp", aliases=['plist', 'players'], description="List the players in your Multiworld")
    async def listplayers(self, ctx, world:int = None):
        conn = Connection(ctx.guild.id)
        gameId = conn.queryWithValues("SELECT gameId FROM players WHERE userId=?", (ctx.author.id,)).fetchone()
        if world != None:
            gameId = [world]
        if gameId == None:
            await ctx.send("You are not in a Multiworld")
            return
        players = conn.queryWithValues("SELECT * FROM players WHERE gameId=?", (gameId[0],)).fetchall()
        if len(players) == 0:
            await ctx.send("That Multiworld doesn't exist")
            return
        msg = "```\n"
        msg += "Multiworld {}\n\n".format(gameId[0])
        msg += "{:^5}| {:34} | {}\n".format("#", "Player", "Total Time")
        msg += "{}|{}|{}\n".format("-"*5, "-"*36, "-"*16)
        numCount = 1
        if len(players) > 9:
            numCount = 2
        if len(players) > 99:
            numCount = 3
        for player in players:
            p = ctx.guild.get_member(player[1])
            if player[4] == False:
                msg += "{:^5}| {:34}\n".format("{:0{numCount}d}".format(player[2], numCount=numCount), p.name)
            else:
                game = conn.queryWithValues('SELECT startTime FROM worlds WHERE gameId=?', (gameId[0],)).fetchone()
                msg += "{:^5}| {:34} | {}\n".format("[Fin]", p.name, player[5] - game[0])
        msg += "```"
        await ctx.send(msg)

    # List the Multiworlds
    @commands.command(name="list", description="List active Multiworlds on the server")
    async def listWorlds(self, ctx):
        conn = Connection(ctx.guild.id)
        worlds = conn.queryWithValues("SELECT gameId, maxPlayers, open, startTime FROM worlds WHERE finished=?", (False,)).fetchall()
        players = conn.query("SELECT gameId, COUNT(gameId) FROM players GROUP BY gameId").fetchall()
        timeWidth = 11
        for world in worlds:
            if len(str(world[3] - datetime.datetime.now()).split(".")[0]) > timeWidth:
                timeWidth = len(str(world[3] - datetime.datetime.now()).split(".")[0]) + 2
        msg = "```\n"
        msg += "{:^8}| {:^6} |{:^{timeWidth}}| {:^7}\n--------|--------|{}|--------\n".format("Status", "World#", "Starts In", "Players", "-"*timeWidth, timeWidth=timeWidth)
        for world in worlds:
            status = "OPEN" if world[2] == 1 else "CLOSED"
            playerCount = conn.queryWithValues("SELECT * FROM players WHERE gameId=?", (world[0],)).fetchall()
            if len(playerCount) == world[1]:
                status = "CLOSED"
            if (world[3] - datetime.datetime.now()).days < 0:
                time = str(datetime.datetime.now() - world[3]).split(".")[0]
            else:
                time = str(world[3] - datetime.datetime.now()).split(".")[0]
            if world[1] == 0:
                playerCount = "0"
            else:
                playerCount = "0/{}".format(world[1])
            for player in players:
                if player[0] == world[0]:
                    if world[1] == 0:
                        playerCount = "{}".format(player[1])
                    else:
                        playerCount = "{}/{}".format(player[1], world[1])
                    break
            msg += "{:^8}| {:^6} |{:^{timeWidth}}| {:^7}\n--------|--------|{}|--------\n".format(status, world[0], time, playerCount, "-"*timeWidth, timeWidth=timeWidth)
        msg += "```"
        await ctx.send(msg)

    # List information of a specific Multiworld
    @commands.command(name="info", description="List information of a specific multiworld")
    async def info(self, ctx):
        conn = Connection(ctx.guild.id)
        player = conn.queryWithValues("SELECT * FROM players WHERE userId=?", (ctx.author.id,)).fetchone()
        if player == None:
            await ctx.send("You are not in a Multiworld")
            return
        game = conn.queryWithValues("SELECT * FROM worlds WHERE gameId=?", (player[0],)).fetchone()
        role = ctx.guild.get_role(game[10])
        status = "OPEN" if game[3] == 1 else "CLOSED"
        startTime = str(game[5] - datetime.datetime.now()).split(".")[0]
        owner = ctx.guild.get_member(game[1])
        embed=discord.Embed(title="Multiworld {}".format(player[0]), description="\u200b", colour=role.colour)
        embed.add_field(name="Start Time", value=startTime, inline=True)
        embed.add_field(name="Status", value=status, inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=False)
        embed.add_field(name="Game Owner", value=owner.name, inline=False)
        embed.add_field(name="\u200b", value="\u200b", inline=False)
        # embed.add_field(name="Connection Type", value=game[7], inline=True)
        # embed.add_field(name="Connection Info", value=game[8], inline=True)
        # embed.add_field(name="\u200b", value="\u200b", inline=False)
        embed.add_field(name="Seed", value=game[9], inline=False)
        await ctx.send(embed=embed)

    # Plan a Multiworld
    @commands.command(name="plan", description="Plan a Multiworld")
    async def plan(self, ctx):
        conn = Connection(ctx.guild.id)
        if len(conn.queryWithValues("SELECT * FROM worlds WHERE gameOwner=? AND finished=?", (ctx.author.id, False)).fetchall()) > 0:
            await ctx.send("You already have a Multiworld in progress {}".format(ctx.author.display_name))
            return
        def check(message):
            return message.author.id == ctx.author.id

        try:
            # Grab number of players
            await ctx.send("Hello {}, please answer these questions:".format(ctx.author.display_name))
            await ctx.send("How many players are you looking to have? ('unknown' for an ambiguous amount)")
            players = await self.bot.wait_for('message', timeout=30.0, check=check)
            try:
                players = int(players.content)
                assert 256 > players > 1, "Player amount set to undefined"
            # except ValueError:
            #     await ctx.send("You must enter an integer. That means no text or decimals\n\nPlanning aborted")
            #     return
            except Exception as e:
                # await ctx.send(e)
                # return
                players = 0

            # Grab start time
            await ctx.send("How long from now do you plan to start?")
            startTime = await self.bot.wait_for('message', timeout=30.0, check=check)
            try:
                startTime = dateparser.parse(startTime.content)
                assert startTime != None, "The time you entered couldn't be parsed\n\nPlanning aborted"
                # assert datetime.datetime.now() > startTime, "You can't have a time in the past\n\nPlanning aborted"
                # print(type(startTime))
                # print(startTime)
                # print(datetime.datetime.now())
                # print(datetime.datetime.now() < startTime)
                # print((datetime.datetime.now() - startTime) + datetime.datetime.now())
                startTime = (datetime.datetime.now() - startTime) + datetime.datetime.now()
            except AssertionError as e:
                await ctx.send(e)
                return

            # Grab connection type and details
#             await ctx.send("""What kind of connection will you be using?
#             ```
# 1. Zerotier
# 2. Hamachi
# 3. Port forward
# 4. Other```""")
#             connectionType = await self.bot.wait_for('message', timeout=30.0, check=check)
#             if connectionType.content.lower() in ['1', 'zerotier']:
#                 connectionType = "Zerotier"
#                 await ctx.send("Provide additional details (Network code and IP)")
#                 connectionDetails = await self.bot.wait_for('message', timeout=30.0, check=check)
#                 connectionDetails = connectionDetails.content
#             elif connectionType.content.lower() in ['2', 'hamachi']:
#                 connectionType = "Hamachi"
#                 await ctx.send("Provide additional details (Network code and IP)")
#                 connectionDetails = await self.bot.wait_for('message', timeout=30.0, check=check)
#                 connectionDetails = connectionDetails.content
#             elif connectionType.content.lower() in ['3', 'port forward']:
#                 connectionType = "Port Forward"
#                 await ctx.send("Provide additional details (IP)")
#                 connectionDetails = await self.bot.wait_for('message', timeout=30.0, check=check)
#                 connectionDetails = connectionDetails.content
#             elif connectionType.content.lower() in ['4', 'other']:
#                 connectionType = "Other"
#                 await ctx.send("Provide additional details")
#                 connectionDetails = await self.bot.wait_for('message', timeout=30.0, check=check)
#                 connectionDetails = connectionDetails.content
#             else:
#                 await ctx.send("No valid option provided\n\nPlanner aborted")
#                 return

            connectionType = None
            connectionDetails = None

            # Grab seed settings
            await ctx.send("What seed settings are you planning to use? (Enter the seed string)")
            seedSettings = await self.bot.wait_for('message', timeout=30.0, check=check)
            seedSettings = seedSettings.content

            # Create the world
            conn.queryWithValues("INSERT INTO worlds (gameOwner, maxPlayers, open, finished, startTime, stopTime, connectionType, connectionDetails, seedSettings, roleId) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (ctx.author.id, players, True, False, startTime, None, connectionType, connectionDetails, seedSettings, None))

            # Get values
            prefix = conn.query("SELECT flag FROM settings WHERE parameter='prefix'").fetchone()[0]
            gameId = conn.queryWithValues("SELECT gameId FROM worlds WHERE gameOwner=? AND finished=?", (ctx.author.id, False)).fetchone()[0]

            # Add creator to Multiworld
            conn.queryWithValues("INSERT INTO players (gameId, userId, playerNum, isCreator, isFinished) VALUES(?, ?, ?, ?, ?)", (gameId, ctx.author.id, 1, True, False))

            # Send an all good message
            if (startTime - datetime.datetime.now()).days < 0:
                formattedTime = str(datetime.datetime.now() - startTime).split(".")[0]
            else:
                formattedTime = str(startTime - datetime.datetime.now()).split(".")[0]
            await ctx.send("Alright! Everything is set. Your Multiworld is scheduled to begin in **{}**\nMembers on this server can join the planner by typing `{}join {}`".format(formattedTime, prefix, gameId))

            # Add Cosmetics
            role = await ctx.guild.create_role(
                name="Multiworld {}".format(gameId),
                mentionable=True,
                hoist=True,
                colour=(discord.Colour.from_rgb(
                    random.randint(0,255),
                    random.randint(0,255),
                    random.randint(0,255),
                ))
            )
            conn.queryWithValues("UPDATE worlds SET roleId=? WHERE gameId=?", (role.id, gameId))
            await ctx.author.add_roles(role)
            try:
                await ctx.author.edit(nick="1. {}".format(ctx.author.name))
            except Exception as e:
                print(traceback.format_exc())
                print(e)

            # Add mod role to channels
            mod_role = None
            mod_role_id = conn.query("SELECT flag FROM settings WHERE parameter = 'mod_role'").fetchone()
            if mod_role_id:
                mod_role = ctx.guild.get_role(mod_role_id[0])

            # Permission overwrites
            try:
                overwrites = {
                    ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    ctx.guild.me: discord.PermissionOverwrite(read_messages=True),
                    role: discord.PermissionOverwrite(read_messages=True)
                }
                if mod_role:
                    overwrites.update({
                        mod_role: discord.PermissionOverwrite(read_messages=True)
                    })
            except Exception as e:
                print(traceback.format_exc())
                print(e)


            # Add voice channel
            try:
                category = conn.query("SELECT flag FROM settings WHERE parameter='categoryId'").fetchone()
                if category[0] == None:
                    return
                category = ctx.guild.get_channel(int(category[0]))
                voiceChannel = await ctx.guild.create_voice_channel(
                    name="Multiworld {}".format(gameId),
                    category=category,
                    overwrites=overwrites
                )
                conn.queryWithValues("UPDATE worlds SET voiceChannelId=? WHERE gameId=?", (voiceChannel.id, gameId))
            except Exception as e:
                print(e)

            # Add text channel
            try:
                category = conn.query("SELECT flag FROM settings WHERE parameter='categoryId'").fetchone()
                if category[0] == None:
                    return
                category = ctx.guild.get_channel(int(category[0]))
                textChannel = await ctx.guild.create_text_channel(
                    name="multiworld_{}".format(gameId),
                    category=category,
                    overwrites=overwrites
                )
                conn.queryWithValues("UPDATE worlds SET textChannelId=? WHERE gameId=?", (textChannel.id, gameId))
            except Exception as e:
                print(e)


        except asyncio.TimeoutError:
            await ctx.send("Your planner has timed out")
            return
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            await ctx.send("Something unexpected has gone wrong\n\nPlanner aborted")
            return

def setup(bot):
    bot.add_cog(PlannerCog(bot))
