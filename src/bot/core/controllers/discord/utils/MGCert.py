import json
import logging
from functools import wraps

import discord
from discord.ext import commands

from core.controllers.discord.utils.command_helper import send
from mgylabs.i18n import _
from mgylabs.utils.config import USER_DATA_PATH

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
            @wraps(func)
            async def outerfunc(*args, **kwargs):
                if isinstance(args[0], commands.Context) or isinstance(
                    args[0], discord.Interaction
                ):
                    ctx_or_iaction: commands.Context = args[0]
                else:
                    ctx_or_iaction: commands.Context = args[1]

                if isinstance(ctx_or_iaction, discord.Interaction):
                    bot = ctx_or_iaction.client
                    user = ctx_or_iaction.user
                else:
                    bot = ctx_or_iaction.bot
                    user = ctx_or_iaction.author

                req_user = str(user)
                req_user_id = user.id

                if await bot.is_owner(user):
                    perm = Level.ADMIN_USERS
                else:
                    perm = MGCertificate.getUserLevel(req_user)

                if perm > level:
                    embed = MsgFormatter.get(
                        ctx_or_iaction,
                        _("Permission denied"),
                        _(
                            "%(member)s is not in the %(userlist)s. This incident will be reported."
                        )
                        % {
                            "member": f"<@{req_user_id}>",
                            "userlist": Level.get_description(level),
                        },
                        show_req_user=False,
                    )
                    embed.add_field(name=_("User"), value=req_user)
                    embed.add_field(
                        name=_("Command tried"),
                        value="{} ({})".format(
                            ctx_or_iaction.command.name, Level.get_description(level)
                        ),
                    )
                    await send(ctx_or_iaction, embed=embed)
                    logger.critical(
                        '"{}" tried to command "{}" that needs "{}" permission.'.format(
                            req_user,
                            ctx_or_iaction.command.name,
                            Level.get_description(level),
                        )
                    )
                    return

                return await func(*args, **kwargs)

            return outerfunc

        return deco
