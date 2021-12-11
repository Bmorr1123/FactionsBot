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

        self.channel = None

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

    # ------------------------------------------------------ Non-commands ----------------------------------------------

    def create_faction(self, faction_name, faction_owner):

        # text_overwrites = {
        #     channel.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        # }
        # voice_overwrites = {
        #     channel.guild.default_role: discord.PermissionOverwrite(connect=False),
        # }
        # voice_channel = await channel.guild.create_voice_channel(
        #     'Mafia Game Room',
        #     category=channel.category,
        #     overwrites=voice_overwrites
        # )
        # text_channel = await channel.guild.create_text_channel(
        #     'Mafia-Text-Room',
        #     category=channel.category,
        #     overwrites=text_overwrites
        # )

        self.data["factions"][faction_name] = {
            "owner": faction_owner,
            "players": {
                f"{faction_owner}": {
                    "permission_level": 4
                }
            },
            "wars": {},
            "requests": [],
            "discord_info": {
                "channel_id": 0,
                "role_id": 0
            },
            "victories": 0,
            "losses": 0
        }

    # ------------------------------------------------------ Faction Management ----------------------------------------

    @commands.command(aliases=["c"])
    async def create(self, ctx, *args):
        faction_name = " ".join(args)
        if faction_name not in self.data["factions"]:
            await ctx.reply(f"You have created the faction: \"{faction_name}\"")
        else:
            await ctx.reply(f"That faction already exists!")

    @commands.command(aliases=["l"])
    async def leave(self, ctx):
        pass

    @commands.command(aliases=["j"])
    async def join(self, ctx, *args):
        faction_name = " ".join(args)
        if faction_name in self.data["factions"]:
            await ctx.send(f"Requested to join the faction \"{faction_name}\".")
            self.data["factions"][faction_name]["requests"].append(ctx.author.id)
        else:
            await ctx.send(f"Could not find the faction \"{faction_name}\"!")
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
