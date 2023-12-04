import time
import traceback
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import discord
import pytz
from discord import app_commands
from discord.ext import commands

from mgylabs.db import database
from mgylabs.db.storage import localStorage
from mgylabs.i18n import _L, __
from mgylabs.utils import logger
from mgylabs.utils.event import AsyncScheduler, SchTask, Sleeper

from .utils.command_helper import send
from .utils.feature import Feature
from .utils.MGCert import Level, MGCertificate
from .utils.MsgFormat import MsgFormatter

log = logger.get_logger(__name__)


sleeper = Sleeper()


@dataclass
class DDayData:
    user_id: int
    channel_id: int
    date: datetime
    title: str
    offset: str
    last_updated_at: float = 0


def calc_dday(date: datetime):
    dday = datetime.now(tz=date.tzinfo).date() - date.date()
    return dday.days


def get_dday_content(dday: int, name: str):
    if dday == 0:
        return f"🎉 D-Day ({name})"
    else:
        return f"{'📅' if dday < 0 else '✅'} D{'{:+d}'.format(dday)} ({name})"


def get_midnight_datetime(timezone, now: datetime = None):
    now = now or datetime.now(pytz.UTC)
    now = now.astimezone(timezone)
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(
        days=1
    )

    return midnight


def remaining_time_in_timezone(timezone, now: datetime = datetime.now(pytz.UTC)) -> int:
    now = now.astimezone(timezone)
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(
        days=1
    )
    remaining_time = midnight - now

    log.info(f"Remaining Time: {remaining_time}")
    return remaining_time.seconds


async def add_to_scheduler(bot: commands.Bot, cid: int, data: DDayData):
    await AsyncScheduler.add_task(
        SchTask(
            get_midnight_datetime(data.date.tzinfo), do_update_ch_name(bot, cid, data)
        )
    )


async def do_update_ch_name(bot: commands.Bot, cid: int, data: DDayData):
    ch = bot.get_channel(cid)
    if not ch:
        localStorage.dict_pop("discord_dday_registry", cid)
        log.info(f"Remove D-Day: {cid}")
        return

    if time.time() - data.last_updated_at < 300:
        await add_to_scheduler(bot, cid, data)
        return

    day = calc_dday(data.date)

    if day == 0 and data.date > datetime.now(pytz.UTC):

        async def notify():
            channel = ch.guild.get_channel(data.channel_id)

            await channel.send(
                embed=MsgFormatter.push(
                    f"📅 {data.title}",
                    __("Today is D-Day. 🎉"),
                    [
                        {
                            "name": "Time",
                            "value": f"{data.date.strftime('%I:%M %p')} ({data.offset})",
                        },
                        {
                            "name": "Author",
                            "value": bot.get_user(data.user_id).mention,
                        },
                    ],
                ),
            )

        await AsyncScheduler.add_task(SchTask(data.date, notify()))

    try:
        await ch.edit(name=get_dday_content(day, data.title))
    except Exception:
        traceback.print_exc()
    else:
        data.last_updated_at = time.time()
        localStorage.dict_update("discord_dday_registry", {cid: data})

    await add_to_scheduler(bot, cid, data)
    log.info(f"Update D-Day: {data.title}")


@database.using_database
async def dday_loader(bot: commands.Bot):
    registry: dict = localStorage["discord_dday_registry"]

    if not (registry):
        return

    cid: int
    data: DDayData
    for cid, data in registry.items():
        await do_update_ch_name(bot, cid, data)


class DDay(commands.Cog):
    group = app_commands.Group(
        name="dday",
        description=_L("Shows D-Day widget."),
        # default_permissions=discord.Permissions(administrator=True),
    )

    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await dday_loader(self.bot)

    @group.command()
    @app_commands.rename(time_str="time")
    @app_commands.describe(date="<year/month/day>", time_str="<hour>:<minute>")
    @MGCertificate.verify(level=Level.TRUSTED_USERS)
    @Feature.Experiment()
    async def set(
        self,
        interaction: discord.Interaction,
        title: str,
        timezone: str,
        date: str,
        time_str: str,
        channel: Optional[discord.TextChannel],
    ):
        """
        Enables D-Day widget.
        """
        try:
            tz = pytz.timezone(timezone)
        except Exception as error:
            raise app_commands.AppCommandError(f"Invalid timezone: {error}")

        channel = channel or interaction.channel

        registry = localStorage["discord_dday_registry"]

        if registry is None:
            localStorage["discord_dday_registry"] = {}

        dt = tz.utcoffset(datetime.now()).total_seconds() / 3600
        offset = "GMT{:+}".format(int(dt))

        date_ls = date.split("/")
        if len(date_ls) != 3 or not all([d.isdigit() for d in date_ls]):
            raise app_commands.AppCommandError(
                __("Invalid date format. The required format is `<year/month/day>`")
            )
        date_ls = list(map(int, date_ls))

        time_ls = time_str.split(":")
        if len(time_ls) != 2 or not all([d.isdigit() for d in time_ls]):
            raise app_commands.AppCommandError(
                __("Invalid time format. The required format is `<hour>:<minute>`.")
            )
        time_ls = list(map(int, time_ls))

        data = DDayData(
            interaction.user.id,
            channel.id,
            datetime(*date_ls, *time_ls, tzinfo=tz),
            title,
            offset,
        )

        ps = discord.PermissionOverwrite.from_pair([], discord.Permissions.all())
        ps.update(view_channel=True)

        overwrites = {interaction.guild.default_role: ps}
        ch = await interaction.guild.create_voice_channel(
            get_dday_content(calc_dday(data.date), data.title), overwrites=overwrites
        )

        data.last_updated_at = ch.created_at.timestamp()

        localStorage.dict_update("discord_dday_registry", {ch.id: data})

        await do_update_ch_name(self.bot, ch.id, data)

        await send(
            interaction,
            embed=MsgFormatter.get(
                interaction,
                "D-Day",
                __("Successfully set D-Day widget."),
                [
                    {
                        "name": "Title",
                        "value": data.title,
                    },
                    {
                        "name": "Time",
                        "value": f"{data.date.strftime('%I:%M %p')} ({data.offset})",
                    },
                ],
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
    await bot.add_cog(DDay(bot))
