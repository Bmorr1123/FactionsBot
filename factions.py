#!/usr/bin/python
import discord
import requests
import json
from discord.ext import commands
from random import randint
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

    def getMcId(self, mc_username):
        web = requests.get("https://playerdb.co/api/player/minecraft/" + mc_username)
        data = str(json.loads(web.content.decode()))
        if data["success"]:
            return data["data"]["player"]["id"]
        return None

    async def create_faction(self, ctx, faction_name, faction_owner):
        channel = ctx.channel

        # Role creation
        role = await channel.guild.create_role(
            name=faction_name,
            color=discord.Color.from_rgb(
                randint(0, 255),
                randint(0, 255),
                randint(0, 255)
            ),
            reason=f"{ctx.author.name} requested a new faction be created."
        )
        # Permissions Overwrites
        text_overwrites = {
            channel.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            role: discord.PermissionOverwrite(read_messages=True)
        }
        voice_overwrites = {
            channel.guild.default_role: discord.PermissionOverwrite(connect=False),
            role: discord.PermissionOverwrite(connect=True)
        }

        # Channel creation
        voice_channel = await channel.guild.create_voice_channel(
            f"{faction_name}",
            category=channel.category,
            overwrites=voice_overwrites,
            reason=f"{ctx.author.name} requested a new faction be created."
        )
        text_channel = await channel.guild.create_text_channel(
            f"{faction_name.lower()}-chat",
            category=channel.category,
            overwrites=text_overwrites,
            reason=f"{ctx.author.name} requested a new faction be created."
        )

        # Adding it to the save
        self.data["factions"][faction_name] = {
            "owner": faction_owner,
            "players": {
                faction_owner: {
                    "permission_level": 4
                }
            },
            "wars": {},
            "requests": {},
            "discord_info": {
                "text_channel_id": text_channel.id,
                "voice_channel_id": voice_channel.id,
                "role_id": role.id
            },
            "victories": 0,
            "losses": 0
        }

    # ------------------------------------------------------ Faction Management ----------------------------------------

    @commands.command(aliases=["r"])
    async def register(self, ctx, arg):
        if str(ctx.author.id) in self.data["players"]:
            await ctx.reply(f"You have already registered as {self.data['players'][str(ctx.author.id)]['mc_username']}")
            return
        uuid = self.getMcId(arg)
        if uuid == None:
            await ctx.reply(f"This user doesn't exist")
            return

        self.data["players"][str(ctx.author.id)] = {
            "mc_username": arg,
            "mc_uuid": uuid,
            "pfp": ("https://crafthead.net/avatar/" + uuid).replace("-","")
        }
        await ctx.reply(f"Player {arg} registered")

    @commands.command(aliases=["c"])
    async def create(self, ctx, *args):
        faction_name = " ".join(args)

        # Conditions
        if ctx.channel.category.name.upper() != "MINECRAFT SERVER":
            await ctx.reply("Can't do that in this channel.")
            return

        if faction_name in self.data["factions"]:
            await ctx.reply(f"That faction already exists!")
            return

        for faction in self.data["factions"].values():
            if f"{ctx.author.id}" in faction["players"].keys():
                await ctx.reply("You are already in a faction!")
                return

        await self.create_faction(ctx, faction_name, str(ctx.author.id))
        await ctx.reply(f"You have successfully created the faction: \"{faction_name}\"")

    @commands.command(aliases=["l"])
    async def leave(self, ctx):
        for name, faction in self.data["factions"].items():
            if f"{ctx.author.id}" in faction["players"].keys():
                await ctx.reply("You are already in a faction!")
                return

    @commands.command(aliases=["j"])
    async def join(self, ctx, *args):
        faction_name = " ".join(args)
        if faction_name in self.data["factions"]:
            await ctx.send(f"Requested to join the faction \"{faction_name}\".")
            id = self.data["factions"][faction_name]["discord_info"]["text_channel_id"]
            channel = self.bot.get_channel(id)
            embed = discord.Embed(
                title="User is requesting to join your faction!",
                color=discord.Colour.from_rgb(255//2, 0, 255),
                description=f"Would you like to accept <@{ctx.author.id}> into your faction?"
            )
            embed.set_image(url=f"{self.data['players'][str(ctx.author.id)]['pfp']}")
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)

            confirmation_message: discord.Message = await channel.send(embed=embed)

            await confirmation_message.add_reaction("✅")
            await confirmation_message.add_reaction("❌")

            self.data["factions"][faction_name]["requests"][str(confirmation_message.id)] = str(ctx.author.id)

        else:
            await ctx.send(f"Could not find the faction \"{faction_name}\"!")
        pass

    @commands.command(aliases=["b"])
    async def declare(self, ctx, *args):
        faction_name = " ".join(args)
        if faction_name in self.data["factions"]:
            await ctx.send(f"Requested to start a war \"{faction_name}\".")
            id = self.data["factions"][faction_name]["discord_info"]["text_channel_id"]
            channel = self.bot.get_channel(id)
            embed = discord.Embed(
                title="User is requesting to start a war!",
                color=discord.Colour.from_rgb(255 // 2, 0, 255),
                description=f"Would you like to accept <@{ctx.author.id}> into your faction?"
            )
            embed.set_image(url=f"{self.data['players'][str(ctx.author.id)]['pfp']}")
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)

            confirmation_message: discord.Message = await channel.send(embed=embed)

            await confirmation_message.add_reaction("✅")
            await confirmation_message.add_reaction("❌")

            self.data["factions"][faction_name]["requests"][str(confirmation_message.id)] = str(ctx.author.id)

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

    # --------------------------------------- Listeners ----------------------------------------------------------------

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        print(f"{payload.member.name} added {payload.emoji}")
        faction_channels = {str(value["discord_info"]["text_channel_id"]): name for name, value in self.data["factions"].items()}
        if str(payload.channel_id) not in faction_channels:
            print("Not a valid channel")
            return
        faction_name = faction_channels[str(payload.channel_id)]
        faction = self.data["factions"][faction_name]

        if str(payload.message_id) in faction["requests"]:
            print("Found the request")
            candidate_id = int(faction["requests"][str(payload.message_id)])
            print(f"{payload.member.id}")
            print(self.bot.get_guild(payload.guild_id).get_member(payload.member.id))
            if faction["players"][str(payload.member.id)]["permission_level"] > 0:
                print(f"{payload.member.name} has permission to to accept/deny.")
                nothing = False
                if payload.emoji.name == "✅":
                    print("W")
                    faction["players"][candidate_id] = {
                        "permission_level": 0
                    }
                elif payload.emoji.name == "❌":
                    print(f"L {candidate_id}, {type(candidate_id)}")
                    await discord.Member(id=int(candidate_id)).send(f"Sorry, you have been denied from joining {faction_name}.")
                else:
                    nothing = True
                # if not nothing:
                #     await self.bot.get_message(payload.message_id).delete()
                #     del faction["requests"][str(payload.message_id)]

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
