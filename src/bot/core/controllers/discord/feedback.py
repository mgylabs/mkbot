import traceback

from core.controllers.discord.utils.MGCert import Level, MGCertificate
from core.controllers.discord.utils.register import add_command

import discord
from discord import app_commands
from discord.ext import commands


class Dropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Bug Report",
                description="Report broken or incorrect behaviour",
                emoji="💡",
            ),
            discord.SelectOption(
                label="Feature Request",
                description="Suggest a feature for this library",
                emoji="🪲",
            ),
        ]

        super().__init__(
            placeholder="Select feedback type...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        self.fv = Feedback(self.values[0])
        await interaction.response.send_modal(self.fv)
        self.view.stop()


class DropdownView(discord.ui.View):
    def __init__(self):
        super().__init__()

        self.d = Dropdown()
        self.add_item(self.d)


class Feedback(discord.ui.Modal):
    summary = discord.ui.TextInput(
        label="Summarize your feedback",
        required=True,
    )

    feedback = discord.ui.TextInput(
        label="Explain in more detail (optional)",
        style=discord.TextStyle.long,
        placeholder="Give as much detail as you can.",
        required=False,
        max_length=300,
    )

    def __init__(self, feedback_type, **kwargs) -> None:
        super().__init__(title=f"Feedback ({feedback_type})", **kwargs)
        self.feedback_type = feedback_type

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"Thanks for your feedback, {interaction.user.name}!", ephemeral=True
        )

        if self.feedback_type == "Bug Report":
            ch_id = 699936047018278982
        else:
            ch_id = 950758949370601502

        text = f"[{self.feedback_type}]\n{self.summary}"

        if self.feedback.value != "":
            text += f"\n\n{self.feedback}"

        text += f"\n\nby {interaction.user.name}"

        await interaction.client.get_channel(ch_id).send(text)

    async def on_error(
        self, error: Exception, interaction: discord.Interaction
    ) -> None:
        await interaction.response.send_message(
            "Oops! Something went wrong.", ephemeral=True
        )

        traceback.print_tb(error.__traceback__)


@app_commands.command()
@MGCertificate.verify(level=Level.TRUSTED_USERS)
async def feedback(interaction: discord.Interaction):
    """
    Sends feedback
    """
    view = DropdownView()
    await interaction.response.send_message(view=view, ephemeral=True)

    await view.wait()
    view.clear_items()

    await interaction.edit_original_message(
        content=f"Thanks for your feedback, {interaction.user.name}!", view=view
    )


async def setup(bot: commands.Bot):
    add_command(bot, feedback)
