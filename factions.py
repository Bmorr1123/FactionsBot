#!/usr/bin/python
import discord
import requests
import json
from discord.ext import commands
from random import randint
from pprint import pprint as pp

def check_if_admin(ctx):
    return ctx.message.author.id in [138027430693568512, 405528235816779776]


permission_tiers = {
    0: "Member",
    1: "Officer",
    2: "Executive",
    3: "Co-Owner",
    4: "Owner"
}


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

    def get_uuid(self, mc_username):
        web = requests.get("https://playerdb.co/api/player/minecraft/" + mc_username)
        data = json.loads(web.content.decode())
        if data["success"]:
            return data["data"]["player"]["id"]
        return None

    def get_discord_id(self, user):
        if isinstance(user, discord.User):
            return str(user.id)
        elif isinstance(user, discord.Member):
            return str(user.id)
        elif isinstance(user, int):
            return str(user)
        elif isinstance(user, str):
            return user
        return None

    def find_users_faction(self, user):
        id = self.get_discord_id(user)
        for name, faction in self.data["factions"].items():
            if id in faction["players"].keys():
                return name
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

        await ctx.channel.guild.get_member(int(faction_owner)).add_roles(role)

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
            "requests": {},
            "wars": {},
            "declarations": {},
            "discord_info": {
                "text_channel_id": text_channel.id,
                "voice_channel_id": voice_channel.id,
                "role_id": role.id
            },
            "victories": 0,
            "losses": 0
        }

    def is_faction_channel(self, channel: discord.TextChannel):
        for faction, data in self.data["factions"].items():
            if str(channel.id) == str(data["discord_info"]["text_channel_id"]):
                return True
        return False

    async def increment_permission(self, ctx, user: discord.User, increment_by):
        pid, cid = str(ctx.author.id), str(user.id)
        action = "promote" if increment_by > 0 else "demote"

        if cid == pid:
            await ctx.reply(f"You can't {action} yourself!")
            return

        for name, faction in self.data["factions"].items():
            players = faction["players"]
            if pid in players and cid in players:
                if not players[pid]["permission_level"] >= players[cid]["permission_level"] + increment_by:
                    await ctx.reply(f"You do not have permission to {action} this player.")
                    return
                new_cpl = players[cid]["permission_level"] + increment_by

                if 0 <= new_cpl <= 4:
                    faction["players"][cid]["permission_level"] = new_cpl
                    if new_cpl == 4:
                        faction["owner"] = cid
                        players[pid]["permission_level"] -= 1
                    await ctx.reply(f"<@{cid}> has been {action}d to level {new_cpl} ({permission_tiers[new_cpl]})")
                else:
                    await ctx.reply(f"<@{cid}> cannot be {action}d to level {new_cpl}!")
                return
        await ctx.reply("Something went wrong. Please @Bmorr")

    def is_registered(self, user):
        id = self.get_discord_id(user)
        return id in self.data["players"].keys()

    def get_user(self, user):
        if not self.is_registered(user):
            return None
        id = self.get_discord_id(user)
        return self.data["players"][id]

    # ------------------------------------------------------- User Commands --------------------------------------------

    @commands.command(aliases=["r"])
    async def register(self, ctx, arg):
        if str(ctx.author.id) in self.data["players"]:
            await ctx.reply(f"You have already registered as {self.data['players'][str(ctx.author.id)]['mc_username']}")
            return
        uuid = self.get_uuid(arg)
        if uuid is None:
            await ctx.reply(f"This user doesn't exist")
            return

        self.data["players"][str(ctx.author.id)] = {
            "mc_username": arg,
            "mc_uuid": uuid,
            "pfp": f"https://crafthead.net/avatar/{uuid.replace('-', '')}"
        }
        await ctx.reply(f"Player {arg} registered")

    @commands.command(aliases=["l"])
    async def leave(self, ctx):
        pid = f"{ctx.author.id}"

        if not self.is_registered(ctx.author):
            await ctx.reply("You must be registered to use this command! Please try `.register`.")
            return

        if not self.is_faction_channel(ctx.channel):
            await ctx.reply("You must be in faction chat to use this command!")
            return

        for name, faction in self.data["factions"].items():
            if pid in faction["players"].keys():
                if faction["owner"] == pid:
                    await ctx.reply("You can't leave the faction as the owner!")
                    return

                candidate = ctx.channel.guild.get_member(ctx.author.id)
                await candidate.remove_roles(ctx.guild.get_role(faction["discord_info"]["role_id"]))
                del self.data["factions"][name]["players"][pid]
                await ctx.message.delete()
                await ctx.send(f"<@{ctx.author.id}> left the faction.")
                return
            print(f"Not in {name}")
        await ctx.reply("Could not find user in a faction! Please @Bmorr")

    @commands.command(aliases=["j"])
    async def join(self, ctx, *args):
        faction_name = " ".join(args)

        if not self.is_registered(ctx.author):
            await ctx.reply("You must be registered to use this command! Please try `.register`.")
            return

        if faction_name not in self.data["factions"]:
            await ctx.send(f"Could not find the faction \"{faction_name}\"!")
            return

        if str(ctx.author.id) in self.data["factions"][faction_name]["requests"].values():
            await ctx.send(f"You have already applied to join this faction! \"{faction_name}\"!")
            return

        if faction := self.find_users_faction(ctx.author):
            await ctx.send(f"You cannot apply to join a new faction because you are already in \"{faction}\"!")
            return

        await ctx.send(f"Requested to join the faction \"{faction_name}\".")

        channel = self.bot.get_channel(self.data["factions"][faction_name]["discord_info"]["text_channel_id"])

        embed = discord.Embed(
            title="User is requesting to join your faction!",
            color=discord.Colour.from_rgb(255 // 2, 0, 255),
            description=f"Would you like to accept <@{ctx.author.id}> into your faction?"
        )

        embed.set_image(url=f"{self.data['players'][str(ctx.author.id)]['pfp']}")
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)

        confirmation_message: discord.Message = await channel.send(embed=embed)

        await confirmation_message.add_reaction("✅")
        await confirmation_message.add_reaction("❌")

        self.data["factions"][faction_name]["requests"][str(confirmation_message.id)] = str(ctx.author.id)

    # ------------------------------------------------------ Faction Management ----------------------------------------

    @commands.command(aliases=["c"])
    async def create(self, ctx, *args):
        faction_name = " ".join(args)

        # Conditions
        if not self.is_registered(ctx.author):
            await ctx.reply("You must be registered to use this command! Please try `.register`.")
            return

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

    @commands.command()
    async def info(self, ctx, *args):
        if len(args) == 0:
            await self.list(ctx)
            return
        faction_name, faction_info = " ".join(args), {}

        for name, faction in self.data["factions"].items():
            if name.lower() == faction_name.lower():
                faction_name = name
                faction_info = faction

        if not faction_info:
            await ctx.send(f"Couldn't find faction \"{faction_name}\"")
            return

        embed = discord.Embed(
            title=f"{faction_name} Information:",
            color=ctx.channel.guild.get_role(faction_info["discord_info"]["role_id"]).color
        )

        owner = self.get_user(faction_info["owner"])
        embed.set_author(name=owner["mc_username"], icon_url=owner["pfp"])
        wr = faction_info["victories"]
        if l := faction_info["losses"]:
            wr /= l

        embed.add_field(name="Win Rate:", value=wr, inline=True)

        embed.add_field(
            name="Member List:",
            value="\n".join([f"<@{player}>: {permission_tiers[info['permission_level']]}" for player, info in faction_info["players"].items()]),
            inline=False
        )

        await ctx.send(embed=embed)

    @commands.command()
    async def list(self, ctx):
        embed = discord.Embed(
            title=f"Faction List:",
            color=discord.Color.from_rgb(255, 255, 255)
        )

        for name, info in self.data["factions"].items():
            value = f"<@{info['owner']}>"
            embed.add_field(name=name, value=value, inline=False)

        await ctx.send(embed=embed)

    @commands.command()
    async def kick(self, ctx, user: discord.User):
        pid, cid = str(ctx.author.id), str(user.id)
        for name, faction in self.data["factions"].items():
            players = faction["players"]
            if pid in players and cid in players:
                if not players[pid]["permission_level"] > players[cid]["permission_level"]:
                    await ctx.reply(f"You do not have permission to kick this player.")
                    return

                candidate = ctx.channel.guild.get_member(int(cid))
                await candidate.remove_roles(ctx.guild.get_role(faction["discord_info"]["role_id"]))
                if randint(0, 24):
                    await candidate.send(f"You've been kicked from {name}!")
                else:
                    await candidate.send(f"{name} doesn't want you anymore. L + ratio + ur malding + ur mom's fat")
                del faction["players"][cid]
                await ctx.send(f"<@{pid}> kicked <@{cid}>!")
                await ctx.message.delete()

    @commands.command()
    async def delete(self, ctx, *args):
        faction_name = " ".join(args)

        # Conditions
        if ctx.channel.category.name.upper() != "MINECRAFT SERVER":
            await ctx.reply("Can't do that in this channel.")
            return

        if faction_name not in self.data["factions"]:
            await ctx.reply(f"That faction doesn't exist!")
            return
        faction = self.data["factions"][faction_name]
        if faction["owner"] != str(ctx.author.id):
            await ctx.reply(f"You do not own that faction!")
            return

        await ctx.channel.guild.get_channel(faction["discord_info"]["voice_channel_id"]).delete()
        await ctx.channel.guild.get_channel(faction["discord_info"]["text_channel_id"]).delete()
        await ctx.channel.guild.get_role(faction["discord_info"]["role_id"]).delete()

        del self.data["factions"][faction_name]
        await ctx.reply(f"You have successfully deleted the faction: \"{faction_name}\"")

    @commands.command()
    async def color(self, ctx, r: int, g: int, b: int):
        faction = self.find_users_faction(ctx.author)
        if faction:
            faction = self.data["factions"][faction]
        else:
            await ctx.send(f"Can't find faction for <@{ctx.author.id}>!")
            return

        if faction["players"][self.get_discord_id(ctx.author)]["permission_level"] < 3:
            await ctx.send(f"<@{ctx.author.id}> does not have permission to do this.")
            return

        await ctx.channel.guild.get_role(faction["discord_info"]["role_id"]).edit(color=discord.Color.from_rgb(r, g, b))
        await ctx.reply(f"Successfully changed faction color!")

    @commands.command()
    async def rename(self, ctx, *args):
        faction_name = " ".join(args)

        if faction_name in self.data["factions"].keys():
            await ctx.send(f"A faction by this name already exists!")
            return

        faction = self.find_users_faction(ctx.author)
        og_name = faction
        if faction:
            faction = self.data["factions"][faction]
        else:
            await ctx.send(f"Can't find faction for <@{ctx.author.id}>!")
            return

        if faction["players"][self.get_discord_id(ctx.author)]["permission_level"] < 3:
            await ctx.send(f"<@{ctx.author.id}> does not have permission to do this.")
            return

        await ctx.channel.guild.get_channel(faction["discord_info"]["voice_channel_id"]).edit(name=faction_name)
        await ctx.channel.guild.get_channel(faction["discord_info"]["text_channel_id"]).edit(name=faction_name.lower() + " chat")
        await ctx.channel.guild.get_role(faction["discord_info"]["role_id"]).edit(name=faction_name)
        self.data["factions"][faction_name] = faction
        del self.data["factions"][og_name]
        await ctx.reply(f"Successfully renamed \"{og_name}\" to \"{faction_name}\"!")

    # @commands.command(aliases=["b"])
    # async def declare(self, ctx, *args):
    #     faction_name = " ".join(args)
    #     src_faction = self.find_users_faction(str(ctx.author.id))
    #     if faction_name in self.data["factions"]:
    #         await ctx.send(f"Requested to start a war \"{faction_name}\".")
    #         id = self.data["factions"][faction_name]["discord_info"]["text_channel_id"]
    #         channel = self.bot.get_channel(id)
    #         embed = discord.Embed(
    #             title=f"Would you like to accept a war with {src_faction}?",
    #             color=discord.Colour.from_rgb(255 // 2, 0, 255),
    #             #description=f"Would you like to accept a war with {src_faction}?"
    #         )
    #         embed.set_image(url=f"{self.data['players'][str(ctx.author.id)]['pfp']}")
    #         embed.set_author(name=ctx.author.name + " is requesting to start a war!", icon_url=ctx.author.avatar_url)
    #
    #         confirmation_message: discord.Message = await channel.send(embed=embed)
    #
    #         await confirmation_message.add_reaction("✅")
    #         await confirmation_message.add_reaction("❌")
    #
    #         self.data["factions"][faction_name]["requests"][str(confirmation_message.id)] = str(ctx.author.id)
    #
    #     else:
    #         await ctx.send(f"Could not find the faction \"{faction_name}\"!")
    #     pass

    @commands.command(aliases=["p"])
    async def promote(self, ctx, user: discord.User):
        await self.increment_permission(ctx, user, +1)

    @commands.command(aliases=["d"])
    async def demote(self, ctx, user: discord.User):
        await self.increment_permission(ctx, user, -1)

    # ---------------------------------------------- Admin Commands ----------------------------------------------------

    @commands.command(aliases=["test"])
    @commands.check(check_if_admin)
    async def example(self, ctx, length: int = 0):
        pass

    # --------------------------------------- Listeners ----------------------------------------------------------------

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        faction_channels = {
            str(value["discord_info"]["text_channel_id"]): name
            for name, value in self.data["factions"].items()
        }

        if str(payload.channel_id) not in faction_channels:
            return

        faction_name = faction_channels[str(payload.channel_id)]
        faction = self.data["factions"][faction_name]

        if str(payload.message_id) not in faction["requests"]:
            return
        if str(payload.member.id) not in faction["players"]:
            return

        candidate_id = int(faction["requests"][str(payload.message_id)])
        channel = self.bot.get_channel(payload.channel_id)
        if faction["players"][str(payload.member.id)]["permission_level"] > 0:
            nothing = False
            if self.find_users_faction(candidate_id):
                await channel.send(f"<@{candidate_id}> already joined another faction!")
            elif payload.emoji.name == "✅":
                faction["players"][str(candidate_id)] = {
                    "permission_level": 0
                }
                await channel.guild.get_member(candidate_id).add_roles(channel.guild.get_role(faction["discord_info"]["role_id"]))
                await channel.send(f"<@{candidate_id}> was accepted by <@{str(payload.member.id)}>!")
            elif payload.emoji.name == "❌":
                await self.bot.get_user(candidate_id).send(f"Sorry, you have been denied from joining {faction_name}.")
            else:
                nothing = True
            if not nothing:
                message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
                await message.delete()
                del faction["requests"][str(payload.message_id)]

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
