import discord
from discord import app_commands
from discord.ext import commands

from mgylabs.i18n import __

from .utils.MGCert import Level, MGCertificate
from .utils.MsgFormat import MsgFormatter


@app_commands.command()
@app_commands.describe()
@MGCertificate.verify(level=Level.TRUSTED_USERS)
async def ping(interaction: discord.Interaction):
    """
    Shows the bot's latency.
    """
    await interaction.response.send_message(
        embed=MsgFormatter.get(
            interaction, __("Pong in %sms") % round(interaction.client.latency * 1000)
        )
    )


async def setup(bot: commands.Bot):
    bot.tree.add_command(ping)
