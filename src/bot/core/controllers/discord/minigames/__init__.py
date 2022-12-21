from __future__ import annotations

from typing import Dict

import discord
from discord import app_commands
from discord.ext import commands

from core.controllers.discord.minigames import battleship, gobblet
from core.controllers.discord.minigames.hangman import Hangman
from core.controllers.discord.utils import listener
from core.controllers.discord.utils.MGCert import Level, MGCertificate
from core.controllers.discord.utils.MsgFormat import MsgFormatter
from mgylabs.i18n import _
from mgylabs.utils import logger

log = logger.get_logger(__name__)


class Minigame(commands.GroupCog):
    """Simple minigames to play with others"""

    channels: Dict[int, Hangman] = {}

    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @property
    def display_emoji(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(name="\N{VIDEO GAME}", id=None)

    def __repr__(self) -> str:
        return "<cogs.Minigame>"

    @commands.Cog.listener()
    @listener.on_message()
    async def on_message(self, message: discord.Message):
        if len(self.channels) == 0:
            return

        ctx: commands.Context = await self.bot.get_context(message)

        if ctx.channel.id not in self.channels:
            return

        await message.delete()

        log.debug(message.content)

        hangman = self.channels[ctx.channel.id]

        input_letter = message.content[0].upper()

        letter_state = hangman.checkLetter(input_letter)

        hangman.respondToLetter(input_letter, letter_state)

        game_state = hangman.checkGameState()

        ds = f"{hangman.displayScreen()}\n{letter_state}"
        log.debug(ds)
        await hangman.send(ds)

        if game_state != "PLAYING":
            self.channels.pop(ctx.channel.id)
            ds = f"{hangman.displayScreen()}\n{hangman.displayGameResult(game_state)}"
            log.debug(ds)
            await hangman.send(ds)

    @commands.hybrid_command()
    @commands.guild_only()
    @app_commands.guild_only()
    @app_commands.rename(other="with")
    @app_commands.describe(other="The opponent to play with")
    @MGCertificate.verify(level=Level.TRUSTED_USERS)
    async def gobblet(self, ctx: commands.Context, *, other: discord.Member):
        """Play a game of Gobblet Gobblers with someone else"""
        if other.bot:
            return await ctx.send(_("You cannot play against a bot"), ephemeral=True)

        prompt = gobblet.Prompt(ctx.author, other)
        msg = await ctx.send(
            _(
                "%(other)s has been challenged to a game of Gobblet Gobblers by %(author)s.\n"
                "This is a game similar to Tic-Tac-Toe except each piece has an associated strength with it. "
                "A higher strength value eats a piece even if it's already on the board. "
                "Careful, you only have 1 piece of each strength value!\n\n"
                "Do you accept this challenge, %(other)s?"
            )
            % {"other": other.mention, "author": ctx.author.mention},
            view=prompt,
        )

        await prompt.wait()
        await msg.delete(delay=10)

    @commands.hybrid_command()
    @commands.guild_only()
    @app_commands.guild_only()
    @app_commands.rename(other="with")
    @app_commands.describe(other="The opponent to play with")
    @MGCertificate.verify(level=Level.TRUSTED_USERS)
    async def battleship(self, ctx: commands.Context, *, other: discord.Member):
        """Play a game of battleship with someone else"""
        if other.bot:
            return await ctx.send("You cannot play against a bot", ephemeral=True)

        prompt = battleship.Prompt(ctx.author, other)
        prompt.message = await ctx.send(
            f"{other.mention} has been challenged to a game of Battleship by {ctx.author.mention}.\n"
            f"In order to accept, please press your button below to ready up.",
            view=prompt,
        )
        prompt.message = await ctx.send(
            _(
                "%(other)s has been challenged to a game of Battleship by %(author)s.\n"
                "In order to accept, please press your button below to ready up."
            )
            % {"other": other.mention, "author": ctx.author.mention},
            view=prompt,
        )

    @commands.hybrid_command()
    @app_commands.choices(
        command=[
            app_commands.Choice(name="start", value="start"),
            app_commands.Choice(name="exit", value="exit"),
        ]
    )
    @MGCertificate.verify(level=Level.TRUSTED_USERS)
    async def hangman(
        self,
        ctx: commands.Context,
        command: str = commands.parameter(
            default="start", description="`start` or `exit`"
        ),
    ):
        """
        Play a game of Hangman

        {commandPrefix}hangman
        {commandPrefix}hangman exit
        """

        command = command.lower()

        if command == "start":
            pass
        elif command == "exit":
            channel_id = ctx.channel.id

            if channel_id in self.channels:
                self.channels.pop(channel_id)

            await ctx.send(
                embed=MsgFormatter.get(ctx, _("Hangman"), _("Exit Hangman Game"))
            )
            return
        else:
            await ctx.send(
                embed=MsgFormatter.get(ctx, _("Hangman"), _("Invalid Argument"))
            )
            return

        hangman = Hangman()
        hangman.initialiseVariables()

        ds = hangman.displayScreen()
        log.debug(ds)
        message = await ctx.send(
            embed=MsgFormatter.get(ctx, _("Hangman"), f"```{ds}```")
        )

        async def display(text):
            await message.edit(
                embed=MsgFormatter.get(ctx, _("Hangman"), f"```{text}```")
            )

        hangman.send = display

        self.channels[ctx.channel.id] = hangman


async def setup(bot: commands.Bot):
    """
    Minigame
    """
    await bot.add_cog(Minigame(bot))
