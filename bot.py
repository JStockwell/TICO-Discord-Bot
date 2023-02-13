# Created by JStockwell on GitHub
import os
import discord
import requests
import json
import datetime
import Paginator

from utils.help import help_command
from utils.roles import base_reactions, handle_reaction
from utils.runs import get_wr_ce, get_wr_standard, post_run
from utils.game_gen import gen_db
from utils.stream import gen_streamer_list, post_stream_msg
from utils.messages import post

from dotenv import load_dotenv
from discord.ext import commands, tasks
from datetime import datetime as dt
from tinydb import TinyDB

### --- REST api Initialization --- ###

base_url = "https://www.speedrun.com/api/v1/"
games_path = "json/games.json"

### --- Bot Initialization --- ###

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEST_TOKEN = os.getenv('TEST_TOKEN')
SRCOM_TOKEN = os.getenv('SRCOM_TOKEN')
TWITCH_TOKEN = os.getenv('TWITCH_TOKEN')
TWITCH_CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')
TINYDB_PATH = os.getenv('TINYDB_PATH')
db = TinyDB(TINYDB_PATH)

DEV_MODE = os.getenv('DEV_MODE') == 'True'
GEN_DB_FLAG = False

GEN_DB_LAMBDA = not DEV_MODE or (DEV_MODE and GEN_DB_FLAG)

bot = commands.Bot(command_prefix='!', intents=discord.Intents().all())
bot.remove_command('help')

if GEN_DB_LAMBDA:
    gen_db(games_path)
game_db = json.load(open(games_path, 'r'))

streams_list = []

### --- Functions --- ###

@bot.event
async def on_ready():
    post(f'{bot.user.name} has connected to Discord!', False)

    if GEN_DB_LAMBDA:
        await gen_streamer_list(bot)

    await base_reactions(bot)

    reset_streams_list.start()
    post("Started streams list loop", False)
    post_stream.start()
    post("Started post stream loop", False)

    post_verification.start()
    post("Started post verification loop", False)

    post("Init process complete!", False)

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

    post(error, True)
    await ctx.send(message)

@bot.event
async def on_raw_reaction_add(payload):
    await handle_reaction(payload, bot, False)

@bot.event
async def on_raw_reaction_remove(payload):
    await handle_reaction(payload, bot, True)

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
            await help_command(ctx, bot_command)

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
                post(f"New run validated for {run['data']['game']}", False)
                if DEV_MODE:
                    await post_run(bot,1068245117544169545, run['data'], "Run Verified!")
                else:
                    await post_run(bot,channel_id, run['data'], "Run Verified!")

@tasks.loop(seconds=180) # 3 minutes
async def post_stream():
    streamer_table = db.table('streamers')
    guild = bot.get_guild(155844173591740416)

    for streamer in streamer_table.all():
        member = guild.get_member(streamer['id'])
        stream_flag = False

        for act in member.activities:
            if isinstance(act, discord.Streaming): # Making sure it's the correct activity
                headers = {'Authorization': f'Bearer {TWITCH_TOKEN}', 'Client-Id': TWITCH_CLIENT_ID}
                user_login = act.url.split('/')[-1]
                stream = requests.get(f'https://api.twitch.tv/helix/streams?user_login={user_login}', headers=headers).json()['data'][0]

                for game in game_db:
                    if stream['game_id'] == game_db[game]['twitch']:
                        stream_flag = True
                        await post_stream_msg(bot, stream, streams_list)

        role = discord.utils.get(guild.roles, name="NOW STREAMING!")
        if stream_flag:
            await member.add_roles(role)

        else:
            await member.remove_roles(role)

@tasks.loop(seconds=21600) # 6 hours
async def reset_streams_list():
    streams_list.clear()
    post("Streams list reset", False)


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