import os
import discord
import requests
import asyncio
import json
import datetime

from dotenv import load_dotenv
from discord.ext import commands

### --- REST api Initialization --- ###

base_url = "https://www.speedrun.com/api/v1/"

### --- Bot Initialization --- ###

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
SRCOM_TOKEN = os.getenv('SRCOM_TOKEN')
TINYDB_PATH = os.getenv('TINYDB_PATH')
DEV_MODE = os.getenv('DEV_MODE') == 'True'
GEN_DB_FLAG = False

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
game_db = json.load(open('games.json', 'r'))

### --- Functions --- ###

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

@bot.event
async def on_error(event, *args, **kwargs):
    with open('err.log', 'a') as f:
        if event == 'on_message':
            f.write(f'Unhandled message: {args[0]}\n')
        else:
            raise ValueError(f'Unhandled event: {event}')

@bot.event
async def on_command_error(ctx, error):
    message = ""

    if DEV_MODE:
        message += f'\n{error}'

    print(error)
    await ctx.send(message)

### --- Commands --- ###

@bot.command(name="hello")
async def hello(ctx):
    await ctx.send("Hello!")

# Format: !wr <game> <category> <var_1> <var_2>
# Example: !wr ico co-op 60hz
@bot.command(name="wr", help="Get the world record for a category")
async def get_wr(ctx):
    var = []
    # Get the game id
    game_name = ctx.message.content.split(" ")[1]
    # Get the category id
    category = ctx.message.content.split(" ")[2]
    # Get the category variable 1
    if len(ctx.message.content.split(" ")) > 3:
        i = 3
        while i < len(ctx.message.content.split(" ")):
            var.append(ctx.message.content.split(" ")[i])
            i += 1

    game = game_db["data"][game_name]

    url = f"{base_url}leaderboards/{game['id']}/category/{game['full-game-categories'][category]['id']}?top=1&embed=players"
    i = 0
    for v in var:
        url += f"&var-{game['full-game-categories'][category]['variables'][i]['var_id']}={game['full-game-categories'][category]['variables'][i]['values'][v]['id']}"
        i += 1
    wr = requests.get(url, headers={"X-API-Key": SRCOM_TOKEN}).json()

    if len(wr['data']['runs']) > 0:
        await post_run(ctx,game,var,category,wr)

    else:
        await ctx.send("No world record found")

@tasks.loop(seconds = 300) # repeat after every five minutes
async def post_verification():
    channel_lookup = json.load(open('json/channels.json', 'r'))
    notifications = requests.get(f"{base_url}notifications", headers={"X-API-Key": SRCOM_TOKEN}).json()["data"]
    for notification in notifications:
        notif_time = dt.strptime(notification['created'].replace('T',' ').replace('Z',''), '%Y-%m-%d %H:%M:%S')
        if (dt.now() - notif_time).total_seconds() <= 300:
            run = requests.get(notification["links"][0]["uri"]).json()
            if len(run.keys())==1:
                channel_id = channel_lookup[run['data']['game']]
                print(f"New run validated for {run['data']['game']}")
                if DEV_MODE:
                    await post_run(1068245117544169545, run['data'], "Run Verified!")
                else:
                    await post_run(channel_id, run['data'], "Run Verified!")

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
        player_names = ""
        for player in run['data']['runs'][0]['run']['players']:
            player_names += requests.get(f"{base_url}users/{player['id']}").json()['data']['names']['international'] + ", "
        embed.add_field(name='Runner/s', value=player_names[:-2], inline=False)
    primary = run['data']['runs'][0]['run']['times']['primary_t']
    realtime = run['data']['runs'][0]['run']['times']['realtime_t']
    primary_time = str(datetime.timedelta(seconds=primary))
    if primary_time[-4:] == "0000":
        embed.add_field(name='Time', value=primary_time[:-4], inline=True)
    else:
        embed.add_field(name='Time', value=primary_time, inline=True)
    if realtime != run['data']['runs'][0]['run']['times']['primary_t']:
        embed.add_field(name='Realtime', value=datetime.timedelta(seconds=realtime), inline=True)

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
