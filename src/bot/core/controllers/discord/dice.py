import asyncio
import random

import discord
from discord.ext import commands

from mgylabs.i18n import __
from mgylabs.utils.config import resource_path
from mgylabs.utils.LogEntry import DiscordEventLogEntry

from .utils import Emoji
from .utils.command_helper import related_commands
from .utils.feature import Feature
from .utils.MGCert import Level, MGCertificate
from .utils.MsgFormat import MsgFormatter


@commands.hybrid_command()
@MGCertificate.verify(level=Level.TRUSTED_USERS)
@Feature.Experiment()
@related_commands(["dday set", "roulette", "poll"])
async def dice(ctx: commands.Context):
    """
    Roll a dice.
    """
    embed = MsgFormatter.get(
        ctx, description=f"{Emoji.typing} {__('Rolling a dice...')}"
    )
    dice_file = discord.File(
        resource_path("common/bot/Game Die.png"), filename="dice.png"
    )
    embed.set_author(name="Dice", icon_url="attachment://dice.png")

    msg: discord.Message = await ctx.send(embed=embed, file=dice_file)

    result = random.randint(1, 6)

    DiscordEventLogEntry.Add(ctx, "DiceResult", {"result": result})

    dice_file = discord.File(
        resource_path("common/bot/Game Die.png"), filename="dice.png"
    )

    number_file_name = f"Keycap Digit {result}.png"
    discord_number_file_name = number_file_name.replace(" ", "")
    number_file = discord.File(
        resource_path(f"common/bot/{number_file_name}"),
        filename=discord_number_file_name,
    )

    embed.description = None
    embed.set_thumbnail(url=f"attachment://{discord_number_file_name}")

    await asyncio.sleep(1)

    await msg.edit(embed=embed, attachments=[dice_file, number_file])


async def setup(bot: commands.Bot):
    bot.add_command(dice)
