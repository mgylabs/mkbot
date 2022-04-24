from discord.ext import commands

from .utils.MGCert import Level, MGCertificate
from .utils.MsgFormat import MsgFormatter


@commands.command()
@MGCertificate.verify(level=Level.TRUSTED_USERS)
async def join(ctx: commands.Context):
    """
    Joins voice channel that the user who typed the command is in
    """
    channel = ctx.message.channel
    voice_channel = ctx.author.voice.channel
    await voice_channel.connect()
    await ctx.message.delete()
    await channel.send(
        embed=MsgFormatter.get(ctx, "joined {}".format(voice_channel.name))
    )


async def setup(bot: commands.Bot):
    bot.add_command(join)
