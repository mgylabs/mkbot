import asyncio
import random
import shlex

import discord
from discord import app_commands
from discord.app_commands import locale_str
from discord.ext import commands

from mgylabs.i18n import __
from mgylabs.utils.LogEntry import DiscordEventLogEntry

from .utils.command_helper import related_commands
from .utils.MGCert import Level, MGCertificate
from .utils.MsgFormat import MsgFormatter


@commands.hybrid_command(aliases=["rou"])
@app_commands.describe(items=locale_str('item1 "item 2" "item3" ...'))
@MGCertificate.verify(level=Level.TRUSTED_USERS)
@related_commands(["dice", "lotto", "poll"])
async def roulette(ctx: commands.Context, *, items: str):
    """
    Play roulette

    Examples:
    {commandPrefix}roulette @user1 @user2 @user3
    {commandPrefix}rou "item 1" "item 2"

    Note:
    This bot cannot be added to items.
    """
    item_ls = shlex.split(items)

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

    result = random.choice(item_ls)

    DiscordEventLogEntry.Add(
        ctx, "RouletteResult", {"result": result, "items": item_ls}
    )

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
