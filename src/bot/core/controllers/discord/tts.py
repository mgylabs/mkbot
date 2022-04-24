import io
import logging
import shlex
import subprocess

import aiohttp
from mgylabs.utils.config import CONFIG

import discord
from discord.ext import commands
from discord.opus import Encoder

from .utils.exceptions import UsageError
from .utils.MGCert import Level, MGCertificate
from .utils.MsgFormat import MsgFormatter
from .utils.voice import validate_voice_client

log = logging.getLogger(__name__)


class FFmpegPCMAudio(discord.AudioSource):
    def __init__(
        self,
        source,
        *,
        executable="ffmpeg",
        pipe=False,
        stderr=None,
        before_options=None,
        options=None,
    ):
        stdin = None if not pipe else source
        args = [executable]
        if isinstance(before_options, str):
            args.extend(shlex.split(before_options))
        args.append("-i")
        args.append("-" if pipe else source)
        args.extend(("-f", "s16le", "-ar", "48000", "-ac", "2", "-loglevel", "warning"))
        if isinstance(options, str):
            args.extend(shlex.split(options))
        args.append("pipe:1")
        self._process = None
        try:
            self._process = subprocess.Popen(
                args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr
            )
            self._stdout = io.BytesIO(self._process.communicate(input=stdin)[0])
        except FileNotFoundError:
            raise commands.CommandError(executable + " was not found.") from None
        except subprocess.SubprocessError as exc:
            raise commands.CommandError(
                "Popen failed: {0.__class__.__name__}: {0}".format(exc)
            ) from exc

    def read(self):
        ret = self._stdout.read(Encoder.FRAME_SIZE)
        if len(ret) != Encoder.FRAME_SIZE:
            return b""
        return ret

    def cleanup(self):
        proc = self._process
        if proc is None:
            return
        proc.kill()
        if proc.poll() is None:
            proc.communicate()

        self._process = None


@commands.command()
@MGCertificate.verify(level=Level.TRUSTED_USERS)
async def tts(ctx: commands.Context, *args):
    """
    TTS voice available
    {commandPrefix}tts [option] "Content" : Says the content in "content". You do not have to use Quotation marks even if there are spaces included in content.

    *Example*
    {commandPrefix}tts "Content"
    {commandPrefix}tts -m "Content"
    {commandPrefix}tts -w "Content": -m speaks in male voice and -w speaks in female voice. Default voice is male.
    """

    if not await validate_voice_client(ctx):
        raise UsageError(
            "You are not in any voice channel. Please join a voice channel to use TTS."
        )

    headers = {
        "Content-Type": "application/xml",
        "Authorization": "KakaoAK " + CONFIG.kakaoToken,
    }

    if args[0][0] == "-":
        voice = args[0]
        string = " ".join(args[1:])
        if voice.upper() == "-M":
            vs = "MAN_DIALOG_BRIGHT"
        elif voice.upper() == "-W":
            vs = "WOMAN_DIALOG_BRIGHT"
        else:
            raise UsageError(
                f"Invalid parameter. For more information, type `{CONFIG.commandPrefix}help tts`."
            )
    else:
        string = " ".join(args)
        vs = "MAN_DIALOG_BRIGHT"

    data = '<speak><voice name="{}">{}</voice></speak>'.format(vs, string).encode(
        "utf-8"
    )

    async with aiohttp.ClientSession(headers=headers, raise_for_status=True) as session:
        async with session.post(
            "https://kakaoi-newtone-openapi.kakao.com/v1/synthesize", data=data
        ) as r:
            mp3 = io.BytesIO(await r.read())

    ctx.voice_client.play(FFmpegPCMAudio(mp3.read(), pipe=True))

    await ctx.message.delete()
    embed = MsgFormatter.get(
        ctx,
        string,
        "[MK Bot](https://github.com/mgylabs/mulgyeol-mkbot) said on behalf of <@{}>".format(
            ctx.author.id
        ),
    )
    embed.set_author(
        name=ctx.message.author.name, icon_url=ctx.message.author.avatar_url
    )
    await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    bot.add_command(tts)
