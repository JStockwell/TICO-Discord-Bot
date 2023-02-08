# Created by JStockwell on GitHub
import requests
import discord
import datetime
import os

from datetime import datetime as dt

base_url = "https://www.speedrun.com/api/v1/"
SRCOM_TOKEN = os.getenv('SRCOM_TOKEN')

async def post_run(bot, channel_id, run, title):
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

async def get_wr_standard(bot, ctx, game, args):
    var = []
    category = args[1].lower()

    for arg in args[2:]:
        var.append(arg.lower())

    url = f"{base_url}leaderboards/{game['id']}/category/{game['categories']['fg'][category]['id']}?top=1&embed=players"
    i = 0
    for v in var:
        url += f"&var-{game['categories']['fg'][category]['variables'][i]['var_id']}={game['categories']['fg'][category]['variables'][i]['values'][v]}"
        i += 1
    wr = requests.get(url, headers={"X-API-Key": SRCOM_TOKEN}).json()["data"]

    if len(wr['runs']) > 0:
        run = requests.get(f"{base_url}runs/{wr['runs'][0]['run']['id']}").json()["data"]
        await post_run(bot, ctx.message.channel.id, run, "World Record")

    else:
        await ctx.send("No world record found")

game_list = ["ico", "sotc", "tlg"]
async def get_wr_ce(bot, ctx, game, args):
    game_name = args[0]

    if args[1].lower() in game_list:
        game_name += f" {args[1].lower()}"
        args = args[1:]

    game = game["categories"][game_name]

    var = []
    category = args[1].lower()

    for arg in args[2:]:
        var.append(arg.lower())

    url = f"{base_url}leaderboards/y6547l0d/category/{game['fg'][category]['id']}?top=1&embed=players"
    i = 0
    for v in var:
        url += f"&var-{game['fg'][category]['variables'][i]['var_id']}={game['fg'][category]['variables'][i]['values'][v]}"
        i += 1
    wr = requests.get(url, headers={"X-API-Key": SRCOM_TOKEN}).json()["data"]

    if len(wr['runs']) > 0:
        run = requests.get(f"{base_url}runs/{wr['runs'][0]['run']['id']}").json()["data"]
        await post_run(bot, ctx.message.channel.id, run, "World Record")

    else:
        await ctx.send("No world record found")