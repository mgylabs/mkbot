import logging

import aiofiles
import aiohttp
import discord
from discord.ext import commands

from .utils.config import CONFIG
from .utils.MGCert import Level, MGCertificate
from .utils.MsgFormat import MsgFormatter

log = logging.getLogger(__name__)

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

    if ctx.voice_client == None:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send(embed=MsgFormatter.get(ctx, "Usage Error", "You are not in any voice channel. Please join a voice channel to use TTS."))
            log.warning("Author not connected to a voice channel.")
            return

    headers = {
        'Content-Type': 'application/xml',
        'Authorization': 'KakaoAK ' + CONFIG.kakaoToken,
    }

    if args[0][0] == '-':
        voice = args[0]
        string = ' '.join(args[1:])
        if voice.upper() == '-M':
            vs = 'MAN_DIALOG_BRIGHT'
        elif voice.upper() == '-W':
            vs = 'WOMAN_DIALOG_BRIGHT'
        else:
            await ctx.send(embed=MsgFormatter.get(ctx, "Usage Error", f"Invalid parameter. For more information, type `{CONFIG.commandPrefix}help tts`."))
            return
    else:
        string = ' '.join(args)
        vs = 'MAN_DIALOG_BRIGHT'

    data = '<speak><voice name="{}">{}</voice></speak>'.format(
        vs, string).encode('utf-8')

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post('https://kakaoi-newtone-openapi.kakao.com/v1/synthesize', data=data) as r:
            if r.status == 200:
                async with aiofiles.open('temp_tts.mp3', 'wb') as f:
                    await f.write(await r.read())

    ctx.voice_client.play(discord.FFmpegPCMAudio('temp_tts.mp3'))

    await ctx.message.delete()
    embed = MsgFormatter.get(
        ctx, string, '[MK Bot](https://github.com/mgylabs/mulgyeol-mkbot) said on behalf of <@{}>'.format(ctx.author.id))
    embed.set_author(name=ctx.message.author.name,
                     icon_url=ctx.message.author.avatar_url)
    await ctx.send(embed=embed)


def setup(bot: commands.Bot):
    bot.add_command(tts)
