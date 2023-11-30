import asyncio
import random

import discord
from discord.ext import commands

from mgylabs.i18n import __
from mgylabs.utils.LogEntry import DiscordEventLogEntry

from .utils.MGCert import Level, MGCertificate
from .utils.MsgFormat import MsgFormatter


@commands.command(aliases=["rou"])
@MGCertificate.verify(level=Level.TRUSTED_USERS)
async def roulette(ctx: commands.Context, *items):
    """
    Play roulette

    Examples:
    {commandPrefix}roulette @user1 @user2 @user3
    {commandPrefix}rou "item 1" "item 2"

    Note:
    This bot cannot be added to items.
    """
    msg: discord.Message = await ctx.send(
        embed=MsgFormatter.get(ctx, __("Roulette is running. Please wait."), "...")
    )

    for i in range(5, 0, -1):
        await msg.edit(
            embed=MsgFormatter.get(
                ctx, __("Roulette is running. Please wait."), __("%dsec left") % i
            )
        )
        await asyncio.sleep(1)

    result = random.choice(items)

    DiscordEventLogEntry.Add(ctx, "RouletteResult", {"result": result, "items": items})

    await msg.edit(
        embed=MsgFormatter.get(ctx, __("Roulette"), __("chose... %s!") % result)
    )


# @register_intent("command::roulette", "roulette")
# def cmd_roulette(intent: Intent):
#     if items := intent.get_an_entity("items"):
#         items: str
#         items = [i.strip() for i in items.split(",")]
#         return "roulette " + " ".join(f'"{i}"' for i in items)
#     else:
#         return None


async def setup(bot: commands.Bot):
    bot.add_command(roulette)
