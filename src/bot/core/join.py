from discord.ext import commands


def setup(bot: commands.Bot):
    @commands.command()
    @bot.MGCert.verify(2)
    async def join(ctx: commands.Context):
        """
        Joins voice channel that the user who typed the command is in
        """
        channel = ctx.message.channel
        voice_channel = ctx.author.voice.channel
        await voice_channel.connect()
        await ctx.message.delete()
        await channel.send(embed=bot.replyformat.get(ctx, 'joined {}'.format(voice_channel.name)))

    bot.add_command(join)
