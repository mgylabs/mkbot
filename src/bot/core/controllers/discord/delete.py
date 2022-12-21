from discord.ext import commands

from mgylabs.i18n import _
from mgylabs.utils.LogEntry import DiscordCommandEventLogEntry

from .utils.MGCert import Level, MGCertificate
from .utils.MsgFormat import MsgFormatter


@commands.command()
@MGCertificate.verify(level=Level.ADMIN_USERS)
async def delete(ctx: commands.Context, amount):
    """
    Deletes messages. (Requires Admin Permission)
    {commandPrefix}delete amount : deletes 'amount' number of messages
    {commandPrefix}delete all : deletes all(maximum 200) messages
    """
    channel = ctx.message.channel
    messages = []

    await ctx.message.delete()

    if amount.isdigit():
        await channel.purge(limit=int(amount))
        await channel.send(
            embed=MsgFormatter.get(ctx, _("%d Messages Deleted") % int(amount))
        )

    elif amount == "all":
        async for message in channel.history(limit=200):
            messages.append(message)

        amount = len(messages)
        await channel.purge(limit=amount)
        await channel.send(
            embed=MsgFormatter.get(ctx, _("%d Messages Deleted") % int(amount))
        )

    DiscordCommandEventLogEntry.add(ctx, "MessageDeleted", {"count": int(amount)})


async def setup(bot: commands.Bot):
    bot.add_command(delete)
