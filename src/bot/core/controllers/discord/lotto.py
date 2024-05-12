import random

from discord.ext import commands

from mgylabs.i18n import __

from .utils.command_helper import related_commands
from .utils.MGCert import Level, MGCertificate
from .utils.MsgFormat import MsgFormatter


@commands.hybrid_command()
@MGCertificate.verify(level=Level.TRUSTED_USERS)
@related_commands(["roulette", "dice", "dday set"])
async def lotto(ctx: commands.Context):
    """
    Recommends Korean lotto lucky numbers
    """
    reactions = [
        ":zero:",
        "1⃣",
        "2⃣",
        "3⃣",
        "4⃣",
        "5⃣",
        ":six:",
        ":seven:",
        ":eight:",
        ":nine:",
    ]
    lotto = ""

    for i in range(6):
        rand = random.randint(1, 45)
        ones = rand % 10
        tens = int((rand - ones) / 10)
        lotto += reactions[tens] + reactions[ones] + " "

    await ctx.send(
        embed=MsgFormatter.get(
            ctx,
            __("The lucky numbers are... :sunglasses:"),
            lotto,
        )
    )


# @register_intent("command::lotto", "lotto")
# def cmd_lotto(intent: Intent):
#     return "lotto"


async def setup(bot: commands.Bot):
    bot.add_command(lotto)
