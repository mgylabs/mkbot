from discord.ext import commands


def setup(bot: commands.Bot):
    @commands.command()
    @bot.MGCert.verify(2)
    async def delete(ctx: commands.Context, amount):
        """
        Deletes messages
        {commandPrefix}delete amount : deletes 'amount' number of messages
        {commandPrefix}delete all : deletes all(maximum 200) messages
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
