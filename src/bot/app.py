import asyncio
import discord
from discord.ext import commands
from core.utils.config import CONFIG, VERSION
from MGCert import MGCertificate
from MsgFormat import MsgFormatter
from core_ext import core_extensions
from command_help import CommandHelp
import sys
import os
import re
import core.utils.api
import time
import traceback

stime = time.time()
errorlevel = 0

replyformat = MsgFormatter()
client = commands.Bot(command_prefix=CONFIG.commandPrefix,
                      help_command=CommandHelp(replyformat))
cert = MGCertificate('../data/mgcert.json')
client.__dict__.update({'MGCert': cert, 'replyformat': replyformat})


def is_development_mode():
    return not getattr(sys, 'frozen', False)


@client.event
async def on_ready():
    print('Logged in within', time.time() - stime)
    replyformat.set_avatar_url(client.user.avatar_url)
    if is_development_mode():
        name = "IN DEBUG" if CONFIG.__DEBUG_MODE__ else "IN DEV"
        activity_type = discord.ActivityType.playing
    elif VERSION == None:
        name = "MK Bot Test Mode"
        activity_type = discord.ActivityType.playing
    else:
        name = f"MK Bot {VERSION} Stable"
        activity_type = discord.ActivityType.listening
    activity = discord.Activity(name=name, type=activity_type)
    await client.change_presence(status=discord.Status.online, activity=activity)


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if (message.channel.type.value == 1) and (CONFIG.disabledPrivateChannel):
        return

    if client.user.mentioned_in(message) and cert.isAdminUser(str(message.author)):
        text = re.sub('<@!?\d+> ', '', message.content)
        if text == 'ping':
            await message.channel.send(message.author.mention + ' pong')
    else:
        if CONFIG.__DEBUG_MODE__:
            for i in core_extensions:
                client.reload_extension(i)
        await client.process_commands(message)


for i in core_extensions:
    try:
        client.load_extension(i)
    except Exception as e:
        traceback.print_exc()
        errorlevel += 1

try:
    exts = core.utils.api.get_enabled_extensions()
    if len(exts) > 0:
        for i in exts:
            if is_development_mode():
                sys.path.append(f'..\\..\\extensions\\{i[0]}')
            else:
                sys.path.append(os.getenv('USERPROFILE') +
                                f'\\.mkbot\\extensions\\{i[0]}')
            client.load_extension(i[1])
except Exception as e:
    traceback.print_exc()


if '--dry-run' in sys.argv:
    sys.exit(errorlevel)
else:
    try:
        client.run(CONFIG.discordToken)
    except discord.errors.LoginFailure as e:
        print(e)
        sys.exit(1)
