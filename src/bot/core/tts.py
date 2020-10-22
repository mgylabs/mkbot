from discord.ext import commands
import discord
import requests
from .utils.config import CONFIG


def setup(bot: commands.Bot):
    @commands.command()
    @bot.MGCert.verify(2)
    async def tts(ctx: commands.Context, *args):
        """
        TTS 목소리를 사용할 수 있습니다.
        {commandPrefix}tts [option] "내용" : 내용에 있는 내용을 말합니다. 내용에 띄어쓰기가 있는 경우에도 큰 따옴표로 감싸지 않아도 됩니다.

        *사용예시*
        {commandPrefix}tts "내용"
        {commandPrefix}tts -m "내용"
        {commandPrefix}tts -w "내용": -m 은 남성 목소리로 말하고 -w 는 여성 목소리로 말합니다. 기본은 남성입니다.
        """

        if ctx.voice_client == None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send(embed=bot.replyformat.get(ctx, "Usage Error", "You are not in any voice channel. Please join a voice channel to use TTS."))
                raise commands.CommandError(
                    "Author not connected to a voice channel.")

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
                vs = 'WOMAN_DIALOG_BRIGH'
            else:
                await ctx.send(embed=bot.replyformat.get(ctx, "Usage Error", f"Invalid parameter. For more information, type `{CONFIG.commandPrefix}help tts`."))
                raise commands.CommandError("Error")
        else:
            string = ' '.join(args)
            vs = 'MAN_DIALOG_BRIGHT'

        data = '<speak><voice name="{}">{}</voice></speak>'.format(
            vs, string).encode('utf-8')
        response = requests.post(
            'https://kakaoi-newtone-openapi.kakao.com/v1/synthesize', headers=headers, data=data)

        with open('temp.mp3', 'wb') as f:
            f.write(response.content)

        ctx.voice_client.play(discord.FFmpegPCMAudio('temp.mp3'))

        await ctx.message.delete()
        embed = bot.replyformat.get(
            ctx, string, '[MK Bot](https://gitlab.com/mgylabs/mulgyeol-mkbot) said on behalf of <@{}>'.format(ctx.author.id))
        embed.set_author(name=ctx.message.author.name,
                         icon_url=ctx.message.author.avatar_url)
        await ctx.send(embed=embed)

    bot.add_command(tts)
