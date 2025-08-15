import discord
from discord import app_commands
from discord.ext import commands

from mgylabs.utils.version import VERSION

from .utils.MGCert import Level, MGCertificate
from .utils.MsgFormat import MsgFormatter


@app_commands.command()
@app_commands.describe()
@MGCertificate.verify(level=Level.TRUSTED_USERS)
async def ping(interaction: discord.Interaction):
    """
    Shows the bot's latency.
    """
    v = {
        "name": "Version",
        "value": str(VERSION),
        "inline": True,
    }

    c = {
        "name": "Commit",
        "value": VERSION.commit[:7] if VERSION.commit else "N/A",
        "inline": True,
    }

    p = {
        "name": "Ping",
        "value": "%sms" % round(interaction.client.latency * 1000),
        "inline": True,
    }

    embed = MsgFormatter.get(
        interaction,
        "Mulgyeol MK Bot",
        "Copyright © Mulgyeol Labs. All rights reserved.",
        [v, c, p],
        thumbnail_url=interaction.client.user.avatar.url,
        url="https://github.com/mgylabs/mkbot",
    )

    await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    bot.tree.add_command(ping)
