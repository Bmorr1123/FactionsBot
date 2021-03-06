#!/usr/bin/python
import atexit, json, datetime, os, discord.ext.commands as commands
from factions import Factions
import discord


'''
https://discord.com/api/oauth2/authorize?client_id=916069861837377546&permissions=8&scope=bot

'''

data = {}
with open("data.json", "r") as file:
    for key, value in json.load(file).items():
        data[key] = value


def on_close():
    with open("data.json", "w") as file:
        json.dump(data, file, indent=4)
        print("Dumped data.")
    print("Closing bot")


def main():
    atexit.register(on_close)

    today = datetime.datetime.today()

    file = open("data.json", "r")
    # Backing up data.json
    backup = open(f"backups/data-{today.year}-{today.month}-{today.day}-{today.hour}_{today.minute}.json", "w+")

    backup.writelines(file.readlines())

    file.close()
    backup.close()

    # Old backup clearing
    for file in os.listdir("backups"):
        nums = [""]
        for i in file[file.find("-") + 1:file.rfind(".")]:
            if i == "-" or i == "_":
                nums[-1] = int(nums[-1])
                nums.append("")
            else:
                nums[-1] += i
        nums[-1] = int(nums[-1])

        if nums[2] > 2000:
            nums.insert(0, nums.pop(2))

        backup_date = datetime.datetime(*nums)

        if today - backup_date > datetime.timedelta(7):
            # print(" ".join([str(num) for num in nums]))
            os.remove(f"backups/{file}")

    # Configuration Loading
    config_file = open("config.json", "r")
    config = json.load(config_file)
    config_file.close()

    # Bot stuff
    intents = discord.Intents().all()
    bot = commands.Bot(command_prefix=config["prefix"], intents=intents)

    # @bot.event
    # async def on_command_error(ctx, error):
    #     await ctx.send(error)

    cogs = [Factions(bot, data)]
    for cog in cogs:
        bot.add_cog(cog)
        print(f"Loaded \"{cog.qualified_name}\" cog!")

    bot.run(config["bot_token"])


if __name__ == '__main__':
    main()

