import random

from discord.ext import commands

from mgylabs.i18n import __

from .utils.MGCert import Level, MGCertificate
from .utils.MsgFormat import MsgFormatter


@commands.command()
@MGCertificate.verify(level=Level.TRUSTED_USERS)
async def yacht(ctx: commands.Context):
    """
    Play simplified version of Yacht Dice!
    """
    dices = [
        ":zero:",
        "1⃣",
        "2⃣",
        "3⃣",
        "4⃣",
        "5⃣",
        ":six:",
    ]
    rolledDice = []

    # run dice
    for i in range(5):
        rand = random.randint(1, 6)
        rolledDice.append(dices[rand])

    botmsg = await ctx.send(
        embed=MsgFormatter.get(
            ctx,
            __("Yacht Dice!"),
            rolledDice.toString(),
        )
    )

    for i in range(5):
        await botmsg.add_reaction(rolledDice[i])
    await botmsg.add_reaction("✅")


async def setup(bot: commands.Bot):
    bot.add_command(yacht)
