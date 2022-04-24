import discord
from mgylabs.utils.config import CONFIG


def add_command(bot, command):
    bot.tree.add_command(
        command, guilds=[discord.Object(g) for g in CONFIG.discordAppCmdGuilds]
    )


async def add_cog(bot, Cog):
    await bot.add_cog(
        Cog(bot), guilds=[discord.Object(g) for g in CONFIG.discordAppCmdGuilds]
    )
