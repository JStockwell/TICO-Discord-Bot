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
    var_flag = False
    # Get the game id
    game_name = ctx.message.content.split(" ")[1]
    # Get the category id
    category = ctx.message.content.split(" ")[2]
    # Get the category variable 1
    if len(ctx.message.content.split(" ")) > 3:
        var = []
        i = 3
        while i < len(ctx.message.content.split(" ")):
            var.append(ctx.message.content.split(" ")[i])
            i += 1

        var_flag = True

    game = game_db["data"][game_name]

    if var_flag:
        url = f"{base_url}leaderboards/{game['id']}/category/{game['full-game-categories'][category]['id']}?top=1&embed=players"
        for v in var:   
            url += f"&var-{game['full-game-categories'][category]['var_id']}={game['full-game-categories'][category]['variables'][v]['id']}"
        wr = requests.get(url, headers={"X-API-Key": SRCOM_TOKEN}).json()
    else:
        wr = requests.get(f"{base_url}leaderboards/{game['id']}/category/{game['full-game-categories'][category]['id']}?top=1&embed=players", headers={"X-API-Key": SRCOM_TOKEN}).json()
    
    if len(wr['data']['runs']) > 0:
        # Create the embed
        embed = discord.Embed(title='World Record', color=discord.Color.random())
        embed.add_field(name='Game', value=game['name'], inline=True)
        embed.add_field(name='Category', value=game['full-game-categories'][category]['name'], inline=True)
        if var_flag:
            for v in var:
                embed.add_field(name='Variable', value=game['full-game-categories'][category]['variables'][v]['name'], inline=True)
        for player in wr['data']['runs'][0]['run']['players']:
            player_name = requests.get(f"{base_url}users/{player['id']}").json()['data']['names']['international']
            embed.add_field(name='Runner', value=player_name, inline=True)
        embed.add_field(name='Time', value=datetime.timedelta(seconds=wr['data']['runs'][0]['run']['times']['primary_t']), inline=False)

        await ctx.send(embed=embed)

    else:
        await ctx.send("No world record found")


bot.run(TOKEN)