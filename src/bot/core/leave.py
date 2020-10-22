from discord.ext import commands


def setup(bot: commands.Bot):
    @commands.command()
    @bot.MGCert.verify(2)
    async def leave(ctx: commands.Context):
        """
        명령어를 입력한 유저가 있는 음성채널을 퇴장합니다
        """
        channel = ctx.message.channel
        voice_channel = ctx.author.voice.channel
        await ctx.message.delete()
        for x in bot.voice_clients:
            if(x.guild == ctx.message.guild):
                await x.disconnect()
                await channel.send(embed=bot.replyformat.get(ctx, 'leaved {}'.format(voice_channel.name)))

    bot.add_command(leave)
