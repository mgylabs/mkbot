from __future__ import annotations

import asyncio
import json
import random
import re
import shlex

import discord
from discord import app_commands
from discord.app_commands import locale_str
from discord.ext import commands

from mgylabs.i18n import __
from mgylabs.utils import logger
from mgylabs.utils.config import CONFIG
from mgylabs.utils.LogEntry import DiscordEventLogEntry

from .utils.emoji import Emoji
from .utils.feature import Feature
from .utils.gemini import gemini_enabled, get_gemini_response
from .utils.MGCert import Level, MGCertificate
from .utils.MsgFormat import MsgFormatter, related_commands

log = logger.get_logger(__name__)


def is_discord_special_string(s: str) -> bool:
    patterns = [
        r"^<@!?(\d+)>$",  # user mention
        r"^<@&(\d+)>$",  # role mention
        r"^<#(\d+)>$",  # channel mention
        r"^<a?:\w+:\d+>$",  # custom emoji
        r"^<t:\d+(?::[tTdDfFR])?>$",  # timestamp
    ]

    return any(re.match(pattern, s) for pattern in patterns)


class OracleCandyButton(discord.ui.Button["RouletteView"]):
    def __init__(self, label, emoji=None, enabled=False):
        super().__init__(
            label=label,
            style=discord.ButtonStyle.secondary,
            emoji=emoji,
        )
        self.disabled = not enabled
        self.buttons = None

    def add_buttons(self, buttons: list[OracleActionButton]):
        self.buttons = buttons

    async def callback(self, interaction: discord.Interaction) -> None:
        if interaction.user != self.view.ctx.author:
            await interaction.response.send_message(
                __("You are not authorized to use this button."), ephemeral=True
            )
            return

        self.label = "Generating..."
        self.emoji = Emoji.generating

        await interaction.response.edit_message(view=self.view)
        await self.view.add_oracle_button(self.buttons)

        DiscordEventLogEntry.Add(self.view.ctx, "RouletteCandyButtonClick")


class OracleActionButton(discord.ui.Button["RouletteView"]):
    def __init__(
        self,
        label: str,
        result: str = "",
        comment: str = "",
        enabled: bool = True,
        emoji: str = None,
    ):
        super().__init__(label=label, style=discord.ButtonStyle.secondary, emoji=emoji)
        self.label = label
        self.result = result
        self.comment = comment
        self.disabled = not enabled

    async def callback(self, interaction: discord.Interaction) -> None:
        if interaction.user != self.view.ctx.author:
            await interaction.response.send_message(
                __("You are not authorized to use this button."), ephemeral=True
            )
            return

        self.style = discord.ButtonStyle.primary
        self.view.disable_all_buttons_in_rows()
        await interaction.response.edit_message(view=self.view)

        if self.result:
            await self.view.update_oracle_result(self.result, self.comment)
        else:
            await interaction.response.send_message(
                __("No result available for this button."), ephemeral=True
            )
            return

        DiscordEventLogEntry.Add(
            self.view.ctx,
            "RouletteOracleButtonClick",
            {
                "button_label": self.label,
                "result": self.result,
                "comment": self.comment,
            },
        )


class RouletteView(discord.ui.LayoutView):
    def __init__(self, ctx: commands.Context):
        super().__init__(timeout=60 * 5)
        self.ctx = ctx
        self.msg = None

        self.container = discord.ui.Container()
        self.header = discord.ui.TextDisplay("## Roulette")
        self.container.add_item(self.header)
        self.container.add_item(
            discord.ui.Separator(spacing=discord.SeparatorSpacing.large)
        )

        self.result = discord.ui.TextDisplay(
            f"### {Emoji.typing} {__('Lucky Pick')}\n{__('Preparing the roulette...')}"
        )

        self.container.add_item(self.result)
        self.container.add_item(
            discord.ui.Separator(spacing=discord.SeparatorSpacing.large)
        )

        self.choices = discord.ui.TextDisplay(
            f"### :clipboard: {__("Choices")}\n{Emoji.generating} Generating..."
        )

        self.container.add_item(self.choices)

        self.row = discord.ui.ActionRow()
        self.candy_button = OracleCandyButton(
            label=__("How do you feel?"),
            emoji="💬",
            enabled=False,
        )
        self.row.add_item(self.candy_button)
        self.oracle_msg = discord.ui.TextDisplay(
            __(
                """*You've already made the choice. You're here to understand why you've made it.*\n-# -The Oracle in The Matrix"""
            )
        )

        self.container.add_item(
            discord.ui.Separator(spacing=discord.SeparatorSpacing.large)
        )
        self.whisper = discord.ui.TextDisplay(
            f"### :woman_mage: {__("The Oracle's Whisper")}"
        )

        self.container.add_item(self.whisper)
        self.container.add_item(self.row)
        self.container.add_item(self.oracle_msg)

        self.container.add_item(
            discord.ui.Separator(spacing=discord.SeparatorSpacing.small)
        )

        footer = discord.ui.TextDisplay(
            "-# "
            + __("MK Bot uses AI. Check for mistakes.")
            + (
                (
                    " "
                    + "[{0}](https://discord.gg/3RpDwjJCeZ)".format(
                        __("Give Feedback ▷")
                    )
                )
                if CONFIG.showFeedbackLink
                else ""
            )
        )

        self.container.add_item(footer)

        self.add_item(self.container)

    def set_message(self, msg: discord.Message):
        self.msg = msg

    async def edit_message(self):
        await self.msg.edit(view=self)

    async def update_title_and_choices(self, title: str, choices: list[str]):
        self.header.content = f"## Roulette\n{title}"
        choices_str = ", ".join(
            choice if is_discord_special_string(choice) else f"`{choice}`"
            for choice in choices
        )
        self.choices.content = f"### :clipboard: {__('Choices')}\n{choices_str}"

        self.result.content = (
            f"### {Emoji.loading} {__('Lucky Pick')}\n{__('Roulette is running.')}"
        )

        await self.countdown(__("Lucky Pick"))

    async def countdown(self, result_title: str):
        for i in range(5, 0, -1):
            self.result.content = (
                f"### {Emoji.loading} {result_title}\n"
                f"{__('Roulette is running.')} {__('%dsec left') % i}"
            )
            await self.edit_message()
            await asyncio.sleep(1)

    async def update_oracle_result(self, result, comment: str = ""):
        result_title = __("The Oracle's Pick")

        self.result.content = (
            f"### {Emoji.loading} {result_title}\n{__('Roulette is running.')}"
        )

        await self.countdown(result_title)

        await self.update_result(f":crystal_ball: {result_title}", result, comment)

    async def update_result(self, result_title: str, result: str, comment: str = ""):

        if is_discord_special_string(result):
            base_content = f"### {result_title}\n### {result}"
        else:
            base_content = f"### {result_title}\n## ```{result}```"

        if comment:
            self.result.content = base_content + f"\n{Emoji.generating} Generating..."

        await self.edit_message()

        if comment:
            self.result.content = base_content + f"\n{Emoji.GenAI} {comment}"

            await self.edit_message()

    async def update_header(self, title: str):
        self.header.content = f"## Roulette\n{title}"
        await self.edit_message()

    async def enable_candy_button(self, buttons: list[OracleActionButton]):
        if buttons:
            self.candy_button.disabled = False
            self.candy_button.label = __("Candy?")
            self.candy_button.emoji = "🍬"
            self.candy_button.add_buttons(buttons)
            await self.edit_message()

    async def add_oracle_button(self, buttons: list[OracleActionButton]) -> None:
        await asyncio.sleep(1)

        self.row.clear_items()

        if buttons:
            for button in buttons:
                self.row.add_item(button)

        await self.edit_message()

    def disable_all_buttons_in_rows(self):
        for button in self.row.children:
            button.disabled = True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        await self.edit_message()


@commands.hybrid_command(aliases=["rou"])
@app_commands.describe(items=locale_str("Ask anything"))
@MGCertificate.verify(level=Level.TRUSTED_USERS)
@Feature.Experiment()
@related_commands(["dice", "lotto", "poll"])
async def roulette(ctx: commands.Context, *, items: str):
    """
    Play roulette

    Examples:
    {commandPrefix}roulette @user1 @user2 @user3
    {commandPrefix}rou "item 1" "item 2"

    Note:
    This bot cannot be added to items.
    """
    if gemini_enabled:
        ai_generating_task = asyncio.create_task(
            get_gemini_response(
                """You are an assistant that creates a roulette based on a user's input.

                    Here is a natural-language input that the user gives:
                    """
                + f'"{items}"'
                + """
                    Based on that, follow these steps carefully:

                    1. Analyze the user's input and generate a clear and accurate question-style title that reflects the user's intent. The title should be phrased as a yes/no or choice-based short question, depending on the input. Do not try to be witty or funny—just be clear and relevant.

                    2. Extract distinct and relevant options from the input. Be creative if needed.

                    3. Randomly select one of the options as the roulette result.

                    4. Based on the result, write a witty and humorous comment in the **same language as the user_input**. The comment should be playful but not too light—it should also carry a subtle sense of meaning, reflection, or depth. Keep it under 2–3 sentences.

                    5. If the user might not be satisfied with the result, generate up to 3 alternative "message button" texts that represent possible different intentions the user could have had.
                        - Do NOT simply repeat or directly mention the option text.
                        - Instead, phrase each button naturally as a short sentence that reflects a mood, situation, or feeling.
                        - Each button must still map to one of the available options via "result".
                        - Provide a witty and meaningful comment for each alternative result, in the **same language as the user_input**.

                    Your final response must be a JSON object with the following structure:

                    ```json
                    {
                        "title": "string",                // The title of the roulette
                        "options": ["string", ...],       // The list of choices
                        "result": "string",               // The selected choice
                        "comment": "string",              // A witty yet slightly meaningful reaction
                        "alternatives": [                 // Up to 3 alternative choices
                            {
                                "button": "string",       // Expresses the user's inner thought, not the option directly
                                "result": "string",       // The option selected if this button is chosen
                                "comment": "string"       // Witty yet slightly meaningful reaction for this alternative
                            }
                        ]
                    }
                    ```

                    Only return the JSON. Do not include any explanation or extra text outside of the JSON."""
            )
        )

        view = RouletteView(ctx)
        msg = await ctx.send(view=view)

        view.set_message(msg)

        ai_response = await ai_generating_task

        if ai_response:
            ai_response = re.sub(r"^```json\n|\n```$", "", ai_response.strip())
            try:
                data = json.loads(ai_response)
            except json.JSONDecodeError:
                log.error("Failed to parse AI response:\n%s", ai_response)
                data = None
                await ctx.send(
                    embed=MsgFormatter.get(
                        ctx,
                        __("AI response error"),
                        __("Failed to parse AI response. Please try again later."),
                    )
                )
                return

            title = data["title"]
            item_ls = data["options"]
            result = data["result"]
            ai_comment = data["comment"]
            alternatives = data.get("alternatives", [])

            await view.update_title_and_choices(title, item_ls)

            await view.update_result(f':dart: {__("Lucky Pick")}', result, ai_comment)
            await view.enable_candy_button(
                [
                    OracleActionButton(
                        button["button"], button["result"], button["comment"]
                    )
                    for button in alternatives
                ]
            )

            DiscordEventLogEntry.Add(
                ctx,
                "RouletteResult",
                {
                    "result": result,
                    "items": item_ls,
                    "ai_response": ai_response,
                },
            )

            return

    item_ls = shlex.split(items)
    result = random.choice(item_ls)

    if len(item_ls) == 1:
        await ctx.send(
            embed=MsgFormatter.get(
                ctx,
                "Roulette",
                __("Only one item provided. No roulette needed."),
            )
        )
        return

    input_field = {
        "name": ":clipboard: " + __("Choices"),
        "value": ", ".join(
            item if is_discord_special_string(item) else f"`{item}`" for item in item_ls
        ),
        "inline": False,
    }

    description = f"{Emoji.GenAI} " + __(
        "AI comment is not available for this roulette."
    )

    output_field = {
        "name": Emoji.loading + " " + __("Lucky Pick"),
        "value": __("Roulette is running."),
        "inline": False,
    }

    embed = MsgFormatter.get(
        ctx,
        "Roulette",
        description=description,
        fields=[output_field, input_field],
    )

    msg: discord.Message = await ctx.send(embed=embed)

    async def countdown():
        for i in range(5, 0, -1):
            output_field["value"] = (
                __("Roulette is running.") + " " + __("%dsec left") % i
            )

            embed.set_field_at(0, **output_field)

            await msg.edit(embed=embed)
            await asyncio.sleep(1)

    countdown_task = asyncio.create_task(countdown())
    await countdown_task

    DiscordEventLogEntry.Add(
        ctx,
        "RouletteResult",
        {"result": result, "items": item_ls, "ai_response": None},
    )

    output_field["name"] = ":dart: " + __("Lucky Pick")
    output_field["value"] = (
        result if is_discord_special_string(result) else f"```{result}```"
    )

    embed.set_field_at(0, **output_field)

    await msg.edit(embed=embed)


# @register_intent("command::roulette", "roulette")
# def cmd_roulette(intent: Intent):
#     if items := intent.get_an_entity("items"):
#         items: str
#         items = [i.strip() for i in items.split(",")]
#         return "roulette " + " ".join(f'"{i}"' for i in items)
#     else:
#         return None


async def setup(bot: commands.Bot):
    bot.add_command(roulette)
