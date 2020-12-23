import random
import time

import discord
from discord.ext import commands

from .utils.MGCert import Level, MGCertificate
from .utils.MsgFormat import MsgFormatter


@commands.command(aliases=['rou'])
@MGCertificate.verify(level=Level.TRUSTED_USERS)
async def roulette(ctx: commands.Context, title, *items):
    """
    Play roulette

    Examples:
    {commandPrefix}roulette "Player" @user1 @user2 @user3
    {commandPrefix}rou "title" "item 1" "item 2"

    Note:
    This bot cannot be added to items.
    """
    msg: discord.Message = await ctx.send(embed=MsgFormatter.get(ctx, "Roulette is running. Please wait.", "..."))

    for i in range(5, 0, -1):
        await msg.edit(embed=MsgFormatter.get(ctx, "Roulette is running. Please wait.", f"{i} sec left"))
        time.sleep(1)

    await msg.edit(embed=MsgFormatter.get(
        ctx, f"Roulette for {title}", f"chose... {random.choice(items)}!"))

def setup(bot: commands.Bot):
    bot.add_command(roulette)
