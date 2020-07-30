from discord.ext import commands


def setup(bot):
    @commands.command()
    @bot.MGCert.verify(2)
    async def delete(ctx, amount):
        """
        메세지를 삭제합니다.
        //delete amount : amount 만큼의 최근 메세지를 삭제합니다.
        //delete all : 모든 메세지(최대 200개)를 삭제합니다.
        """
        channel = ctx.message.channel
        messages = []

        await ctx.message.delete()

        if amount.isdigit():
            await channel.purge(limit=int(amount))
            await channel.send(embed=bot.replyformat.get(ctx, '{} Messages deleted'.format(amount)))

        elif amount == 'all':
            async for message in channel.history(limit=200):
                messages.append(message)

            amount = len(messages)
            await channel.purge(limit=amount)
            await channel.send(embed=bot.replyformat.get(ctx, '{} Messages deleted'.format(amount)))

    bot.add_command(delete)
