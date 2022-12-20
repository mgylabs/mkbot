import discord
from babel import Locale

from mgylabs.db.models import DiscordUser


def init_user_locale(interaction: discord.Interaction):
    user: DiscordUser
    if user := DiscordUser.get_one(id=interaction.user.id):
        if user.locale is None:
            user.locale = str(interaction.locale)
            user.save()

            return Locale.parse(str(interaction.locale)).get_language_name()
    return None


def get_user_locale_code(user_id):
    user: DiscordUser
    if user := DiscordUser.get_one(id=user_id):
        return user.locale
    return None
