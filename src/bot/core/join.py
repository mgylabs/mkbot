from discord.ext import commands


def setup(bot):
    @commands.command()
    @bot.MGCert.verify(2)
    async def join(ctx):
        """
        명령어를 입력한 유저가 있는 음성 채널을 입장합니다
        """
        channel = ctx.message.channel
        voice_channel = ctx.author.voice.channel
        await voice_channel.connect()
        await ctx.message.delete()
        await channel.send(embed=bot.replyformat.get(ctx, 'joined {}'.format(voice_channel.name)))

    bot.add_command(join)
