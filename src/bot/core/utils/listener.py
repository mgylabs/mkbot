from functools import wraps

from discord import message
from .config import CONFIG
import discord


def on_message(bot):
    def deco(func):
        @wraps(func)
        async def outerfunc(*args, **kwargs):
            if isinstance(args[0], discord.Message):
                message = args[0]
            else:
                message = args[1]

            if message.author == bot.user:
                return

            if (message.channel.type.value == 1) and (CONFIG.disabledPrivateChannel):
                return
            ctx = await bot.get_context(message)

            if ctx.valid:
                return

            return await func(*args, **kwargs)
        return outerfunc
    return deco
