from discord.ext import commands


def setup(bot: commands.Bot):
    @commands.command()
    @bot.MGCert.verify(2)
    async def leave(ctx: commands.Context):
        """
        Leaves voice channel where the user who typed the command is in
        """
        channel = ctx.message.channel
        voice_channel = ctx.author.voice.channel
        await ctx.message.delete()
        for x in bot.voice_clients:
            if(x.guild == ctx.message.guild):
                await x.disconnect()
                await channel.send(embed=bot.replyformat.get(ctx, 'leaved {}'.format(voice_channel.name)))

    bot.add_command(leave)
