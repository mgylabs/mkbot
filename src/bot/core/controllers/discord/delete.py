from discord.ext import commands

from mgylabs.i18n import __
from mgylabs.utils.LogEntry import DiscordEventLogEntry

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
            embed=MsgFormatter.get(ctx, __("%d Messages Deleted") % int(amount))
        )

    elif amount == "all":
        async for message in channel.history(limit=200):
            messages.append(message)

        amount = len(messages)
        await channel.purge(limit=amount)
        await channel.send(
            embed=MsgFormatter.get(ctx, __("%d Messages Deleted") % int(amount))
        )

    DiscordEventLogEntry.Add(ctx, "MessageDeleted", {"count": int(amount)})


# @register_intent("command::delete", "delete")
# def cmd_delete(intent: Intent):
#     if amount := intent.get_an_entity("amount"):
#         return f"delete {amount}"
#     else:
#         return "delete 2"


async def setup(bot: commands.Bot):
    bot.add_command(delete)
