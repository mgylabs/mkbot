from discord.ext import commands


def setup(bot: commands.Bot):
    @commands.command()
    @bot.MGCert.verify(2)
    async def poll(ctx, question, *candidates):
        """
        투표 명령어입니다.
        {commandPrefix}poll "어느걸 고를래?" a b c : a, b, c 세 개의 후보를 가진 투표를 생성합니다. (, 사용은 안됩니다)
        reaction 기능으로 투표를 할 수 있습니다.
        """
        channel = ctx.message.channel

        if len(candidates) <= 1:
            await channel.send(embed=bot.replyformat.get(ctx, '후보가 2개 이상은 있어야 합니다!'))
            return
        elif len(candidates) > 10:
            await channel.send(embed=bot.replyformat.get(ctx, '후보를 10개 넘게는 만들 수 없습니다!'))
            return
        else:
            # reactions for 1, 2, 3... 10
            reactions = ['1⃣', '2⃣', '3⃣', '4⃣',
                         '5⃣', '6⃣', '7⃣', '8⃣', '9⃣', '🔟']

            message = '\n'.join(
                (f'{n+1}. {v}' for n, v in enumerate(candidates)))

            botmsg = await channel.send(embed=bot.replyformat.get(ctx, question, message))
            for reaction in reactions[:len(candidates)]:
                await botmsg.add_reaction(reaction)

    bot.add_command(poll)
