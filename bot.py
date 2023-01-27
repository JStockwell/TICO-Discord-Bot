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
TEST_TOKEN = os.getenv('TEST_TOKEN')
SRCOM_TOKEN = os.getenv('SRCOM_TOKEN')
DEV_MODE = True

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

async def post_run(ctx,game,var,category,run):
    embed = discord.Embed(title='World Record', color=discord.Color.random())
    embed.add_field(name='Game', value=game['name'], inline=False)
    embed.add_field(name='Category', value=game['full-game-categories'][category]['name'], inline=False)
    # Check for variables
    variable_text = ""
    i = 0
    for v in var:
        variable_text += f"{game['full-game-categories'][category]['variables'][i]['values'][v]['name']}, "
        i += 1
    if variable_text != "":
        embed.add_field(name='Variable/s', value=variable_text[:-2], inline=False)
    # Check for Private User
    if run['data']['runs'][0]['run']['players'][0]['rel'] == 'guest':
        embed.add_field(name='Runner', value=run['data']['runs'][0]['run']['players'][0]['name'], inline=False)
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

    await ctx.send(embed=embed)

if DEV_MODE:
    bot.run(TEST_TOKEN)
else:
    bot.run(TOKEN)