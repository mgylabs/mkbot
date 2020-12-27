import hashlib
import logging
import msvcrt  # pylint: disable=import-error
import os
import re
import sys
import time
import traceback

import discord
from discord.ext import commands

from command_help import CommandHelp
from core.utils import api
from core.utils.config import CONFIG, MGCERT_PATH, VERSION, is_development_mode
from core.utils.MGCert import MGCertificate
from core.utils.MsgFormat import MsgFormatter
from core_ext import core_extensions
from release import ReleaseNotify

stime = time.time()
os.chdir(os.path.dirname(os.path.abspath(__file__)))
log = logging.getLogger(__name__)
errorlevel = 0
pending = True

replyformat = MsgFormatter()
bot = commands.Bot(command_prefix=CONFIG.commandPrefix,
                   help_command=CommandHelp(replyformat))
cert = MGCertificate(MGCERT_PATH)
bot.__dict__.update({'MGCert': cert, 'replyformat': replyformat})


def instance_already_running():
    key = hashlib.sha1(CONFIG.discordToken.encode()).hexdigest()[:8]

    fd = os.open(f"{os.getenv('TEMP')}\\mkbot_{key}.lock",
                 os.O_WRONLY | os.O_CREAT)

    try:
        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        already_running = False
    except IOError:
        already_running = True

    return already_running


@bot.event
async def on_ready():
    print('Logged in within', time.time() - stime)
    replyformat.set_avatar_url(bot.user.avatar_url)
    if is_development_mode():
        name = "IN DEBUG" if '--debug' in sys.argv else "IN DEV"
        activity_type = discord.ActivityType.playing
    elif VERSION == None:
        name = "MK Bot Test Mode"
        activity_type = discord.ActivityType.playing
    else:
        name = f"{bot.command_prefix}help"
        activity_type = discord.ActivityType.listening
    activity = discord.Activity(name=name, type=activity_type)
    await bot.change_presence(status=discord.Status.online, activity=activity)
    if not is_development_mode():
        await ReleaseNotify.run(bot)


@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return

    if (message.channel.type.value == 1) and (CONFIG.disabledPrivateChannel):
        return

    if bot.user.mentioned_in(message) and cert.isAdminUser(str(message.author)):
        text = re.sub('<@!?\\d+> ', '', message.content)
        if text.lower() == 'ping':
            await message.channel.send(f"{message.author.mention}  Pong: {round(bot.latency*1000)}ms")
    else:
        await bot.process_commands(message)
        global pending
        if pending and message.content.startswith(bot.command_prefix):
            pending = False
            name = f"MK Bot {VERSION}"
            activity = discord.Activity(
                name=name, type=discord.ActivityType.listening)
            await bot.change_presence(
                status=discord.Status.online, activity=activity)
            if not is_development_mode():
                await ReleaseNotify.run(message.channel)


@bot.event
async def on_command_error(ctx, error: commands.CommandError):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.CommandInvokeError):
        await ctx.send(str(error))
        raise error
    await ctx.send(embed=MsgFormatter.get(ctx, error.__class__.__name__, str(error)))


for i in core_extensions:
    try:
        bot.load_extension(i)
    except Exception:
        traceback.print_exc()
        if i != "core.install":
            errorlevel += 1

try:
    exts = api.get_enabled_extensions()
    for i in exts:
        if is_development_mode():
            sys.path.append(f'..\\..\\extensions\\{i[0]}')
        else:
            sys.path.append(os.getenv('USERPROFILE') +
                            f'\\.mkbot\\extensions\\{i[0]}')
        bot.load_extension(i[1])
except Exception:
    traceback.print_exc()

print('Mulgyeol MK Bot')
print(f'Version {VERSION}' if VERSION != None else 'Test Mode')
print('Copyright (c) 2020 Mulgyeol Labs. All rights reserved.\n')

if instance_already_running():
    print('The discord token provided is already in use by MK Bot.')
    sys.exit(0)

if '--dry-run' in sys.argv:
    print("Test succeeded")
    sys.exit(errorlevel)
else:
    try:
        bot.run(CONFIG.discordToken)
    except discord.errors.LoginFailure as e:
        log.critical(e)
        sys.exit(1)
