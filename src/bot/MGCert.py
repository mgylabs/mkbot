import asyncio
import discord
from discord.ext import commands
from functools import wraps
import logging
import json
from MsgFormat import MsgFormatter
from core.utils.config import CONFIG

logger = logging.getLogger('Logger')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(levelname)s :: %(asctime)s :: %(message)s", "%Y-%m-%d %H:%M:%S")
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
file_handler = logging.FileHandler('MK Bot.log', mode='a', encoding='utf-8')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


class Level:
    ALL_USERS = 3
    TRUSTED_USERS = 2
    ADMIN_USERS = 1

    @staticmethod
    def get_description(num):
        if num == Level.ALL_USERS:
            return Level.Description.ALL_USERS
        elif num == Level.TRUSTED_USERS:
            return Level.Description.TRUSTED_USERS
        else:
            return Level.Description.ADMIN_USERS

    class Description:
        ALL_USERS = 'all users'  # 3
        TRUSTED_USERS = 'trusted users'  # 2
        ADMIN_USERS = 'admin users'  # 1


class MGCertificate:
    def __init__(self, name):
        with open(name, 'rt') as f:
            data = json.load(f)
        self.admin_users: list = data.get('adminUsers', [])
        self.trusted_users: list = data.get('trustedUsers', [])

    def isTrustedUser(self, username):
        return self.getUserLevel(username) == Level.TRUSTED_USERS

    def isAdminUser(self, username):
        return self.getUserLevel(username) == Level.ADMIN_USERS

    def isCertUser(self, username):
        return self.getUserLevel(username) < 3

    def getUserLevel(self, username):
        if username in self.admin_users:
            return Level.ADMIN_USERS
        elif len(self.trusted_users) == 0:
            return Level.TRUSTED_USERS
        elif username in self.trusted_users:
            return Level.TRUSTED_USERS
        else:
            return Level.ALL_USERS

    def bind(self, func, level=Level.TRUSTED_USERS, name=None, cls=None, **attrs):
        return commands.command(name, cls, **attrs)(self.verify(level)(func))

    def verify(self, level=Level.TRUSTED_USERS):
        def deco(func):
            if func.__doc__ != None:
                func.__doc__ = func.__doc__.format(
                    commandPrefix=CONFIG.commandPrefix)

            @wraps(func)
            async def outerfunc(*args, **kwargs):
                if isinstance(args[0], commands.context.Context):
                    ctx = args[0]
                else:
                    ctx = args[1]

                req_user = str(ctx.author)

                if self.getUserLevel(req_user) > level:
                    replyformat = MsgFormatter(ctx.me.avatar_url)
                    embed = replyformat.get(ctx, "Permission denied", '<@{}> is not in the {}. This incident will be reported.'.format(
                        ctx.author.id, Level.get_description(level)), False)
                    embed.add_field(name='User', value=str(ctx.author))
                    embed.add_field(name='Command tried', value='{} ({})'.format(
                        ctx.command.name, Level.get_description(level)))
                    await ctx.send(embed=embed)
                    logger.critical('"{}" tried to command "{}" that needs "{}" permission.'.format(
                        req_user, ctx.command.name, Level.get_description(level)))
                    raise Exception('Untrusted user')

                return await func(*args, **kwargs)
            return outerfunc
        return deco
