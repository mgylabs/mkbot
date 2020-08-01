import asyncio
import discord
from discord.ext import commands
import requests
from core.utils.token import TOKEN
from MGCert import MGCertificate, Level
from MsgFormat import MsgFormatter
from core_ext import core_extensions
import sys
import os
import re
import api
import time

stime = time.time()
PREFIX = None


def get_prefix():
    global PREFIX
    if PREFIX == None:
        PREFIX = TOKEN.get('commandPrefix', '.')
    return PREFIX


client = commands.Bot(command_prefix=get_prefix())
cert = MGCertificate('../data/mgcert.json')
replyformat = MsgFormatter()
client.__dict__.update({'MGCert': cert, 'replyformat': replyformat})


@client.event
async def on_ready():
    print('Logged in within', time.time() - stime)
    global replyformat
    replyformat.set_avatar_url(client.user.avatar_url)
    activity = discord.Game(
        name=f"{get_prefix()}help로 도움말을 이용하세요", type=3)
    await client.change_presence(status=discord.Status.online, activity=activity)


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if (message.channel.type.value == 1) and (TOKEN.get('disabledPrivateChannel', False)):
        return

    if client.user.mentioned_in(message) and cert.isAdminUser(str(message.author)):
        text = re.sub('<@!?\d+> ', '', message.content)
        if text == 'ping':
            await message.channel.send(message.author.mention + ' pong')
    else:
        if TOKEN.get('__DEBUG_MODE__', False):
            for i in core_extensions:
                client.reload_extension(i)
        await client.process_commands(message)


for i in core_extensions:
    client.load_extension(i)

try:
    exts = api.get_enabled_extensions()
    if len(exts) > 0:
        if getattr(sys, 'frozen', False):
            sys.path.append(os.getenv('USERPROFILE') + '\\.mkbot')
        for i in exts:
            client.load_extension(i)
except Exception as e:
    print(e)


try:
    client.run(TOKEN['discordToken'])
except discord.errors.LoginFailure as e:
    print(e)
    sys.exit(1)
