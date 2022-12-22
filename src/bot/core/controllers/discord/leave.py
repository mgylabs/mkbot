from discord.ext import commands

from .utils.MGCert import Level, MGCertificate
from .utils.MsgFormat import MsgFormatter


@commands.command()
@MGCertificate.verify(level=Level.TRUSTED_USERS)
async def leave(ctx: commands.Context):
    """
    Leaves voice channel where the user who typed the command is in
    """
    channel = ctx.message.channel
    voice_channel = ctx.author.voice.channel
    await ctx.message.delete()
    for x in ctx.bot.voice_clients:
        if x.guild == ctx.message.guild:
            await x.disconnect()
            await channel.send(
                embed=MsgFormatter.get(ctx, "left {}".format(voice_channel.name))
            )


async def setup(bot: commands.Bot):
    bot.add_command(leave)
