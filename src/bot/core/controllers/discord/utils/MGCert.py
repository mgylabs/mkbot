import json
import logging
from functools import wraps

import discord
from discord.ext import commands
from mgylabs.utils.config import CONFIG, USER_DATA_PATH

from .MsgFormat import MsgFormatter

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(levelname)s :: %(asctime)s :: %(message)s", "%Y-%m-%d %H:%M:%S"
)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
file_handler = logging.FileHandler(
    USER_DATA_PATH + "/MK Bot.log", mode="a", encoding="utf-8"
)
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
        ALL_USERS = "all users"  # 3
        TRUSTED_USERS = "trusted users"  # 2
        ADMIN_USERS = "admin users"  # 1


class MGCertificate:
    admin_users = []
    trusted_users = []

    def __init__(self, name):
        with open(name, "rt") as f:
            data = json.load(f)
        MGCertificate.admin_users: list = data.get("adminUsers", [])
        MGCertificate.trusted_users: list = data.get("trustedUsers", [])

    @staticmethod
    def isTrustedUser(username):
        return MGCertificate.getUserLevel(username) == Level.TRUSTED_USERS

    @staticmethod
    def isAdminUser(username):
        return MGCertificate.getUserLevel(username) == Level.ADMIN_USERS

    @staticmethod
    def isCertUser(username):
        return MGCertificate.getUserLevel(username) < 3

    @staticmethod
    def getUserLevel(username):
        if username in MGCertificate.admin_users:
            return Level.ADMIN_USERS
        elif len(MGCertificate.trusted_users) == 0:
            return Level.TRUSTED_USERS
        elif username in MGCertificate.trusted_users:
            return Level.TRUSTED_USERS
        else:
            return Level.ALL_USERS

    @staticmethod
    def bind(func, level=Level.TRUSTED_USERS, name=None, cls=None, **attrs):
        return commands.command(name, cls, **attrs)(MGCertificate.verify(level)(func))

    @staticmethod
    def verify(level=Level.TRUSTED_USERS):
        def deco(func):
            if func.__doc__ != None:
                func.__doc__ = func.__doc__.format(commandPrefix=CONFIG.commandPrefix)

            @wraps(func)
            async def outerfunc(*args, **kwargs):
                if isinstance(args[0], commands.Context) or isinstance(
                    args[0], discord.Interaction
                ):
                    ctx: commands.Context = args[0]
                else:
                    ctx: commands.Context = args[1]

                req_user = str(ctx.author)
                perm = MGCertificate.getUserLevel(req_user)

                if perm > level:
                    embed = MsgFormatter.get(
                        ctx,
                        "Permission denied",
                        "<@{}> is not in the {}. This incident will be reported.".format(
                            ctx.author.id, Level.get_description(level)
                        ),
                        show_req_user=False,
                    )
                    embed.add_field(name="User", value=str(ctx.author))
                    embed.add_field(
                        name="Command tried",
                        value="{} ({})".format(
                            ctx.command.name, Level.get_description(level)
                        ),
                    )
                    await ctx.send(embed=embed)
                    logger.critical(
                        '"{}" tried to command "{}" that needs "{}" permission.'.format(
                            req_user, ctx.command.name, Level.get_description(level)
                        )
                    )
                    return

                return await func(*args, **kwargs)

            return outerfunc

        return deco
