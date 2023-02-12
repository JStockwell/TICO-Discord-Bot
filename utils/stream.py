import os

from dotenv import load_dotenv
from discord.ext import tasks
from tinydb import TinyDB, Query

from utils.messages import post

load_dotenv()
TINYDB_PATH = os.getenv('TINYDB_PATH')
db = TinyDB(TINYDB_PATH)

@tasks.loop(seconds=10)
async def post_stream():
    var = 10

async def gen_streamer_list(bot):
    streamer_table = db.table('streamers')

    guild = await bot.fetch_guild(155844173591740416)

    async for member in guild.fetch_members(limit=None):
        if member.get_role(1074369332777337023) is not None:
            streamer_table.insert({'id': member.id, 'name': member.name})

    post("Streamer list generated successfully!", False)