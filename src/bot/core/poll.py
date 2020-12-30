from discord.ext import commands

from .utils.MGCert import Level, MGCertificate
from .utils.MsgFormat import MsgFormatter


@commands.command()
@MGCertificate.verify(level=Level.TRUSTED_USERS)
async def poll(ctx: commands.Context, question, *candidates):
    """
    Poll command
    {commandPrefix}poll "choose which?" a b c : a, b, c Generate a poll with three candidates. (do not use ,)
    you can vote using reactions
    """
    channel = ctx.message.channel

    if len(candidates) <= 1:
        await channel.send(
            embed=MsgFormatter.get(ctx, "You need more than two candidates!")
        )
        return
    elif len(candidates) > 10:
        await channel.send(
            embed=MsgFormatter.get(ctx, "You cannot make more than 10 candidates!")
        )
        return
    else:
        # reactions for 1, 2, 3... 10
        reactions = ["1⃣", "2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣", "8⃣", "9⃣", "🔟"]

        message = "\n".join((f"{n+1}. {v}" for n, v in enumerate(candidates)))

        botmsg = await channel.send(embed=MsgFormatter.get(ctx, question, message))
        for reaction in reactions[: len(candidates)]:
            await botmsg.add_reaction(reaction)


def setup(bot: commands.Bot):
    bot.add_command(poll)
