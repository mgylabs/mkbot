import asyncio
import os
import re
import sys

sys.path.append("..\\lib")

import platform
import threading
import time
import traceback
import urllib.parse

import discord
from discord import ButtonStyle, Locale
from discord.app_commands import (
    CommandTree,
    TranslationContextTypes,
    Translator,
    locale_str,
)
from discord.ext import commands, tasks
from discord.ui import Button, View

import views
from command_help import CommandHelp
from core.controllers.discord.utils import api
from core.controllers.discord.utils.exceptions import NonFatalError, UsageError
from core.controllers.discord.utils.MGCert import MGCertificate
from core.controllers.discord.utils.MsgFormat import MsgFormatter
from discord_ext import discord_extensions
from mgylabs.db.database import run_migrations
from mgylabs.db.paths import DB_URL, SCRIPT_DIR
from mgylabs.i18n import _
from mgylabs.i18n.extension import I18nExtension
from mgylabs.i18n.utils import get_user_locale_code, init_user_locale
from mgylabs.services.telemetry_service import TelemetryReporter
from mgylabs.utils import logger
from mgylabs.utils.config import CONFIG, MGCERT_PATH, VERSION, is_development_mode
from mgylabs.utils.helper import usage_helper
from mgylabs.utils.LogEntry import DiscordRequestLogEntry
from release import ReleaseNotify

log = logger.get_logger(__name__)
i18n = I18nExtension()


async def interaction_check(self, interaction: discord.Interaction, /) -> bool:
    i18n.set_current_locale(get_user_locale_code(interaction.user.id))

    return True


discord.ui.View.interaction_check = interaction_check


class BotStateFlags:
    online = False
    terminate = False

    class Terminate:
        def __enter__(self):
            BotStateFlags.terminate = True

        def __exit__(self, exc_type, exc_value, traceback):
            BotStateFlags.terminate = False


class MKBotContext(commands.Context):
    pass


class MKBotCommandTree(CommandTree):
    async def interaction_check(self, interaction: discord.Interaction, /) -> bool:
        i18n.set_current_locale(get_user_locale_code(interaction.user.id))
        return await super().interaction_check(interaction)


class MKBotTranslator(Translator):
    async def translate(
        self, string: locale_str, locale: Locale, context: TranslationContextTypes
    ):
        try:
            result = i18n.gettext(str(string), locale.value, False)  # @IgnoreException
        except Exception:
            result = None

        return result


class MKBot(commands.Bot):
    async def process_commands(self, request_id, message):
        if message.author.bot:
            return
        ctx = await self.get_context(message)
        ctx.mkbot_request_id = request_id
        await self.invoke(ctx)

    async def get_context(self, message, *, cls=MKBotContext):
        return await super().get_context(message, cls=cls)


async def create_bot(return_error_level=False):
    stime = time.time()
    errorlevel = 0
    pending = True

    if is_development_mode():
        name = "IN DEBUG" if "--debug" in sys.argv else "IN DEV"
        activity_type = discord.ActivityType.playing
    elif VERSION == None:
        name = "MK Bot Test Mode"
        activity_type = discord.ActivityType.playing
    elif CONFIG.connectOnStart:
        name = f"MK Bot {VERSION}"
        activity_type = discord.ActivityType.listening
        pending = False
    else:
        name = f"{CONFIG.commandPrefix}help"
        activity_type = discord.ActivityType.listening

    activity = discord.Activity(name=name, type=activity_type)

    intent = discord.Intents.all()
    replyformat = MsgFormatter()
    bot = MKBot(
        command_prefix=CONFIG.commandPrefix,
        intents=intent,
        help_command=CommandHelp(replyformat),
        activity=activity,
        tree_cls=MKBotCommandTree,
    )
    cert = MGCertificate(MGCERT_PATH)
    bot.__dict__.update({"MGCert": cert, "replyformat": replyformat})

    i18n.init_bot(bot, lambda ctx: get_user_locale_code(ctx.author.id))

    @bot.event
    async def on_ready():
        TelemetryReporter.start("Login")

        print("Logged in within {:0.2f}s".format(time.time() - stime))

        bot.tree.on_error = on_app_command_error
        await bot.tree.set_translator(MKBotTranslator())
        replyformat.set_avatar_url(
            "https://cdn.discordapp.com/avatars/698478990280753174/6b71c165ba779edc2a7c73f074a51ed5.png?size=20"
        )

        for guild in CONFIG.discordAppCmdGuilds:
            bot.tree.copy_global_to(guild=discord.Object(guild))
            cmds = await bot.tree.sync(guild=discord.Object(guild))
            print(f"App commands sync for {guild} ({', '.join(c.name for c in cmds)})")

    @bot.event
    async def on_message(message: discord.Message):
        if message.author == bot.user:
            return

        if (message.channel.type.value == 1) and (CONFIG.disabledPrivateChannel):
            return

        if bot.user.mentioned_in(message) and cert.isAdminUser(str(message.author)):
            text = re.sub("<@!?\\d+> ", "", message.content)
            if text.lower() == "ping":
                await message.channel.send(
                    f"{message.author.mention}  Pong: {round(bot.latency*1000)}ms"
                )
        else:
            ctx: commands.Context = await bot.get_context(message)

            request_id = None
            if ctx.command is not None:
                request_id = DiscordRequestLogEntry.add(
                    ctx, message, MGCertificate.getUserLevel(str(message.author))
                )

                if get_user_locale_code(message.author.id) is None:
                    dv = views.LanguageSettingView(message.author.id)

                    dv.message = await ctx.send(
                        embed=MsgFormatter.get(
                            ctx,
                            "Mulgyeol MK Bot Display Language",
                            "To continue, set the your language that Mulgyeol MK Bot features appear in.",
                        ),
                        view=dv,
                    )

                    if await dv.wait():
                        return

            await bot.process_commands(request_id, message)

            nonlocal pending
            if message.content.startswith(bot.command_prefix):
                if pending:
                    pending = False
                    name = f"MK Bot {VERSION}"
                    activity = discord.Activity(
                        name=name, type=discord.ActivityType.listening
                    )
                    await bot.change_presence(
                        status=discord.Status.online, activity=activity
                    )

                await ReleaseNotify.run(message.author.id, message.channel.send)

    @bot.event
    async def on_command_error(ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, NonFatalError):
            log.debug(str(error))
            return

        if isinstance(error, commands.MaxConcurrencyReached):
            await ctx.send(
                embed=MsgFormatter.get(
                    ctx,
                    f"Max Concurrency Reached: {ctx.command.name}",
                    "Too many people using this command. Please retry in a minute.",
                )
            )
            return

        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(
                embed=MsgFormatter.get(
                    ctx, f"Command On Cooldown: {ctx.command.name}", str(error)
                )
            )
            return

        if isinstance(error, UsageError):
            await ctx.send(
                embed=MsgFormatter.get(
                    ctx, f"Usage Error: {ctx.command.name}", str(error)
                )
            )
            return

        if isinstance(error, commands.CommandInvokeError):
            tb = "".join(traceback.format_exception(None, error, error.__traceback__))[
                :1700
            ]

            tb = tb.split(
                "The above exception was the direct cause of the following exception:"
            )[0].strip()

            query_str = urllib.parse.urlencode(
                {
                    "template": "bug_report.yml",
                    "labels": "bug,Needs-Triage",
                    "title": str(error).replace(
                        "Command raised an exception:", f"[{ctx.command.name}]"
                    ),
                    "version": f"{VERSION} ({VERSION.commit})",
                    "os_version": platform.platform()
                    .replace("-", " ")
                    .replace("SP0", ""),
                }
            )

            issue_link = f"https://github.com/mgylabs/mkbot/issues/new?{query_str}"

            view = View()
            view.add_item(
                Button(label=_("Report Issue"), style=ButtonStyle.url, url=issue_link)
            )
            await ctx.send(embed=MsgFormatter.abrt(ctx, issue_link, tb), view=view)
            raise error

        await ctx.send(
            embed=MsgFormatter.get(
                ctx, _("Command Error: %s") % ctx.command.name, str(error)
            )
        )

    async def on_app_command_error(
        interaction: discord.Interaction,
        error: discord.app_commands.AppCommandError,
    ):
        command = interaction.command
        if command is not None:
            if command._has_any_error_handlers():
                return

            print(f"Ignoring exception in command {command.name!r}:", file=sys.stderr)

            ###
            if isinstance(error, discord.app_commands.CommandInvokeError):
                tb = "".join(
                    traceback.format_exception(None, error, error.__traceback__)
                )[:1700]

                tb = tb.split(
                    "The above exception was the direct cause of the following exception:"
                )[0].strip()

                query_str = urllib.parse.urlencode(
                    {
                        "template": "bug_report.yml",
                        "labels": "bug,Needs-Triage",
                        "title": str(error).replace(
                            "Command raised an exception:",
                            f"[{interaction.data['name']}]",
                        ),
                        "version": f"{VERSION} ({VERSION.commit})",
                        "os_version": platform.platform()
                        .replace("-", " ")
                        .replace("SP0", ""),
                    }
                )

                issue_link = f"https://github.com/mgylabs/mkbot/issues/new?{query_str}"
                view = View()
                view.add_item(
                    Button(
                        label=_("Report Issue"), style=ButtonStyle.url, url=issue_link
                    )
                )
                await interaction.response.send_message(
                    embed=MsgFormatter.abrt(interaction, issue_link, tb), view=view
                )
                raise error

            await interaction.response.send_message(
                embed=MsgFormatter.get(
                    interaction,
                    f"Command Error: {interaction.command.name}",
                    str(error),
                )
            )
        else:
            print("Ignoring exception in command tree:", file=sys.stderr)

        traceback.print_exception(
            error.__class__, error, error.__traceback__, file=sys.stderr
        )

    @bot.event
    async def on_interaction(interaction: discord.Interaction):
        if interaction.user.bot:
            return

        if interaction.type == discord.InteractionType.application_command:
            DiscordRequestLogEntry.add_for_iaction(
                interaction, MGCertificate.getUserLevel(str(interaction.user))
            )

            if language := init_user_locale(interaction):
                i18n.set_current_locale(str(interaction.locale))
                await interaction.client.get_channel(interaction.channel_id).send(
                    embed=MsgFormatter.get(
                        interaction,
                        _("Your display language has been changed to %s.") % language,
                        _(
                            "Type `/language set` or `{commandPrefix}language set` to change your display language."
                        ),
                    )
                )
            else:
                i18n.set_current_locale(get_user_locale_code(interaction.user.id))

            await ReleaseNotify.run(
                interaction.user.id,
                interaction.client.get_channel(interaction.channel_id).send,
            )

    @tasks.loop(seconds=5.0)
    async def flag_checker():
        if BotStateFlags.terminate:
            print(BotStateFlags.terminate)
            await bot.close()

    @tasks.loop(minutes=10)
    async def usage():
        usage_helper()

    for i in discord_extensions:
        try:
            await bot.load_extension(i)
        except Exception:
            traceback.print_exc()
            if i != "core.install":
                errorlevel += 1

    try:
        exts = api.get_enabled_extensions()
        for i in exts:
            if is_development_mode():
                sys.path.append(f"..\\..\\extensions\\{i[0]}")
            else:
                sys.path.append(
                    os.getenv("USERPROFILE") + f"\\.mkbot\\extensions\\{i[0]}"
                )
            await bot.load_extension(i[1])
    except Exception:
        traceback.print_exc()

    flag_checker.start()
    usage.start()

    print("Mulgyeol MK Bot")
    print(f"Version {VERSION}" if VERSION != None else "Test Mode")
    print("Copyright (c) 2022 Mulgyeol Labs. All rights reserved.\n")
    print(f"{time.strftime('%a, %d %b %Y %H:%M:%S (GMT%z)', time.localtime())}\n")

    return bot if not return_error_level else errorlevel


def get_event_loop():
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    else:
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    return loop


async def start_bot():
    bot = await create_bot()

    async with bot:
        await bot.start(CONFIG.discordToken)

    loop = asyncio.get_event_loop()
    loop.stop()


class DiscordBotManger(threading.Thread):
    def __init__(self, callback):
        super().__init__()
        self.daemon = True
        self.callback = callback

    def run(self):
        exit_code = 0
        try:
            CONFIG.load()
            get_event_loop()
            asyncio.run(start_bot())
            usage_helper()
        except discord.errors.LoginFailure as e:
            log.critical(e)
            exit_code = 1
        except Exception as e:
            traceback.print_exc()
            log.critical(e)

        BotStateFlags.online = False
        self.callback(exit_code)


if __name__ == "__main__":
    run_migrations(SCRIPT_DIR, DB_URL)
    asyncio.run(start_bot())
