import discord
from discord.ext import commands

from mgylabs.i18n import __


def send(ctx_or_iaction, content=None, **kwagrs):
    if isinstance(ctx_or_iaction, commands.Context):
        return ctx_or_iaction.send(content, **kwagrs)
    elif isinstance(ctx_or_iaction, discord.Interaction):
        if content:
            content += "\n[{0}](https://discord.gg/3RpDwjJCeZ)".format(
                __("Give Feedback ▶")
            )
        else:
            content = "[{0}](https://discord.gg/3RpDwjJCeZ)".format(
                __("Give Feedback ▶")
            )

        return ctx_or_iaction.response.send_message(content, **kwagrs)
