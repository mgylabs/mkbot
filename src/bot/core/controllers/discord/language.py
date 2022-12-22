from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from core.controllers.discord.utils.MGCert import Level, MGCertificate
from mgylabs.db.models import DiscordUser
from mgylabs.i18n import I18nExtension, _

from .utils.MsgFormat import MsgFormatter


class Language(commands.Cog):
    """Sets or shows user's display language."""

    @commands.hybrid_group(name="language", aliases=["lang"])
    @MGCertificate.verify(level=Level.TRUSTED_USERS)
    async def language_command(self, ctx: commands.Context) -> None:
        """
        Sets or shows user's display language.

        {commandPrefix}language set English

        {commandPrefix}language show
        """

    @language_command.command()
    @MGCertificate.verify(level=Level.TRUSTED_USERS)
    async def set(
        self,
        ctx: commands.Context,
        language: str,
        member: Optional[discord.Member] = None,
    ):
        """
        Sets user's display language.
        """
        if member is None:
            member = ctx.author
        elif member != ctx.author and not MGCertificate.isAdminUser(str(ctx.author)):
            await ctx.send(
                embed=MsgFormatter.get(
                    ctx,
                    "Language",
                    _("Permission denied"),
                ),
            )
            return

        if language not in ["ko", "en"]:
            await ctx.send(
                embed=MsgFormatter.get(
                    ctx,
                    "Language",
                    _("Invalid language"),
                ),
            )
            return

        user, __ = DiscordUser.get_or_create(id=member.id)
        user.locale = language
        user.save()

        if member.id == ctx.author.id:
            I18nExtension.change_current_locale(language)

        await ctx.send(
            embed=MsgFormatter.get(
                ctx,
                "Language",
                _("Successfully set display language of %(member)s to %(language)s")
                % {"member": member.mention, "language": user.get_language_name()},
            )
        )

    @set.autocomplete("language")
    async def set_language_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ):
        ls = [
            app_commands.Choice(name="English", value="en"),
            app_commands.Choice(name="한국어", value="ko"),
        ]

        return ls

    @language_command.command()
    @MGCertificate.verify(level=Level.TRUSTED_USERS)
    async def show(
        self,
        ctx: commands.Context,
        member: Optional[discord.Member],
    ):
        """
        Shows user's display language.
        """
        if member is None:
            member = ctx.author
        elif member != ctx.author and not MGCertificate.isAdminUser(str(ctx.author)):
            await ctx.send(
                embed=MsgFormatter.get(
                    ctx,
                    "Language",
                    _("Permission denied"),
                ),
            )
            return

        user: DiscordUser
        if user := DiscordUser.get_one(id=member.id):
            await ctx.send(
                embed=MsgFormatter.get(
                    ctx,
                    user.get_language_name(),
                    _("Display language of %(member)s") % {"member": member.mention},
                ),
                ephemeral=True,
            )
        else:
            await ctx.send(
                embed=MsgFormatter.get(
                    ctx,
                    "Language",
                    f"{_('Display language of %(member)s') % {'member': member.mention}}: English",
                ),
                ephemeral=True,
            )


async def setup(bot: commands.Bot):
    """
    Language
    """
    await bot.add_cog(Language(bot))
