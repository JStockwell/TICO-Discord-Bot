import os
import discord
import requests
import asyncio
import json
import datetime

from dotenv import load_dotenv
from discord.ext import commands, tasks
from datetime import datetime as dt

### --- REST api Initialization --- ###

base_url = "https://www.speedrun.com/api/v1/"

### --- Bot Initialization --- ###

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEST_TOKEN = os.getenv('TEST_TOKEN')
SRCOM_TOKEN = os.getenv('SRCOM_TOKEN')
DEV_MODE = True

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
# TODO Automate game_db creation
game_db = json.load(open('games.json', 'r'))

### --- Functions --- ###

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    post_verification.start()

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

@bot.command(name="beginnerhelp", help="Document with all relevant information for beginners")
async def beginner_help(ctx):
    await ctx.send("https://docs.google.com/document/d/1n9hQe9EZO59_sURBwirt9CwpzmBoge_8OWe21w6dZMA/edit?usp=sharing")

@bot.command(name="socials", help="Link to the TICO Speedruns socials")
async def socials(ctx):
    message = "Follow us at!\n"
    message += "Youtube: https://www.youtube.com/channel/UCMLlkQ8CFV8BqXFz86usFeQ\n"
    message += "Twitch: https://www.twitch.tv/teamicospeedruns\n"
    message += "Twitter: https://twitter.com/IcoSpeedruns\n"
    await ctx.send(message)

# Format: !wr <game> <category> <var_1> <var_2>
# Example: !wr ico co-op 60hz
# TODO Add info for people to actually use this lmao
@bot.command(name="wr", help="Get the world record for a category")
async def get_wr(ctx):
    var = []
    i = 1
    while i < len(ctx.message.content.split(" ")):
        # Get the game id
        if i == 1:
            game_name = ctx.message.content.split(" ")[i]
        # Get the category id
        elif i == 2:
            category = ctx.message.content.split(" ")[i]
        # Get the category variables
        else:
            var.append(ctx.message.content.split(" ")[i])
        i += 1

    game = game_db["data"][game_name]

    url = f"{base_url}leaderboards/{game['id']}/category/{game['fg'][category]['id']}?top=1&embed=players"
    i = 0
    for v in var:
        url += f"&var-{game['fg'][category]['variables'][i]['var_id']}={game['fg'][category]['variables'][i]['values'][v]}"
        i += 1
    wr = requests.get(url, headers={"X-API-Key": SRCOM_TOKEN}).json()["data"]

    if len(wr['runs']) > 0:
        await post_run(ctx.message.channel.id, f"{base_url}runs/{wr['runs'][0]['run']['id']}", "World Record")

    else:
        await ctx.send("No world record found")

async def post_run(channel_id, url, title):
    run = requests.get(url).json()["data"]
    game = requests.get(f"{base_url}games/{run['game']}").json()["data"]
    # TODO Add IL/Category check
    category = requests.get(f"{base_url}categories/{run['category']}").json()["data"]

    var_names=[]
    for var in run["values"]:
        variables = requests.get(f"{base_url}variables/{var}").json()["data"]
        name = variables["name"]
        name += ": " + variables["values"]["values"][run["values"][var]]["label"]
        var_names.append(name)

    embed = discord.Embed(title=title, color=discord.Color.random())
    embed.add_field(name='Game', value=game['names']['international'], inline=False)
    embed.add_field(name='Category', value=category['name'], inline=False)
    # Check for variables
    if len(var_names) > 0:
        embed.add_field(name='Variable/s', value=", ".join(var_names), inline=False)

    players = []
    for player in run['players']:
        if player['rel'] == 'guest':
            players.append(player['name'])
        else:
            players.append(requests.get(f"{base_url}users/{player['id']}").json()['data']['names']['international'])
    embed.add_field(name='Runner/s', value=", ".join(players), inline=False)

    primary = run['times']['primary_t']
    realtime = run['times']['realtime_t']
    primary_time = str(datetime.timedelta(seconds=primary))

    if primary_time[-4:] == "0000":
        embed.add_field(name='Time', value=primary_time[:-4], inline=True)
    else:
        embed.add_field(name='Time', value=primary_time, inline=True)

    if realtime != run['times']['primary_t']:
        embed.add_field(name='Realtime', value=datetime.timedelta(seconds=realtime), inline=True)

    channel = bot.get_channel(channel_id)
    await channel.send(embed=embed)

@tasks.loop(seconds = 60) # repeat after every minute
async def post_verification():
    notifications = requests.get(f"{base_url}notifications", headers={"X-API-Key": SRCOM_TOKEN}).json()["data"]
    
    for notification in notifications:
        notif_time = dt.strptime(notification['created'].replace('T',' ').replace('Z',''), '%Y-%m-%d %H:%M:%S')
        # result 0:32:51.212777
        if (dt.now() - notif_time).total_seconds() < 60:
            # TODO Add channel id based on game
            channel_id = 0
            await post_run(channel_id, notification["links"][0]["uri"], "Run Verified")

        
# TODO Ideas
#
# Auto assign roles to people who get their runs verified. Would mean people would have to 
# manually link their SRC accounts, but that can be done when people join the server
# 
# Giving the now streaming role when someone in the server streams a TICO game. Could be a role
# to opt in to this feature, so I dont have to be checking everyone in the world
#
# Command that gives all the positions people have in all 3 games and CE
#
# Notification every time a run gets validated

if DEV_MODE:
    bot.run(TEST_TOKEN)
else:
    bot.run(TOKEN)