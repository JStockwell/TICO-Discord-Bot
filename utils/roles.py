import sys
import os

DEV_MODE = os.getenv('DEV_MODE') == 'True'
sys.path.append("../TICO-DISCORD-BOT")

async def handle_reaction(payload, bot, remove):
    message_id = payload.message_id
    emoji_id = payload.emoji.id
    emoji = payload.emoji.name
    guild = bot.get_guild(payload.guild_id)
    user = guild.get_member(payload.user_id)

    custom_payload = [message_id, emoji_id, emoji, user, guild, remove]

    if DEV_MODE:
        # Standard !
        await modify_role(custom_payload, bot, 1071148440895115314, "❗", "Standard Test")
        # Custom OK
        await modify_role(custom_payload, bot, 1071148440895115314, 822869417930653709, "Custom Test")

    # TODO Add these functions
    # Alert
    await modify_role(custom_payload, bot, 929064886300971078, "❗", "Alert")
    # Pronouns
    await pronouns_modify_role(custom_payload, bot)
    await modify_role(custom_payload, bot, 929065214761123840, "👍", "Member")

# custom_payload = [message_id, emoji_id, emoji, user, guild, remove, user]
async def modify_role(payload, bot, target_message_id, target_emoji, role_name):
    if payload[0] == target_message_id and (payload[1] == target_emoji or payload[2] == target_emoji) and payload[3] != bot.user:
        print("hello")
        await exe_modify_role(payload[3], payload[4], payload[5], role_name)

async def pronouns_modify_role(payload, bot):
    # She/Her, He/Him, They/Them
    emojis = [937812173596540978, 937812173672038420, 937811380512374874]
    if payload[0] == 929065103687573544 and (payload[1] in emojis) and payload[3] != bot.user:
        if payload[1] == emojis[0]:
            await exe_modify_role(payload[3], payload[4], payload[5], "she/her")
        elif payload[1] == emojis[1]:
            await exe_modify_role(payload[3], payload[4], payload[5], "he/him")
        else:
            await exe_modify_role(payload[3], payload[4], payload[5], "they/them")

async def exe_modify_role(user, guild, remove, role_name):
    role = discord.utils.get(guild.roles, name=role_name)
    if remove:
        await user.remove_roles(role)
    else:
        await user.add_roles(role)

async def base_reactions(bot):
    guild = bot.get_guild(155844173591740416)
    messages = []
    emotes = []

    if DEV_MODE:
        test_channel = bot.get_channel(1068245117544169545)
        for i in range(2):
            messages.append(await test_channel.fetch_message(1071148440895115314))
        emotes.append("❗")
        emotes.append(await guild.fetch_emoji(822869417930653709))

    guidelines = bot.get_channel(848973738190831697)

    # Alert
    messages.append(await guidelines.fetch_message(929064886300971078))
    emotes.append("❗")

    # Pronouns
    for i in range(3):
        messages.append(await guidelines.fetch_message(929065103687573544))
    emotes.append(await guild.fetch_emoji(937812173596540978))
    emotes.append(await guild.fetch_emoji(937812173672038420))
    emotes.append(await guild.fetch_emoji(937811380512374874))

    # Member
    messages.append(await guidelines.fetch_message(929065214761123840))
    emotes.append("👍")

    for i in range(len(messages)):
        await messages[i].add_reaction(emotes[i])
