import discord
from discord.ext import commands

from mgylabs.i18n import __
from mgylabs.utils.config import VERSION, is_development_mode

from .utils.feature import Feature
from .utils.MGCert import Level, MGCertificate

if is_development_mode(False) or VERSION.is_canary():
    enabled = True
else:
    enabled = False


@commands.hybrid_command(hidden=True, enabled=enabled, with_app_command=enabled)
@MGCertificate.verify(level=Level.TRUSTED_USERS)
@Feature.Experiment()
async def act(ctx: commands.Context, member: discord.Member, *, message):
    if isinstance(ctx.channel, discord.Thread):
        webhooks = await ctx.channel.parent.webhooks()
    else:
        webhooks = await ctx.channel.webhooks()

    if webhooks:
        webhook = webhooks[0]
    else:
        webhook = await ctx.channel.create_webhook(name=member.name)

    if isinstance(ctx.channel, discord.Thread):
        await webhook.send(
            str(message),
            thread=ctx.channel,
            username=member.display_name,
            avatar_url=member.avatar.url,
        )
    else:
        await webhook.send(
            str(message), username=member.display_name, avatar_url=member.avatar.url
        )

    if ctx.interaction:
        await ctx.send(
            __("[MK Bot]({url}) acted like {member}.").format(
                url="<https://github.com/mgylabs/mkbot>", member=member.mention
            ),
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    bot.add_command(act)
