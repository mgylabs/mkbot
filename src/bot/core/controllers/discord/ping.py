import discord
from discord import app_commands
from discord.ext import commands

from .utils.MsgFormat import MsgFormatter
from .utils.register import add_command


@app_commands.command()
@app_commands.describe()
async def ping(interaction: discord.Interaction):
    """
    Shows the bot's latency
    """
    await interaction.response.send_message(
        embed=MsgFormatter.get(
            interaction, f"Pong in {round(interaction.client.latency*1000)}ms"
        )
    )


async def setup(bot: commands.Bot):
    add_command(bot, ping)
