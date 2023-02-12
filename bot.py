# Created by JStockwell on GitHub
import os
import discord
import requests
import json
import datetime
import Paginator

import utils.help as Help
import utils.roles as Roles
from utils.runs import get_wr_ce, get_wr_standard
from utils.game_gen import gen_db

from dotenv import load_dotenv
from discord.ext import commands, tasks
from datetime import datetime as dt
from tinydb import TinyDB, Query

### --- REST api Initialization --- ###

base_url = "https://www.speedrun.com/api/v1/"
games_path = "json/games.json"

### --- Bot Initialization --- ###

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEST_TOKEN = os.getenv('TEST_TOKEN')
SRCOM_TOKEN = os.getenv('SRCOM_TOKEN')
TINYDB_PATH = os.getenv('TINYDB_PATH')
DEV_MODE = os.getenv('DEV_MODE') == 'True'
GEN_DB_FLAG = True

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
bot.remove_command('help')

if not DEV_MODE or (DEV_MODE and GEN_DB_FLAG):
    gen_db(games_path)
game_db = json.load(open(games_path, 'r'))
db = TinyDB(TINYDB_PATH)

### --- Functions --- ###

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    post_verification.start()
    await Roles.base_reactions(bot)

@bot.event
async def on_error(event, *args, **kwargs):
    with open('err.log', 'a') as f:
        if event == 'on_message':
            f.write(f'Unhandled message: {args[0]}\n')
        else:
            raise ValueError(f'Unhandled event: {event}')

@bot.event
async def on_command_error(ctx, error):
    message = " "

    if DEV_MODE:
        message += f'\n{error}'
    else:
        message += f'An error has occurred, please try again!'

    print(error)
    await ctx.send(message)

@bot.event
async def on_raw_reaction_add(payload):
    await Roles.handle_reaction(payload, bot, False)

@bot.event
async def on_raw_reaction_remove(payload):
    await Roles.handle_reaction(payload, bot, True)

### --- Commands --- ###

@bot.command(name="hello", help="How are you?")
async def hello(ctx):
    await ctx.send("Hello!")

@bot.command(name="beginnerhelp", help="Document with all relevant information for beginners")
async def beginner_help(ctx):
    await ctx.send("https://docs.google.com/document/d/1n9hQe9EZO59_sURBwirt9CwpzmBoge_8OWe21w6dZMA/edit?usp=sharing")

@bot.command(name="socials", help="Link to the TICO Speedruns socials")
async def socials(ctx):
    embed = discord.Embed(title="Follow us at!", color=0x00ff00)
    message = "Youtube: https://www.youtube.com/channel/UCMLlkQ8CFV8BqXFz86usFeQ\n"
    message += "Twitch: https://www.twitch.tv/teamicospeedruns\n"
    message += "Twitter: https://twitter.com/IcoSpeedruns\n"

    embed.add_field(name="", value=message, inline=False)
    await ctx.send(embed=embed)

@bot.command(name="help", help="List of commands or help with a specific command")
async def help(ctx, *args):
    if len(args) == 0:
        embed = discord.Embed(title="List of commands", color=0x00ff00)
        embed.add_field(name="", value="If you need to know more about a command, use !help <command>", inline=False)
        for command in bot.commands:
            if command.name != "help":
                embed.add_field(name=command.name, value=command.help, inline=False)
        await ctx.send(embed=embed)
    else:
        bot_command = None
        for command in bot.commands:
            if command.name == args[0]:
                bot_command = command
                break

        if bot_command is None:
            await ctx.send("Command not found")
        else:
            await Help.help_command(ctx, bot_command)

# Format: !wr <game> <category> <var_1> <var_2>...
# Example: !wr ico co-op 60hz
@bot.command(name="wr", help="Get the world record for a category")
async def get_wr(ctx, *args):
    # Get the game id
    game_name = args[0].lower()

    game = game_db[game_name]

    if game_name == "ce":
        await get_wr_ce(bot, ctx, game, args)

    else:
        await get_wr_standard(bot, ctx, game, args)

@tasks.loop(seconds = 300) # repeat after every five minutes
async def post_verification():
    channel_lookup = json.load(open('json/channels.json', 'r'))
    notifications = requests.get(f"{base_url}notifications", headers={"X-API-Key": SRCOM_TOKEN}).json()["data"]
    for notification in notifications:
        notif_time = dt.strptime(notification['created'].replace('T',' ').replace('Z',''), '%Y-%m-%d %H:%M:%S')
        if (dt.now() - notif_time).total_seconds() <= 300:
            # TODO Add channel id based on game
            run = requests.get(notification["links"][0]["uri"]).json()
            if len(run.keys())==1:
                channel_id = channel_lookup[run['data']['game']]
                print(f"New run validated for {run['data']['game']}")
                if DEV_MODE:
                    await post_run(1068245117544169545, run['data'], "Run Verified!")
                else:
                    await post_run(channel_id, run['data'], "Run Verified!")

# TODO Finish this
# Link SRC account to a Discord account
@bot.command(name="src", help="Set your SRC account")
async def src(ctx, *args):
    if len(args) != 1:
        await ctx.send("Please provide your SRC account name")
        return
    account = args[0]
    user = requests.get(f"{base_url}users/{account}").json()
    if len(user.keys()) == 1:
        # TODO Save to database
        await validate_user(ctx.author.id, account)
    else:
        await ctx.send(f"Could not find account {account}")

# TODO Ideas
#
# Auto assign roles to people who get their runs verified. Would mean people would have to 
# manually link their SRC accounts, but that can be done when people join the server
# 
# Giving the now streaming role when someone in the server streams a TICO game. Could be a role
# to opt in to this feature, so I dont have to be checking everyone in the world
#
# Command that gives all the positions people have in all 3 games and CE

if DEV_MODE:
    bot.run(TEST_TOKEN)
else:
    bot.run(TOKEN)