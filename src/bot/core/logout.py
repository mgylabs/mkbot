from discord.ext import commands

from .utils.MGCert import Level, MGCertificate
from .utils.MsgFormat import MsgFormatter


@commands.command()
@MGCertificate.verify(level=Level.ADMIN_USERS)
async def logout(ctx: commands.Context):
    """
    Terminates bot (Requires Admin Permission)
    """
    await ctx.send(embed=MsgFormatter.get(ctx, "Logs out of Discord and closes all connections"))
    print('Logged out')
    await ctx.bot.logout()


def setup(bot: commands.Bot):
    bot.add_command(logout)
