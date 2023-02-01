import os
import discord
import requests
import json
import datetime
import Paginator

from dotenv import load_dotenv
from discord.ext import commands, tasks
from datetime import datetime as dt
from tinydb import TinyDB, Query

### --- REST api Initialization --- ###

base_url = "https://www.speedrun.com/api/v1/"

### --- Bot Initialization --- ###

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TEST_TOKEN = os.getenv('TEST_TOKEN')
SRCOM_TOKEN = os.getenv('SRCOM_TOKEN')
TINYDB_PATH = os.getenv('TINYDB_PATH')
DEV_MODE = True

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
bot.remove_command('help')
# TODO Automate game_db creation
game_db = json.load(open('games.json', 'r'))
db = TinyDB(TINYDB_PATH)

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
    message = " "

    if DEV_MODE:
        message += f'\n{error}'
    else:
        message += f'An error has occurred, please try again!'

    print(error)
    await ctx.send(message)

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
            match bot_command.name:
                case "wr":
                    await help_wr(ctx, command.help)
                case "hello":
                    embed = discord.Embed(title=f"Hello: {command.help}", color=0x00ff00)
                    embed.add_field(name="", value="Why do you need help with a simple hello? :(", inline=False)
                    await ctx.send(embed=embed)
                case "beginnerhelp":
                    embed = discord.Embed(title=f"Beginnerhelp: {command.help}", color=0x00ff00)
                    embed.add_field(name="", value="I am in your walls.", inline=False)
                    await ctx.send(embed=embed)
                case "socials":
                    embed = discord.Embed(title=f"Socials: {command.help}", color=0x00ff00)
                    embed.add_field(name="", value="Don't forget to follow!", inline=False)
                    await ctx.send(embed=embed)

### --- Help --- ###
async def help_wr(ctx, help):
    embed1 = help_wr_embed()

    ico = "```• Any%\n  • Version:\n    • 60hz\n    • 50hz\n    • ntsc-u\n"
    ico += "• Co-Op\n  • Version:\n    • 60hz\n    • 50hz\n"
    ico += "• Enlightenment```"
    embed1.add_field(name="Ico", value=ico, inline=False)

    sotc = "```• Any%\n  • Version:\n   • PS2\n    • PS3\n  • Difficulty:\n    • Normal\n    • Hard\n"
    sotc += "• Boss_Rush\n  • Version:\n    • PS2\n    • PS3\n  • Difficulty:\n    • NTA\n    • HTA\n"
    sotc += "• Queens_Sword```"
    embed1.add_field(name="Shadow of the Colossus", value=sotc, inline=False)

    embed2 = help_wr_embed()
    sotc2018 = "```• Any%\n  • Difficulty:\n    • Easy\n    • Normal\n    • Hard\n"
    sotc2018 += "• Boss_Rush\n  • Difficulty:\n    • NTA\n    • HTA\n"
    sotc2018 += "• NG+\n  • Sub-Category:\n    • Any%\n    • All_Glints\n  • Item Menu Glitch\n    • No_IMG\n    • IMG\n"
    sotc2018 += "• Platinum\n• 100%```"
    embed2.add_field(name="Shadow of the Colossus (2018)", value=sotc2018, inline=False)

    tlg = "```• Any%\n• All_Barrels\n• Platinum```"
    embed2.add_field(name="The Last Guardian", value=tlg, inline=False)

    await Paginator.Simple().start(ctx, pages=[embed1, embed2])

def help_wr_embed():
    embed = discord.Embed(title=f"WR: {help}", color=0x00ff00)
    embed.add_field(name="Format", value="`!wr <game> <category> <var_1> <var_2>...`", inline=False)
    embed.add_field(name="Example", value="`!wr ico co-op 60hz`", inline=False)

    embed.add_field(name="Games", value="`ico, sotc, sotc(2018), tlg, ce`", inline=False)
    embed.add_field(name="__Categories For Each Game__", value="", inline=False)

    return embed

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

    game = game_db["data"][game_name]

    url = f"{base_url}leaderboards/{game['id']}/category/{game['fg'][category]['id']}?top=1&embed=players"
    i = 0
    for v in var:
        url += f"&var-{game['fg'][category]['variables'][i]['var_id']}={game['fg'][category]['variables'][i]['values'][v]}"
        i += 1
    wr = requests.get(url, headers={"X-API-Key": SRCOM_TOKEN}).json()["data"]

    if len(wr['runs']) > 0:
        run = requests.get(f"{base_url}runs/{wr['runs'][0]['run']['id']}").json()["data"]
        await post_run(ctx.message.channel.id, run, "World Record")

    else:
        await ctx.send("No world record found")

async def post_run(channel_id, run, title):
    game = requests.get(f"{base_url}games/{run['game']}").json()["data"]
    # TODO Add IL/Category check
    category = requests.get(f"{base_url}categories/{run['category']}").json()["data"]

    var_names=[]
    url_variables = ""
    for var in run["values"]:
        # Preparing the variable for visualization
        variables = requests.get(f"{base_url}variables/{var}").json()["data"]
        name = variables["name"]
        name += ": " + variables["values"]["values"][run["values"][var]]["label"]
        var_names.append(name)

        # Building the url for the leaderboard filtering to improve performance
        url_variables += f"&var-{variables['id']}={run['values'][var]}"

    leaderboard = requests.get(f"{base_url}leaderboards/{game['id']}/category/{category['id']}?max=100{url_variables}").json()
    place = "Not found"
    if len(leaderboard) == 1:
        dleaderboard = leaderboard["data"]
        for lrun in dleaderboard["runs"]:
            if lrun["run"]["id"] == run["id"]:
                place = lrun["place"]
                break

    embed = discord.Embed(title=title, color=discord.Color.random())
    embed.add_field(name='Game', value=game['names']['international'], inline=True)
    embed.add_field(name='Position', value=place, inline=True)
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

    embed.add_field(name="Link", value=run['weblink'], inline=False)

    channel = bot.get_channel(channel_id)
    await channel.send(embed=embed)

# Change to your desired channels
channel_lookup = {
    "o1yrkr6q": 155845329957158912,
    "9j1l8v6g": 155844832185548800,
    "y6545p8d": 155844832185548800,
    "j1nvyx6p": 155845509146345473
}

@tasks.loop(seconds = 300) # repeat after every five minutes
async def post_verification():
    notifications = requests.get(f"{base_url}notifications", headers={"X-API-Key": SRCOM_TOKEN}).json()["data"]
    for notification in notifications:
        notif_time = dt.strptime(notification['created'].replace('T',' ').replace('Z',''), '%Y-%m-%d %H:%M:%S')
        if (dt.now() - notif_time).total_seconds() <= 300:
            # TODO Add channel id based on game
            run = requests.get(notification["links"][0]["uri"]).json()
            if len(run.keys())==1:
                channel_id = channel_lookup[run['data']['game']]
                print(f"New run validated for {run['data']['game']}")
                runner_role(run['data']['players'])
                if DEV_MODE:
                    await post_run(1068245117544169545, run['data'], "Run Verified!")
                else:
                    await post_run(channel_id, run['data'], "Run Verified!")

def runner_role(players):
    for player in players:
        if player["rel"]=="user":
            table = db.table('users')
            user = table.search(Query().src == player["id"])

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
        table = db.table('users')
        user = table.search(Query().discord == ctx.author.id)
        if len(user) == 0:
            table.insert({'discord': ctx.author.id, 'src': account})
        else:
            table.update({'src': account}, Query().discord == ctx.author.id)

        print(db)
        await ctx.send(f"Your SRC account has been set to {account}")
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
#
# Notification every time a run gets validated

if DEV_MODE:
    bot.run(TEST_TOKEN)
else:
    bot.run(TOKEN)