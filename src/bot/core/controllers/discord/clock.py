import asyncio
import random
import time
import traceback
from datetime import datetime

import discord
import pytz
from discord import app_commands
from discord.ext import commands

from mgylabs.db.storage import localStorage
from mgylabs.i18n import L_, _
from mgylabs.utils import logger

from .utils.command_helper import send
from .utils.MGCert import Level, MGCertificate
from .utils.MsgFormat import MsgFormatter

log = logger.get_logger(__name__)


class Sleeper:
    # "Group sleep calls allowing instant cancellation of all"

    def __init__(self):
        self.tasks = set()

    async def sleep(self, delay, result=None):
        coro = asyncio.sleep(delay, result=result)
        task = asyncio.ensure_future(coro)
        self.tasks.add(task)
        try:
            return await task
        except asyncio.CancelledError:
            return result
        finally:
            self.tasks.remove(task)

    def cancel_all_helper(self):
        # "Cancel all pending sleep tasks"
        cancelled = set()
        for task in self.tasks:
            if task.cancel():
                cancelled.add(task)
        return cancelled

    async def cancel_all(self):
        # "Coroutine cancelling tasks"
        cancelled = self.cancel_all_helper()
        if self.tasks:
            await asyncio.wait(self.tasks)
            self.tasks -= cancelled
        return len(cancelled)


sleeper = Sleeper()

clock_emoji = ["🕛", "🕐", "🕑", "🕒", "🕓", "🕔", "🕕", "🕖", "🕗", "🕘", "🕙", "🕚"]


def get_clock_content(tz, offset):
    d = pytz.utc.localize(datetime.utcnow()).astimezone(tz)
    ct = d.strftime("%I:%M %p")
    return f"{clock_emoji[d.hour%12]} {ct} ({offset})"


async def clock_updater(bot: commands.Bot):
    while True:
        registry: dict = localStorage["discord_clock_registry"]
        last_updated_at = localStorage["discord_clock_last_updated_at"]

        if not (registry):
            Clock.clock_updater_running = False
            break

        if not last_updated_at:
            last_updated_at = 0

        if time.time() - last_updated_at < 300:
            await sleeper.sleep(300 + random.randrange(0, 60 * 3 + 1, 60))

        for cid, params in registry.items():
            ch = bot.get_channel(cid)
            if not ch:
                localStorage.dict_pop("discord_clock_registry", cid)
                print(f"Remove Clock: {cid}")
                continue

            try:
                await ch.edit(name=get_clock_content(*params))
            except Exception:
                traceback.print_exc()

            log.debug("Clock Updated")

        localStorage["discord_clock_last_updated_at"] = time.time()

        await sleeper.sleep(300 + random.randrange(0, 60 * 3 + 1, 60))


class Clock(commands.Cog):
    clock_group = app_commands.Group(
        name="clock", description=L_("Shows live world clock.")
    )
    clock_updater_running = False

    def __init__(self, bot):
        self.bot: commands.Bot = bot

    async def ensure_clock_updater_running(self):
        if not Clock.clock_updater_running:
            Clock.clock_updater_running = True
            self.bot.loop.create_task(clock_updater(self.bot))

    async def update_clock_now(self):
        await self.ensure_clock_updater_running()
        await sleeper.cancel_all()

    @commands.Cog.listener()
    async def on_ready(self):
        await self.ensure_clock_updater_running()

    @clock_group.command()
    @MGCertificate.verify(level=Level.TRUSTED_USERS)
    async def set(self, interaction: discord.Interaction, timezone: str):
        """Enables live world clock."""
        try:
            tz = pytz.timezone(timezone)
        except Exception as error:
            raise app_commands.AppCommandError(f"Invalid timezone: {error}")

        registry = localStorage["discord_clock_registry"]

        if registry is None:
            localStorage["discord_clock_registry"] = {}

        dt = tz.utcoffset(datetime.now()).total_seconds() / 3600
        offset = "GMT{:+}".format(int(dt))

        ps = discord.PermissionOverwrite.from_pair([], discord.Permissions.all())
        ps.update(view_channel=True)

        overwrites = {interaction.guild.default_role: ps}
        ch = await interaction.guild.create_voice_channel(
            get_clock_content(tz, offset), overwrites=overwrites
        )

        localStorage.dict_update("discord_clock_registry", {ch.id: [tz, offset]})

        await self.ensure_clock_updater_running()

        await send(
            interaction,
            embed=MsgFormatter.get(
                interaction,
                "Clock",
                _("Successfully set live clock."),
            ),
        )

    @set.autocomplete("timezone")
    async def set_timezone_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ):
        ls = [
            app_commands.Choice(name=v, value=v)
            for v in pytz.all_timezones
            if current.lower() in v.lower()
        ]

        return ls[:20]


async def setup(bot: commands.Bot):
    await bot.add_cog(Clock(bot))
