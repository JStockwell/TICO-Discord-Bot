# Created by JStockwell on GitHub
import Paginator
import discord
import json

from utils.switch import switch, case

async def help_command(ctx, command):
    while switch(command.name):
        if case("wr"):
            await help_wr(ctx, command.help)
            break
        if case("hello"):
            await generic_help(ctx, command, "Hello", ["Why do you need help with a simple hello? :("])
            break
        if case("beginnerhelp"):
            await generic_help(ctx, command, "Beginnerhelp", ["I am in your walls."])
            break
        if case("socials"):
            await generic_help(ctx, command, "Socials", ["Don't forget to follow!"])
            break
        if case("src"):
            await generic_help(ctx, command, "SRC", ["Links your Discord to your SRC account (WIP!)", "Format: !src <SRC Account Name>"])
            break
        await ctx.send("Command not found")

async def generic_help(ctx, command, title, description):
    embed = discord.Embed(title=f"{title}: {command.help}", color=0x00ff00)
    for field in description:
        embed.add_field(name="", value=field, inline=False)
    await ctx.send(embed=embed)

async def help_wr(ctx, help):
    help_db = json.load(open("json/help.json", 'r'))
    embeds = []

    # TODO Enable CE
    for game in help_db:
        embed = help_wr_embed(help)
        embed.add_field(name=game, value=help_db[game], inline=False)
        embeds.append(embed)

    await Paginator.Simple().start(ctx, pages=embeds)

def help_wr_embed(help):
    embed = discord.Embed(title=f"WR: {help}", color=0x00ff00)
    embed.add_field(name="Format", value="`!wr <game> <category> <var_1> <var_2>...`", inline=False)
    embed.add_field(name="Example", value="`!wr ico co-op 60hz`", inline=False)

    embed.add_field(name="Games", value="`ico, sotc, sotc(2018), tlg, ce`", inline=False)
    embed.add_field(name="__Categories For Each Game__", value="", inline=False)

    return embed