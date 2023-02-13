import os
import discord

from dotenv import load_dotenv
from discord.ext import tasks
from tinydb import TinyDB, Query

from utils.messages import post

load_dotenv()
TINYDB_PATH = os.getenv('TINYDB_PATH')
DEV_MODE = os.getenv('DEV_MODE') == 'True'
db = TinyDB(TINYDB_PATH)

async def gen_streamer_list(bot):
    streamer_table = db.table('streamers')
    guild = await bot.fetch_guild(155844173591740416)
    async for member in guild.fetch_members(limit=None):
        if member.get_role(1074369332777337023) is not None:
            if len(streamer_table.search(Query()["id"] == member.id)) == 0:
                streamer_table.insert({'id': member.id, 'name': member.name})
        else:
            if len(streamer_table.search(Query()["id"] == member.id)) != 0:
                streamer_table.remove(Query()["id"] == member.id)

    post("Streamer list generated successfully!", False)

async def post_stream_msg(bot, stream, streams_list):
    # Test channel
    if DEV_MODE:
        channel =  bot.get_channel(1068245117544169545)
    else:
        channel =  bot.get_channel(539498046325784576)

    if stream["user_login"] not in streams_list:
        streams_list.append(stream["user_login"])
        
        message = f'__**{stream["title"]}**__\n'
        message += f'Playing: **{stream["game_name"]}**\n'
        message += f'https://twitch.tv/{stream["user_login"]}'

        await channel.send(message)