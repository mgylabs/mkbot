import discord
from babel import Locale

from mgylabs.db.models import DiscordUser


def init_user_locale(interaction: discord.Interaction):
    user: DiscordUser
    if user := DiscordUser.get_one_or_none(id=interaction.user.id):
        if user.locale is None:
            user.locale = str(interaction.locale)
            user.save()

            return Locale.parse(str(interaction.locale)).get_language_name()
    return None


def set_user_locale_by_iaction(interaction: discord.Interaction, locale: str):
    user: DiscordUser
    user, _ = DiscordUser.get_or_create(id=interaction.user.id)

    user.locale = locale
    user.save()

    return Locale.parse(str(locale)).get_language_name()


def get_user_locale_code(user_id):
    user: DiscordUser
    if user := DiscordUser.get_one_or_none(id=user_id):
        return user.locale
    else:
        return None
