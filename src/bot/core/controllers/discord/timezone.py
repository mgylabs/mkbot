from datetime import datetime
from typing import Optional

import discord
import pytz
from discord import app_commands
from discord.app_commands import locale_str
from discord.ext import commands

from core.controllers.discord.utils.command_helper import send
from core.controllers.discord.utils.MGCert import Level, MGCertificate
from mgylabs.db.models import DiscordUser
from mgylabs.i18n import _L, __

from .utils.MsgFormat import MsgFormatter


class TimeZone(commands.Cog):
    timezone_group = app_commands.Group(
        name="timezone", description=_L("Shows user's local time.")
    )

    @timezone_group.command()
    @MGCertificate.verify(level=Level.TRUSTED_USERS)
    async def set(
        self,
        interaction: discord.Interaction,
        timezone: str,
        member: Optional[discord.Member],
    ):
        """
        Sets user's timezone.
        """
        if member is None:
            member = interaction.user
        elif member != interaction.user and not MGCertificate.isAdminUser(
            interaction.user
        ):
            await send(
                interaction,
                embed=MsgFormatter.get(
                    interaction,
                    "Timezone",
                    __("Permission denied"),
                ),
            )
            return

        try:
            pytz.timezone(timezone)
        except Exception as error:
            raise app_commands.AppCommandError(__("Invalid timezone: %s") % error)

        user, _ = DiscordUser.get_or_create(id=member.id)
        user.timezone = timezone
        user.save()

        await send(
            interaction,
            embed=MsgFormatter.get(
                interaction,
                "Timezone",
                __("Successfully set timezone of %(member)s to %(timezone)s")
                % {"member": member.mention, "timezone": timezone},
            ),
            ephemeral=True,
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
        Shows user's timezone.
        """
        if member is None:
            member = interaction.user
        elif member != interaction.user and not MGCertificate.isAdminUser(
            interaction.user
        ):
            await send(
                interaction,
                embed=MsgFormatter.get(
                    interaction,
                    "Timezone",
                    __("Permission denied"),
                ),
            )
            return

        if user := DiscordUser.get_one_or_none(id=member.id):
            await send(
                interaction,
                embed=MsgFormatter.get(
                    interaction,
                    user.timezone,
                    __("Timezone of %(member)s") % {"member": member.mention},
                ),
                ephemeral=True,
            )
        else:
            await send(
                interaction,
                embed=MsgFormatter.get(
                    interaction,
                    "Timezone",
                    f"{__('Timezone of %(member)s') % {'member': member.mention}}: UTC",
                ),
                ephemeral=True,
            )

    @timezone_group.command(name="localtime")
    @MGCertificate.verify(level=Level.TRUSTED_USERS)
    async def localtime(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
    ):
        """
        Shows the user's local time.
        """
        embed = _make_local_time_embed_(interaction, member)
        await send(interaction, embed=embed, ephemeral=True)


def _make_local_time_embed_(interaction, member):
    user = DiscordUser.get_one_or_none(id=member.id)

    if user is None:
        tz = pytz.timezone("UTC")
    else:
        tz = pytz.timezone(user.timezone)

    d = pytz.utc.localize(datetime.utcnow()).astimezone(tz)

    lt = d.strftime("%Y-%m-%d %I:%M %p")

    return MsgFormatter.get(
        interaction,
        lt,
        __("Local time of %(member)s (%(timezone)s)")
        % {"member": member.mention, "timezone": d.strftime("GMT%z")},
    )


@app_commands.context_menu(name=locale_str("Show local time"))
@MGCertificate.verify(level=Level.TRUSTED_USERS)
async def local_time(interaction: discord.Interaction, member: discord.Member):
    embed = _make_local_time_embed_(interaction, member)

    await send(interaction, embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    bot.tree.add_command(local_time)
    await bot.add_cog(TimeZone(bot))
