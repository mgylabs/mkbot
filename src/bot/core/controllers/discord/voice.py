import io

import discord
from discord.ext import commands
from gtts import gTTS

from mgylabs.i18n import __
from mgylabs.utils import logger

from .utils.exceptions import UsageError
from .utils.feature import Feature
from .utils.MGCert import Level, MGCertificate
from .utils.MsgFormat import MsgFormatter
from .utils.voice import validate_voice_client

log = logger.get_logger(__name__)


@commands.hybrid_command()
@MGCertificate.verify(level=Level.TRUSTED_USERS)
@Feature.Experiment()
async def voice(ctx: commands.Context, *, content: str):
    """
    TTS voice available
    {commandPrefix}tts "Content" : Says the content in "content". You do not have to use Quotation marks even if there are spaces included in content.

    *Example*
    {commandPrefix}tts "Content"
    """

    if not await validate_voice_client(ctx):
        raise UsageError(
            __(
                "You are not in any voice channel. Please join a voice channel to use TTS."
            )
        )

    mp3 = io.BytesIO()
    gtts = gTTS(content, lang="ko")
    gtts.write_to_fp(mp3)
    mp3.seek(0)

    if not ctx.interaction:
        await ctx.message.delete()

    embed = MsgFormatter.get(
        ctx,
        content,
        __("[MK Bot]({url}) said on behalf of {author}").format(
            url="https://github.com/mgylabs/mkbot", author=ctx.author.mention
        ),
        show_req_user=False,
    )

    embed.set_author(
        name=ctx.message.author.display_name, icon_url=ctx.message.author.avatar.url
    )
    await ctx.send(embed=embed)

    ctx.voice_client.play(discord.FFmpegPCMAudio(mp3, pipe=True))


async def setup(bot: commands.Bot):
    bot.add_command(voice)
