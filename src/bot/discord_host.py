import asyncio
import re
import sys

if __name__ == "__main__":
    sys.path.append("..\\lib")
    from mgylabs.utils import logger

    logger.configure_logger()

import platform
import threading
import time
import traceback
import urllib.parse
from contextlib import contextmanager

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
from mkbot_nlu.utils import Intent, register_intent

import views
from command_help import CommandHelp
from core.controllers.discord.utils import api
from core.controllers.discord.utils.exceptions import NonFatalError, UsageError
from core.controllers.discord.utils.MGCert import MGCertificate
from core.controllers.discord.utils.MsgFormat import MsgFormatter
from discord_ext import discord_extensions
from mgylabs.db import database
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
from mgylabs.utils.nlu import NluModel
from release import ReleaseNotify

log = logger.get_logger(__name__)
i18n = I18nExtension()

super_ui_scheduled_task = discord.ui.View._scheduled_task


@database.using_database
async def ui_scheduled_task(
    self, item: discord.ui.Item, interaction: discord.Interaction
):
    i18n.set_current_locale(get_user_locale_code(interaction.user.id))

    await super_ui_scheduled_task(self, item, interaction)


discord.ui.View._scheduled_task = ui_scheduled_task


@contextmanager
def using_nlu():
    if CONFIG.enabledChatMode:
        try:
            NluModel.load()
        except Exception:
            pass

    try:
        yield
    finally:
        NluModel.unload()


@register_intent("nlu_fallback", "fallback")
def cmd_fallback(intent: Intent):
    return f"google {intent.text}"


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
        return await super().interaction_check(interaction)

    def _from_interaction(self, interaction: discord.Interaction) -> None:
        with database.db_session():
            i18n.set_current_locale(get_user_locale_code(interaction.user.id))
            return super()._from_interaction(interaction)


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
    async def _run_event(self, coro, event_name: str, *args, **kwargs) -> None:
        with database.db_session():
            return await super()._run_event(coro, event_name, *args, **kwargs)

    async def check_init_user_locale(
        self, ctx: commands.Context, message: discord.Message
    ):
        if get_user_locale_code(message.author.id) is not None:
            return True

        dv = views.LanguageSettingView(message.author.id)

        dv.message = await ctx.reply(
            embed=MsgFormatter.get(
                ctx,
                "Mulgyeol MK Bot Display Language",
                "To continue, set your language that Mulgyeol MK Bot features appear in.",
            ),
            view=dv,
        )

        if await dv.wait():
            return False
        else:
            return True

    async def process_commands(self, request_id, message):
        if message.author.bot:
            return False

        ctx = await self.get_context(message)

        if not await self.check_init_user_locale(ctx, message):
            return False

        ctx.mkbot_request_id = request_id
        await self.invoke(ctx)

        return ctx.command is not None

    async def process_chats(self, ctx: commands.Context, message: discord.Message):
        if message.author.bot:
            return False

        if not await self.check_init_user_locale(ctx, message):
            return False

        if not user_has_nlu_access(self, message.author.id):
            DiscordRequestLogEntry.add_for_chat(
                ctx,
                message,
                MGCertificate.getUserLevel(message.author),
                None,
                {"text": message.content, "detail": "NO_NLU_ACCESS"},
            )

            await ctx.reply(
                _(
                    "Chat mode is only available when you have access to the **MK Bot Support Server**."
                )
                + "\nhttps://discord.gg/3RpDwjJCeZ"
            )
            return True

        if not NluModel.nlu:
            DiscordRequestLogEntry.add_for_chat(
                ctx,
                message,
                MGCertificate.getUserLevel(message.author),
                None,
                {"text": message.content, "detail": "NLU_NOT_ACTIVATED"},
            )

            await ctx.reply(_("Chat mode is not activated."))
            return True

        text = re.sub("<@!?\\d+> ", "", message.content)
        chat_intent: Intent = await NluModel.parse(text)

        if not chat_intent:
            DiscordRequestLogEntry.add_for_chat(
                ctx,
                message,
                MGCertificate.getUserLevel(message.author),
                None,
                {"text": message.content, "detail": "NLU_IS_LOADING"},
            )

            await ctx.reply(_("Loading chat mode... Please try again later."))
            return True

        if chat_intent.response:
            message.content = f"{CONFIG.commandPrefix}{chat_intent.response}"
            new_ctx = await self.get_context(message)

            if new_ctx.command is None:
                raise Exception(f"Invalid Response: {chat_intent.response}")

            request_id = DiscordRequestLogEntry.add_for_chat(
                new_ctx,
                message,
                MGCertificate.getUserLevel(message.author),
                new_ctx.command.name,
                chat_intent.detail,
            )
            new_ctx.mkbot_request_id = request_id

            await self.invoke(new_ctx)

        else:
            DiscordRequestLogEntry.add_for_chat(
                ctx,
                message,
                MGCertificate.getUserLevel(message.author),
                chat_intent.name,
                chat_intent.detail,
            )
            await ctx.reply(
                _(
                    "I think you told me about the `{command}` command, but I am not confident that I have understood you correctly.\nPlease try rephrasing your instruction to me."
                ).format(command=chat_intent.description)
            )

        return True

    async def get_context(self, message, *, cls=MKBotContext):
        return await super().get_context(message, cls=cls)


def user_has_nlu_access(bot: MKBot, user_id: int):
    if is_development_mode():
        return True

    guild = bot.get_guild(VERSION.MBSS_ID)

    if guild and guild.get_member(user_id):
        return True
    else:
        return False


async def create_bot(return_error_level=False):
    stime = time.time()
    errorlevel = 0
    pending = True
    synced = False

    if is_development_mode():
        name = "IN DEBUG" if "--debug" in sys.argv else "IN DEV"
        activity_type = discord.ActivityType.playing
    elif VERSION == None:
        name = "MK Bot Test Mode"
        activity_type = discord.ActivityType.playing
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

        nonlocal synced
        if not synced:
            bot.tree.on_error = on_app_command_error

            await MGCertificate.set_owners(bot)

            replyformat.set_avatar_url(
                "https://cdn.discordapp.com/avatars/698478990280753174/6b71c165ba779edc2a7c73f074a51ed5.png?size=20"
            )

            await bot.tree.set_translator(MKBotTranslator())

            if is_development_mode():
                for guild in CONFIG.discordAppCmdGuilds:
                    try:
                        guild = int(guild)
                    except ValueError:
                        continue

                    bot.tree.copy_global_to(guild=discord.Object(guild))
                    cmds = await bot.tree.sync(guild=discord.Object(guild))

                    print(
                        f"App commands synced for {guild} ({', '.join([c.name for c in cmds])})"
                    )
            else:
                cmds = await bot.tree.sync()

                TelemetryReporter.Event(
                    "AppCommandSynced",
                    {"cmds": [{"id": c.id, "name": c.name} for c in cmds]},
                )

            synced = True

    @bot.event
    async def on_message(message: discord.Message):
        if message.author == bot.user:
            return

        if (message.channel.type.value == 1) and (CONFIG.disabledPrivateChannel):
            return

        ctx: commands.Context = await bot.get_context(message)

        valid_request = False

        if message.content.startswith(bot.user.mention) and cert.isCertUser(
            message.author
        ):
            i18n.set_current_locale(get_user_locale_code(message.author.id))

            valid_request = await bot.process_chats(ctx, message)
        else:
            request_id = None
            if ctx.command is not None:
                request_id = DiscordRequestLogEntry.add(
                    ctx, message, MGCertificate.getUserLevel(message.author)
                )

            valid_request = await bot.process_commands(request_id, message)

        nonlocal pending
        if valid_request:
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

            if len(issue_link) <= 512:
                view = View()
                view.add_item(
                    Button(
                        label=_("Report Issue"), style=ButtonStyle.url, url=issue_link
                    )
                )
            else:
                view = None

            await ctx.send(embed=MsgFormatter.abrt(ctx, issue_link, tb), view=view)

            TelemetryReporter.Exception(error, {"origin": "abrt"})
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

                TelemetryReporter.Exception(error, {"origin": "abrt"})
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
                interaction, MGCertificate.getUserLevel(interaction.user)
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
            sys.path.append(f"{api.extensions_path}/{i[0]}")
            if i[1]:
                await bot.load_extension(i[1])
    except Exception:
        traceback.print_exc()

    flag_checker.start()
    usage.start()

    print("Mulgyeol MK Bot")
    print(f"Version {VERSION}" if VERSION != None else "Test Mode")
    print("Copyright (c) 2023 Mulgyeol Labs. All rights reserved.\n")
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

    with using_nlu():
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
        except discord.errors.LoginFailure as e:
            log.critical(e)
            exit_code = 1
        except Exception as e:
            traceback.print_exc()
            log.critical(e)
        finally:
            usage_helper()

        BotStateFlags.online = False
        self.callback(exit_code)


if __name__ == "__main__":
    run_migrations(SCRIPT_DIR, DB_URL)
    asyncio.run(start_bot())
