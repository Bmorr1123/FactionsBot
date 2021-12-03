#!/usr/bin/python
import discord
from discord.ext import commands
from pprint import pprint as pp

def check_if_admin(ctx):
    return ctx.message.author.id in [138027430693568512, 405528235816779776]


class Factions(commands.Cog):
    def __init__(self, bot, data):
        self.bot = bot

        self.data = data

    # ---------------------------------------------------- Bot Management ----------------------------------------------

    async def set_status(self, string):
        await self.bot.change_presence(activity=discord.Game(name=string))  # Set Discord status

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Logged in and listening as {self.bot.user}!")
        await self.set_status("Managing Factions!")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, arg: int):
        print(f"Clearing {arg} messages.")
        messages = await ctx.channel.history(limit=arg + 1).flatten()
        for message in reversed(messages):
            await message.delete()

    @commands.command()
    async def ping(self, ctx):
        await ctx.reply("Pong!")

    @commands.command()
    async def spongebob(self, ctx):
        await ctx.reply("The greatest show of all time!")

    # ------------------------------------------------------ Account Management ----------------------------------------

    # --------------------------------- User Commands --------------------------------

    @commands.command(aliases=["c"])
    async def create(self, ctx, arg):
        await ctx.reply("You have created the faction: ")
        pass

    @commands.command(aliases=["l"])
    async def leave(self, ctx):
        pass

    @commands.command(aliases=["j"])
    async def join(self, ctx):

        pass

    @commands.command(aliases=["p"])
    async def promote(self, ctx, User: discord.User):
        pass

    @commands.command(aliases=["d"])
    async def demote(self, ctx, User: discord.User):
        pass

    # --------------------------------- Admin Commands -------------------------------

    @commands.command(aliases=["t"])
    @commands.check(check_if_admin)
    async def example(self, ctx, length: int = 0):
        pass

    # -------------------------------------- Voice Channel Management --------------------------------------------------

    # @commands.has_permissions(manage_channels=True)
    # @commands.Cog.listener()
    # async def on_voice_state_update(self, member, before, after):
    #     # Check if Mafia
    #     print(f"{member} updated their voice state")
    #     if after.channel is None or after.channel.name.startswith("Fusion-"):
    #         print(f"{member} updated their voice state in a fusion category.")
    #         return
    #     # Check if moved in
    #     if after.channel.name.startswith("Fusion-"):
    #         channel = after.channel
    #         num = int(channel.name[7:])
    #         category = channel.category
    #         # if len(channel.members) > 0:
    #         #     await self.create_game(channel)
