from functools import wraps

import discord
from discord.ext import commands

from core.controllers.discord.utils.command_helper import send
from mgylabs.i18n import __
from mgylabs.utils.config import CONFIG, VERSION, is_development_mode


class Feature:
    @classmethod
    def user_has_MBSS_access(cls, bot: commands.Bot, user_id: int):
        if is_development_mode():
            return True

        guild = bot.get_guild(VERSION.MBSS_ID)

        if guild and guild.get_member(user_id):
            return True
        else:
            return False

    @classmethod
    def Experiment(cls):
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

                if cls.user_has_MBSS_access(bot, user.id):
                    return await func(*args, **kwargs)
                else:
                    await send(
                        ctx_or_iaction,
                        (
                            __(
                                "This command is an experimental feature and only available when you have access to the **MK Bot Support Server**."
                            )
                            + (
                                "\nhttps://discord.gg/3RpDwjJCeZ"
                                if CONFIG.showFeedbackLink
                                else ""
                            )
                        ),
                    )
                    return

            return outerfunc

        return deco
