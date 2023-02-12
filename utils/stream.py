from discord.ext import tasks

@tasks.loop(seconds=10)
async def post_stream():
    print("Posting stream")