import asyncio
import random
import re
import shlex

import discord
from discord import app_commands
from discord.app_commands import locale_str
from discord.ext import commands

from mgylabs.i18n import __
from mgylabs.utils.LogEntry import DiscordEventLogEntry

from .utils.emoji import Emoji
from .utils.gemini import get_gemini_response
from .utils.MGCert import Level, MGCertificate
from .utils.MsgFormat import MsgFormatter, related_commands


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
@app_commands.describe(items=locale_str('item1 "item 2" "item3" ...'))
@MGCertificate.verify(level=Level.TRUSTED_USERS)
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
    item_ls = shlex.split(items)

    result = random.choice(item_ls)

    if not item_ls:
        await ctx.send(
            embed=MsgFormatter.get(
                ctx, "Roulette `BETA`", __("No items provided for roulette.")
            )
        )
        return

    if len(item_ls) == 1:
        await ctx.send(
            embed=MsgFormatter.get(
                ctx,
                "Roulette `BETA`",
                __("Only one item provided. No roulette needed."),
            )
        )
        return

    ai_comment_task = asyncio.create_task(
        get_gemini_response(
            "\n".join(
                [
                    "You are a witty commentator. Here is a list of roulette items: ",
                    ", ".join(item_ls),
                    f" And the roulette result is: {result}",
                    "Based on this, write a short, clever, and humorous comment in Korean as if you are reacting live to the spin result. ",
                    "Make it sound spontaneous, playful, and fun. Keep it under 2-3 sentences.",
                ]
            )
        )
    )

    input_field = {
        "name": ":clipboard: " + __("Choices"),
        "value": "```mathematica\n"
        + "\n".join(f"{i+1}. {item}" for i, item in enumerate(item_ls))
        + "\n```",
        "inline": False,
    }

    output_field = {
        "name": ":dart: " + __("Lucky Pick"),
        "value": Emoji.typing,
        "inline": False,
    }

    embed = MsgFormatter.get(
        ctx,
        "Roulette `BETA`",
        __("Roulette is running. Please wait."),
        fields=[output_field, input_field],
    )

    msg: discord.Message = await ctx.send(embed=embed)

    for i in range(5, 0, -1):
        output_field["value"] = f"\n{Emoji.typing} " + __("%dsec left") % i + "\n\u2800"

        embed.set_field_at(0, **output_field)

        if i == 1:
            embed.description = f"{Emoji.gemini_generating} Generating..."

        await msg.edit(embed=embed)
        await asyncio.sleep(1)

    ai_comment = await ai_comment_task

    DiscordEventLogEntry.Add(
        ctx,
        "RouletteResult",
        {"result": result, "items": item_ls, "ai_comment": ai_comment},
    )

    if ai_comment:
        embed.description = f"{Emoji.google_gemini} " + ai_comment
    else:
        embed.description = f"{Emoji.google_gemini} " + __(
            "AI comment is not available for this roulette."
        )

    output_field["value"] = f"* {result}"
    input_field["value"] = "|| " + input_field["value"] + " ||"

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
