from discord.ext import commands

from .utils.MGCert import Level, MGCertificate
from .utils.MsgFormat import MsgFormatter


@commands.command()
@MGCertificate.verify(level=Level.TRUSTED_USERS)
async def ping(ctx: commands.Context):
    """
    Shows the bot's latency
    """
    await ctx.send(embed=MsgFormatter.get(ctx, f"Pong in {round(ctx.bot.latency*1000)}ms"))


def setup(bot: commands.Bot):
    bot.add_command(ping)
