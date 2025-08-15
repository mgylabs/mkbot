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

                    4. Based on the result, write a witty, and humorous comment in Korean reacting to the selected option. Make it sound spontaneous, playful, and fun. Keep it under 2-3 sentences.

                    Your final response must be a JSON object with the following structure:

                    json
                    ```
                    {
                        "title": "string",               // The title of the roulette
                        "options": ["string", ...],      // The list of choices
                        "result": "string",              // The selected choice
                        "comment": "string"              // A witty and fun reaction to the result
                    }
                    ```

                    Only return the JSON. Do not include any explanation or extra text outside of the JSON."""
            )
        )

        input_field = {
            "name": ":clipboard: " + __("Choices"),
            "value": f"{Emoji.generating} Generating...",
            "inline": False,
        }

        description = ""

        output_field = {
            "name": Emoji.typing + " " + __("Lucky Pick"),
            "value": __("Preparing the roulette..."),
            "inline": False,
        }

    else:
        item_ls = shlex.split(items)
        result = random.choice(item_ls)

        if len(item_ls) == 1:
            await ctx.send(
                embed=MsgFormatter.get(
                    ctx,
                    "Roulette `✨BETA`",
                    __("Only one item provided. No roulette needed."),
                )
            )
            return

        input_field = {
            "name": ":clipboard: " + __("Choices"),
            "value": ", ".join(
                item if is_discord_special_string(item) else f"`{item}`"
                for item in item_ls
            ),
            "inline": False,
        }

        description = f"{Emoji.GenAI} " + __(
            "AI comment is not available for this roulette."
        )

        output_field = {
            "name": Emoji.typing + " " + __("Lucky Pick"),
            "value": __("Roulette is running."),
            "inline": False,
        }

    embed = MsgFormatter.get(
        ctx,
        "Roulette `✨BETA`",
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

    ai_response = None
    result = None
    ai_comment = ""

    if gemini_enabled:
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

            embed.description = title
            input_field["value"] = ", ".join(
                item if is_discord_special_string(item) else f"`{item}`"
                for item in item_ls
            )

            embed.set_field_at(1, **input_field)

            embed.set_footer(
                text=__("MK Bot can make mistakes. Check important info."),
            )
        else:
            embed.description = f"{Emoji.GenAI} " + __(
                "AI comment is not available for this roulette."
            )

            item_ls = shlex.split(items)
            result = random.choice(item_ls)

            input_field["value"] = ", ".join(
                item if is_discord_special_string(item) else f"`{item}`"
                for item in item_ls
            )

    countdown_task = asyncio.create_task(countdown())
    await countdown_task

    DiscordEventLogEntry.Add(
        ctx,
        "RouletteResult",
        {"result": result, "items": item_ls, "ai_response": ai_response},
    )

    if ai_response:
        output_field["name"] = ":dart: " + __("Lucky Pick")
        output_field["value"] = (
            result if is_discord_special_string(result) else f"```{result}```"
        ) + f"\n{Emoji.generating} Generating..."

        embed.set_field_at(0, **output_field)

        await msg.edit(embed=embed)

        output_field["value"] = (
            result
            if is_discord_special_string(result)
            else f"```{result}```" + f"\n{Emoji.GenAI} {ai_comment}"
        )

        await asyncio.sleep(1)
    else:
        output_field["name"] = ":dart: " + __("Lucky Pick")
        output_field["value"] = (
            result if is_discord_special_string(result) else f"```{result}```"
        )

    embed.set_field_at(0, **output_field)
    embed.set_field_at(1, **input_field)

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
