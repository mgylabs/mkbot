import discord

from core.controllers.discord.utils.MsgFormat import MsgFormatter
from mgylabs.i18n import I18nExtension, _
from mgylabs.i18n.utils import set_user_locale_by_iaction


class LanguageDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="English", value="en"),
            discord.SelectOption(label="한국어", value="ko"),
        ]

        super().__init__(
            placeholder="🌐 Select your language...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        self.view.stop()

        language = set_user_locale_by_iaction(interaction, self.values[0])

        I18nExtension.change_current_locale(self.values[0])

        await interaction.response.send_message(
            embed=MsgFormatter.get(
                interaction,
                _("Your display language has been changed to %s.") % language,
                _(
                    "Type `/language set` or `{commandPrefix}language set` to change your display language."
                ),
            ),
            ephemeral=True,
        )


class LanguageButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.primary, label="Change your language..."
        )

    async def callback(self, interaction: discord.Interaction):
        if self.view.message is not None:
            await self.view.message.delete()

        view = discord.ui.View()
        view.add_item(LanguageDropdown())
        await interaction.response.send_message(view=view, ephemeral=True)
        await view.wait()

        await interaction.delete_original_response()
        if self.view.user_id == interaction.user.id:
            self.view.stop()


class LanguageSettingView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.message = None

        self.add_item(LanguageButton())
