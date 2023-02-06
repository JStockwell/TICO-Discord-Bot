import Paginator
import discord

class switch(object):
    value = None
    def __new__(class_, value):
        class_.value = value
        return True

def case(*args):
    return any((arg == switch.value for arg in args))

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
    embed1 = help_wr_embed(help)

    ico = "```• Any%\n  • Version:\n    • 60hz\n    • 50hz\n    • ntsc-u\n"
    ico += "• Co-Op\n  • Version:\n    • 60hz\n    • 50hz\n"
    ico += "• Enlightenment```"
    embed1.add_field(name="Ico", value=ico, inline=False)

    sotc = "```• Any%\n  • Version:\n   • PS2\n    • PS3\n  • Difficulty:\n    • Normal\n    • Hard\n"
    sotc += "• Boss_Rush\n  • Version:\n    • PS2\n    • PS3\n  • Difficulty:\n    • NTA\n    • HTA\n"
    sotc += "• Queens_Sword```"
    embed1.add_field(name="Shadow of the Colossus", value=sotc, inline=False)

    embed2 = help_wr_embed(help)
    sotc2018 = "```• Any%\n  • Difficulty:\n    • Easy\n    • Normal\n    • Hard\n"
    sotc2018 += "• Boss_Rush\n  • Difficulty:\n    • NTA\n    • HTA\n"
    sotc2018 += "• NG+\n  • Sub-Category:\n    • Any%\n    • All_Glints\n  • Item Menu Glitch\n    • No_IMG\n    • IMG\n"
    sotc2018 += "• Platinum\n• 100%```"
    embed2.add_field(name="Shadow of the Colossus (2018)", value=sotc2018, inline=False)

    tlg = "```• Any%\n• All_Barrels\n• Platinum```"
    embed2.add_field(name="The Last Guardian", value=tlg, inline=False)

    await Paginator.Simple().start(ctx, pages=[embed1, embed2])

def help_wr_embed(help):
    embed = discord.Embed(title=f"WR: {help}", color=0x00ff00)
    embed.add_field(name="Format", value="`!wr <game> <category> <var_1> <var_2>...`", inline=False)
    embed.add_field(name="Example", value="`!wr ico co-op 60hz`", inline=False)

    embed.add_field(name="Games", value="`ico, sotc, sotc(2018), tlg, ce`", inline=False)
    embed.add_field(name="__Categories For Each Game__", value="", inline=False)

    return embed