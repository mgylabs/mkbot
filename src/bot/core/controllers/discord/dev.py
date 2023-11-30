import ast
import asyncio
import copy
import inspect
import io
import re
import textwrap
import traceback
from contextlib import redirect_stdout
from typing import Any, Optional, Union

import aiohttp
import discord
from discord.ext import commands

from mgylabs.i18n import __
from mgylabs.utils.config import is_development_mode

START_CODE_BLOCK_RE = re.compile(r"^((```py(thon)?)(?=\s)|(```))")


class Dev(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self._last_result: Optional[Any] = None
        self.sessions: set[int] = set()

    async def cog_check(self, ctx: commands.Context) -> bool:
        return await self.bot.is_owner(ctx.author)

    @staticmethod
    def async_compile(source, filename, mode):
        return compile(source, filename, mode, flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)

    def cleanup_code(self, content: str) -> str:
        # """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith("```") and content.endswith("```"):
            return START_CODE_BLOCK_RE.sub("", content)[:-3]

        # remove `foo`
        return content.strip("` \n")

    def get_syntax_error(self, e: SyntaxError) -> str:
        if e.text is None:
            return f"```py\n{e.__class__.__name__}: {e}\n```"
        return f'```py\n{e.text}{"^":>{e.offset}}\n{e.__class__.__name__}: {e}```'

    def get_environment(self, ctx: commands.Context) -> dict:
        env = {
            "bot": ctx.bot,
            "ctx": ctx,
            "guild": ctx.guild,
            "channel": ctx.channel,
            "message": ctx.message,
            "author": ctx.author,
            "_": self._last_result,
            "asyncio": asyncio,
            "aiohttp": aiohttp,
            "discord": discord,
            "__name__": "__main__",
        }

        return env

    @commands.command(hidden=False, name="eval")
    @commands.is_owner()
    async def _eval(self, ctx: commands.Context, *, body: str):
        """
        Evaluates a code.

        Environment Variables:
            `ctx`      - the command invocation context
            `bot`      - the bot object
            `guild`    - the current guild object
            `channel`  - the current channel object
            `message`  - the command's message object
            `author`   - the command author's member object
            `_`        - the result of the last dev command
            `aiohttp`  - the aiohttp library
            `asyncio`  - the asyncio library
            `discord`  - the discord.py library
        """

        env = self.get_environment(ctx)

        body = self.cleanup_code(body)
        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        try:
            exec(to_compile, env)
        except Exception as e:
            try:
                await ctx.message.add_reaction("🔴")
            except Exception:
                pass

            return await ctx.send(f"```py\n{e.__class__.__name__}: {e}\n```")

        func = env["func"]
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception:
            value = stdout.getvalue()

            try:
                await ctx.message.add_reaction("🔴")
            except Exception:
                pass

            await ctx.send(f"```py\n{value}{traceback.format_exc()}\n```")
        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction("🟢")
            except Exception:
                pass

            if ret is None:
                if value:
                    await ctx.send(f"```py\n{value}\n```")
            else:
                self._last_result = ret
                await ctx.send(f"```py\n{value}{ret}\n```")

    @commands.command(hidden=False)
    @commands.is_owner()
    async def repl(self, ctx: commands.Context):
        """
        Launches an interactive REPL session.

        The REPL will only recognise code as messages which start with a backtick.
        This includes codeblocks, and as such multiple lines can be evaluated.

        Use `exit()` or `quit` to exit the REPL session, prefixed with a backtick so they may be interpreted.

        Environment Variables:
            `ctx`      - the command invocation context
            `bot`      - the bot object
            `guild`    - the current guild object
            `channel`  - the current channel object
            `message`  - the command's message object
            `author`   - the command author's member object
            `_`        - the result of the last dev command
            `aiohttp`  - the aiohttp library
            `asyncio`  - the asyncio library
            `discord`  - the discord.py library
        """
        env = self.get_environment(ctx)
        env["_"] = None

        if ctx.channel.id in self.sessions:
            await ctx.send(
                __(
                    "Already running a REPL session in this channel. Exit it with `quit`."
                )
            )
            return

        self.sessions.add(ctx.channel.id)
        await ctx.send(
            __("Enter code to execute or evaluate. `exit()` or `quit` to exit.")
        )

        def check(m):
            return (
                m.author.id == ctx.author.id
                and m.channel.id == ctx.channel.id
                and m.content.startswith("`")
            )

        while True:
            try:
                response = await self.bot.wait_for(
                    "message", check=check, timeout=10.0 * 60.0
                )
            except asyncio.TimeoutError:
                await ctx.send(__("Exiting REPL session."))
                self.sessions.remove(ctx.channel.id)
                break

            cleaned = self.cleanup_code(response.content)

            if cleaned in ("quit", "exit", "exit()"):
                await ctx.send(__("Exiting."))
                self.sessions.remove(ctx.channel.id)
                return

            executor = exec
            if cleaned.count("\n") == 0:
                # single statement, potentially 'eval'
                try:
                    code = self.async_compile(cleaned, "<repl session>", "eval")
                except SyntaxError:
                    pass
                else:
                    executor = eval

            if executor is exec:
                try:
                    code = self.async_compile(cleaned, "<repl session>", "exec")
                except SyntaxError as e:
                    try:
                        await response.add_reaction("🔴")
                    except Exception:
                        pass

                    await ctx.send(self.get_syntax_error(e))
                    continue

            env["message"] = response

            fmt = None
            stdout = io.StringIO()

            try:
                with redirect_stdout(stdout):
                    result = executor(code, env)
                    if inspect.isawaitable(result):
                        result = await result
            except Exception:
                value = stdout.getvalue()

                try:
                    await response.add_reaction("🔴")
                except Exception:
                    pass

                fmt = f"```py\n{value}{traceback.format_exc()}\n```"
            else:
                value = stdout.getvalue()

                try:
                    await response.add_reaction("🟢")
                except Exception:
                    pass

                if result is not None:
                    fmt = f"```py\n{value}{result}\n```"
                    env["_"] = result
                elif value:
                    fmt = f"```py\n{value}\n```"

            try:
                if fmt is not None:
                    if len(fmt) > 2000:
                        await ctx.send(__("Content too big to be printed."))
                    else:
                        await ctx.send(fmt)
            except discord.Forbidden:
                pass
            except discord.HTTPException as e:
                await ctx.send("Unexpected error: `{error}`".format(error=e))

    @commands.command(hidden=False)
    @commands.is_owner()
    async def sudo(
        self,
        ctx: commands.Context,
        channel: Optional[discord.TextChannel],
        who: Union[discord.Member, discord.User],
        *,
        command: str,
    ):
        """Run a command as another user optionally in another channel."""
        msg = copy.copy(ctx.message)
        new_channel = channel or ctx.channel
        msg.channel = new_channel
        msg.author = who
        msg.content = ctx.prefix + command
        new_ctx = await self.bot.get_context(msg, cls=type(ctx))
        await self.bot.invoke(new_ctx)

    @commands.group(invoke_without_command=True)
    @commands.is_owner()
    @commands.guild_only()
    async def sync(
        self, ctx: commands.Context, guild_id: Optional[int], copy: bool = True
    ) -> None:
        """Syncs the slash commands with the given guild"""

        if guild_id:
            guild = discord.Object(id=guild_id)
        else:
            guild = ctx.guild

        async with ctx.typing():
            if copy:
                self.bot.tree.copy_global_to(guild=guild)

            commands = await self.bot.tree.sync(guild=guild)

        await ctx.send(f"Successfully synced {len(commands)} commands")

    @sync.command(name="global")
    @commands.is_owner()
    async def sync_global(self, ctx: commands.Context):
        """Syncs the commands globally"""
        async with ctx.typing():
            commands = await self.bot.tree.sync(guild=None)
        await ctx.send(f"Successfully synced {len(commands)} commands")


async def setup(bot: commands.Bot):
    """Dev"""

    if is_development_mode(False):
        await bot.add_cog(Dev(bot))
