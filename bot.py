# Created by: @jstockwell on GitHub
# GNU GENERAL PUBLIC LICENSE
# Version 3, 29 June 2007

# Copyright © 2007 Free Software Foundation, Inc. <https://fsf.org/>

# Everyone is permitted to copy and distribute verbatim copies of this license document, but changing it is not allowed.

# The GNU General Public License is a free, copyleft license for software and other kinds of works.

# The licenses for most software and other practical works are designed to take away your freedom to share and change the works. 
# By contrast, the GNU General Public License is intended to guarantee your freedom to share and change all versions of a program
# to make sure it remains free software for all its users. We, the Free Software Foundation, use the GNU General Public License for most of our software; 
# it applies also to any other work released this way by its authors. You can apply it to your programs, too.

# When we speak of free software, we are referring to freedom, not price. Our General Public Licenses are designed to make sure that you have the freedom 
# to distribute copies of free software (and charge for them if you wish), that you receive source code or can get it if you want it, that you can change 
# the software or use pieces of it in new free programs, and that you know you can do these things.

# To protect your rights, we need to prevent others from denying you these rights or asking you to surrender the rights. Therefore, you have certain 
# responsibilities if you distribute copies of the software, or if you modify it: responsibilities to respect the freedom of others.

# For example, if you distribute copies of such a program, whether gratis or for a fee, you must pass on to the recipients the same freedoms that you 
# received. You must make sure that they, too, receive or can get the source code. And you must show them these terms so they know their rights.

# Developers that use the GNU GPL protect your rights with two steps: (1) assert copyright on the software, and (2) offer you this License giving you 
# legal permission to copy, distribute and/or modify it.

# For the developers' and authors' protection, the GPL clearly explains that there is no warranty for this free software. For both users' 
# and authors' sake, the GPL requires that modified versions be marked as changed, so that their problems will not be attributed erroneously 
# to authors of previous versions.

# Some devices are designed to deny users access to install or run modified versions of the software inside them, although the manufacturer 
# can do so. This is fundamentally incompatible with the aim of protecting users' freedom to change the software. The systematic pattern of 
# such abuse occurs in the area of products for individuals to use, which is precisely where it is most unacceptable. Therefore, we have 
# designed this version of the GPL to prohibit the practice for those products. If such problems arise substantially in other domains, we 
# stand ready to extend this provision to those domains in future versions of the GPL, as needed to protect the freedom of users.

# Finally, every program is threatened constantly by software patents. States should not allow patents to restrict development and use of 
# software on general-purpose computers, but in those that do, we wish to avoid the special danger that patents applied to a free program 
# could make it effectively proprietary. To prevent this, the GPL assures that patents cannot be used to render the program non-free.

import os
import discord
import requests
import json
import datetime
import Paginator

import utils.help as Help
import utils.roles as Roles
import utils.runs as Runs
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

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
bot.remove_command('help')
# TODO Automate game_db creation

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
    var = []
    i = 0
    while i < len(args):
        # Get the game id
        if i == 0:
            game_name = args[i].lower()
        # Get the category id
        elif i == 1:
            category = args[i].lower()
        # Get the category variables
        else:
            var.append(args[i].lower())
        i += 1

    game = game_db[game_name]

    url = f"{base_url}leaderboards/{game['id']}/category/{game['categories']['fg'][category]['id']}?top=1&embed=players"
    i = 0
    for v in var:
        url += f"&var-{game['categories']['fg'][category]['variables'][i]['var_id']}={game['categories']['fg'][category]['variables'][i]['values'][v]}"
        i += 1
    wr = requests.get(url, headers={"X-API-Key": SRCOM_TOKEN}).json()["data"]

    if len(wr['runs']) > 0:
        run = requests.get(f"{base_url}runs/{wr['runs'][0]['run']['id']}").json()["data"]
        await Runs.post_run(bot, ctx.message.channel.id, run, "World Record")

    else:
        await ctx.send("No world record found")

@tasks.loop(seconds = 300) # repeat after every five minutes
async def post_verification():
    channel_lookup = json.load(open('utils/json/channels.json', 'r'))
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

async def validate_user(discord_id, account):
    table = db.table('src_validation')
    user = table.search(Query().discord == discord_id)
    if len(user) == 0:
        dm = await bot.get_user(discord_id).create_dm()
        await dm.send(f"Ligma balls {account}")

#table = db.table('users')
#    user = table.search(Query().discord == ctx.author.id)
#    if len(user) == 0:
#        table.insert({'discord': ctx.author.id, 'src': account})
#    else:
#        table.update({'src': account}, Query().discord == ctx.author.id)

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