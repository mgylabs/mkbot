import asyncio
import random

import discord
from discord.ext import commands

from mgylabs.i18n import _

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
        embed=MsgFormatter.get(ctx, _("Roulette is running. Please wait."), "...")
    )

    for i in range(5, 0, -1):
        await msg.edit(
            embed=MsgFormatter.get(
                ctx, _("Roulette is running. Please wait."), _("%dsec left") % i
            )
        )
        asyncio.sleep(1)

    await msg.edit(
        embed=MsgFormatter.get(
            ctx, _("Roulette"), _("chose... %s!") % random.choice(items)
        )
    )


async def setup(bot: commands.Bot):
    bot.add_command(roulette)
