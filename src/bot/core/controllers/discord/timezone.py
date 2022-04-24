from datetime import datetime
from typing import Optional

import pytz
from core.controllers.discord.utils.command_helper import send
from core.controllers.discord.utils.MGCert import Level, MGCertificate
from mgylabs.db.models import DiscordUser

import discord
from discord import app_commands
from discord.ext import commands

from .utils.MsgFormat import MsgFormatter
from .utils.register import add_cog, add_command


class TimeZone(commands.Cog):
    timezone_group = app_commands.Group(name="timezone", description="Timezone")

    @timezone_group.command()
    @MGCertificate.verify(level=Level.TRUSTED_USERS)
    async def set(
        self,
        interaction: discord.Interaction,
        timezone: str,
        member: Optional[discord.Member],
    ):
        """
        Sets user's timezone
        """
        if member is None:
            member = interaction.user
        elif member != interaction.user and not MGCertificate.isAdminUser(
            str(interaction.user)
        ):
            await send(
                interaction,
                embed=MsgFormatter.get(
                    interaction,
                    "Timezone",
                    "Permission denied",
                ),
            )
            return

        try:
            pytz.timezone(timezone)
        except Exception as error:
            raise app_commands.AppCommandError(f"Invalid timezone: {error}")

        user, _ = DiscordUser.get_or_create(id=member.id)
        user.timezone = timezone
        user.save()

        await send(
            interaction,
            embed=MsgFormatter.get(
                interaction,
                "Timezone",
                f"Successfully set timezone of {member.mention} to {timezone}",
            ),
        )

    @set.autocomplete("timezone")
    async def set_timezone_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ):
        ls = [
            app_commands.Choice(name=v, value=v)
            for v in pytz.all_timezones
            if current.lower() in v.lower()
        ]

        return ls[:20]

    @timezone_group.command()
    @MGCertificate.verify(level=Level.TRUSTED_USERS)
    async def show(
        self,
        interaction: discord.Interaction,
        member: Optional[discord.Member],
    ):
        """
        Shows user's timezone
        """
        if member is None:
            member = interaction.user
        elif member != interaction.user and not MGCertificate.isAdminUser(
            str(interaction.user)
        ):
            await send(
                interaction,
                embed=MsgFormatter.get(
                    interaction,
                    "Timezone",
                    "Permission denied",
                ),
            )
            return

        if user := DiscordUser.get_one(id=member.id):
            await send(
                interaction,
                embed=MsgFormatter.get(
                    interaction,
                    user.timezone,
                    f"Timezone of {member.mention}",
                ),
                ephemeral=True,
            )
        else:
            await send(
                interaction,
                embed=MsgFormatter.get(
                    interaction,
                    "Timezone",
                    f"Timezone of {member.mention}: UTC",
                ),
                ephemeral=True,
            )

    @timezone_group.command(name="local-time")
    @MGCertificate.verify(level=Level.TRUSTED_USERS)
    async def localtime(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
    ):
        """
        Shows the user's local time
        """
        embed = _make_local_time_embed_(interaction, member)
        await send(interaction, embed=embed, ephemeral=True)


def _make_local_time_embed_(interaction, member):
    user = DiscordUser.get_one(id=member.id)

    if user is None:
        tz = pytz.timezone("UTC")
    else:
        tz = pytz.timezone(user.timezone)

    d = pytz.utc.localize(datetime.utcnow()).astimezone(tz)

    lt = d.strftime("%Y-%m-%d %I:%M %p")

    return MsgFormatter.get(
        interaction,
        lt,
        f"Local time of {member.mention} ({d.strftime('GMT%z')})",
    )


@app_commands.context_menu(name="Show local time")
@MGCertificate.verify(level=Level.TRUSTED_USERS)
async def local_time(interaction: discord.Interaction, member: discord.Member):
    """
    Shows the user's local time
    """
    embed = _make_local_time_embed_(interaction, member)

    await send(interaction, embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    add_command(bot, local_time)
    await add_cog(bot, TimeZone)
