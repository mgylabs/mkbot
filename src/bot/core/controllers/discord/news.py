import time
import traceback
from dataclasses import dataclass
from datetime import datetime, timedelta

import aiohttp
import discord
import pytz
from bs4 import BeautifulSoup
from discord import app_commands
from discord.ext import commands

from core.controllers.discord.utils import Emoji
from core.controllers.discord.utils.MGCert import Level, MGCertificate
from core.controllers.discord.utils.MsgFormat import MsgFormatter
from mgylabs.db import database
from mgylabs.db.models import DiscordUser
from mgylabs.db.storage import localStorage
from mgylabs.i18n import __
from mgylabs.utils import logger
from mgylabs.utils.event import AsyncScheduler, SchTask
from mgylabs.utils.LogEntry import DiscordEventLogEntry

from .utils.feature import Feature

log = logger.get_logger(__name__)


def get_useragent():
    return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"


class SearchResult:
    def __init__(
        self, url, title, description, image_url, press, press_image_url, timestamp
    ):
        self.url = url
        self.title = title
        self.description = description
        self.image_url = image_url
        self.press = press
        self.press_image_url = press_image_url
        self.timestamp = timestamp

    def __repr__(self):
        return f"SearchResult(url={self.url}, title={self.title}, description={self.description}, press={self.press})"


PD = {"6h": 12, "1d": 4, "all": 0}


async def _req_query(term, pd=0):
    headers = {"User-Agent": get_useragent()}

    async with aiohttp.ClientSession(headers=headers, raise_for_status=True) as session:
        async with session.get(
            "https://m.search.naver.com/search.naver?ssc=tab.m_news.all&where=m_news&sm=mtb_jum",
            params=dict(query=term, pd=pd),
        ) as r:
            text = await r.text()
            return text


async def search_by_query(term, num_results=1, pd=PD):
    for v in pd.values():
        text = await _req_query(term, v)

        soup = BeautifulSoup(text, "lxml")
        news_result_list_ul = soup.select_one("#news_result_list")

        if news_result_list_ul:
            news_result_list = news_result_list_ul.find_all("li", recursive=False)

            if len(news_result_list) >= num_results:
                break
    else:
        if not news_result_list_ul:
            return []

    ls = []

    result: BeautifulSoup
    for result in news_result_list[:num_results]:
        url = result.select_one("div.news_wrap > a")["href"]
        title = result.select_one("div.news_wrap > a > div").get_text()
        description = result.select_one(
            "div.news_wrap > div.news_dsc > div > a > div"
        ).get_text()
        image_url = result.select_one("div.news_wrap > div.news_dsc > a > img")
        if image_url:
            image_url = image_url["data-lazysrc"]
        press = result.select_one(
            "div.news_wrap > div.news_info > div.info_group > a"
        ).find(string=True, recursive=False)
        press_image_url = result.select_one(
            "div.news_wrap > div.news_info > div.info_group > a > span > img"
        )
        if press_image_url:
            press_image_url = press_image_url["data-lazysrc"]
        timestamp = result.select_one(
            "div.news_wrap > div.news_info > div.info_group > span:nth-child(2)"
        ).get_text()

        ls.append(
            SearchResult(
                url, title, description, image_url, press, press_image_url, timestamp
            )
        )

    return ls


@dataclass
class NewsNotifyData:
    user_id: int
    channel_id: int
    msg_id: int
    hour: int
    minute: int
    keyword: str
    created_at: datetime
    provider: str = "naver"
    count: int = 3
    last_notified_at: float = 0


task_dict = {}


def get_target_datetime(timezone, hour, minute, now: datetime = None):
    now = now or datetime.now(pytz.UTC)
    now = now.astimezone(timezone)
    target_date = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    if now >= target_date:
        target_date = target_date + timedelta(days=1)

    return target_date


async def add_to_scheduler(bot: commands.Bot, data: NewsNotifyData):
    user = DiscordUser.get_one_or_none(id=data.user_id)

    date = get_target_datetime(pytz.timezone(user.timezone), data.hour, data.minute)
    task = SchTask(date, news_notify(bot, data))

    key = (data.channel_id, data.provider, data.keyword)

    if data.msg_id in task_dict:
        try:
            AsyncScheduler.remove_task(task_dict[key])
        except KeyError as error:
            log.exception(error)

    task_dict[key] = task

    await AsyncScheduler.add_task(task)


def remove_from_scheduler(channel_id, provider, keyword):
    key = (channel_id, provider, keyword)

    if key in task_dict:
        try:
            AsyncScheduler.remove_task(task_dict[key])
        except KeyError as error:
            log.exception(error)

        del task_dict[key]


@database.using_database
async def news_notify(bot: commands.Bot, data: NewsNotifyData):
    ch = bot.get_channel(data.channel_id)

    results: list[SearchResult] = await search_by_query(
        data.keyword, 3, {"1d": PD["1d"], "all": PD["all"]}
    )

    await ch.send(
        __("📰 Here is the news related to `{query}`").format(query=data.keyword)
    )

    for result in results:
        await ch.send(
            embed=MsgFormatter.news(
                result.title,
                result.description,
                f"{result.press} · {result.timestamp}",
                result.press_image_url,
                thumbnail_url=result.image_url,
                url=result.url,
            ),
        )

    button = NotificationButtonOff(data.keyword, data.provider, data.msg_id)

    view = discord.ui.View()
    view.add_item(button)
    await ch.send(view=view)

    data.last_notified_at = time.time()
    localStorage.dict_update(
        "discord_news_registry", {(data.channel_id, data.provider, data.keyword): data}
    )

    DiscordEventLogEntry.Add(
        data.msg_id,
        "NewsNotify",
        {
            "query": data.keyword,
            "provider": data.provider,
            "created_at": str(data.created_at),
            "time": f"{data.hour:02d}:{data.minute:02d}",
            "results": [
                {
                    "title": result.title,
                    "description": result.description,
                    "press": result.press,
                    "timestamp": result.timestamp,
                    "url": result.url,
                }
                for result in results
            ],
        },
    )

    await add_to_scheduler(bot, data)


@database.using_database
async def news_notify_loader(bot: commands.Bot):
    registry: dict = localStorage["discord_news_registry"]

    if not (registry):
        return

    data: NewsNotifyData
    for data in registry.values():
        await add_to_scheduler(bot, data)


NEWS_CATEGORY = [
    "Politics",
    "Economy",
    "Society",
    "Lifestyle/Culture",
    "World",
    "IT/Science",
]


class News(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.init_load = False

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.init_load:
            self.init_load = True
            await news_notify_loader(self.bot)

    @commands.hybrid_group(name="news")
    @MGCertificate.verify(level=Level.TRUSTED_USERS)
    async def news_command(self, ctx: commands.Context) -> None:
        """
        Search for news or set up news notifications.

        {commandPrefix}news search microsoft
        {commandPrefix}news category IT/Science
        """

    @news_command.command()
    @MGCertificate.verify(level=Level.TRUSTED_USERS)
    @Feature.Experiment()
    async def search(
        self,
        ctx: commands.Context,
        query: str,
    ):
        """
        Search news by keyword or set up news notifications.
        """
        if query is None:
            await ctx.send(
                embed=MsgFormatter.get(
                    ctx,
                    __("News"),
                    __("Please enter your query."),
                ),
            )
            return

        search_msg: discord.Message = await ctx.send(
            f"{Emoji.typing} " + __("Searching... `%s`") % query
        )

        results: list[SearchResult] = await search_by_query(query, 3)

        subscribed = localStorage.dict_include(
            "discord_news_registry", (ctx.channel.id, "naver", query)
        )

        if results:
            await search_msg.edit(
                content=__("📰 News search results for `{query}`").format(query=query)
            )

            for result in results:
                await ctx.channel.send(
                    embed=MsgFormatter.news(
                        result.title,
                        result.description,
                        f"{result.press} · {result.timestamp}",
                        result.press_image_url,
                        thumbnail_url=result.image_url,
                        url=result.url,
                    ),
                )

            if subscribed:
                button = NotificationButtonOff(query, "naver", ctx.message.id)
            else:
                button = NotificationButtonOn(query, "naver", ctx.message.id)

            view = discord.ui.View()
            view.add_item(button)
            await ctx.channel.send(view=view)

            DiscordEventLogEntry.Add(
                ctx,
                "NewsSearchSucceeded",
                {
                    "query": query,
                    "provider": "naver",
                    "results": [
                        {
                            "title": result.title,
                            "description": result.description,
                            "press": result.press,
                            "timestamp": result.timestamp,
                            "url": result.url,
                        }
                        for result in results
                    ],
                },
            )
        else:
            await search_msg.edit(
                content=__("🚫 No results were found for `{query}`").format(query=query)
            )

            DiscordEventLogEntry.Add(
                ctx, "NewsSearchFailed", {"query": query, "provider": "naver"}
            )

    @news_command.command()
    @MGCertificate.verify(level=Level.TRUSTED_USERS)
    @Feature.Experiment()
    async def category(
        self,
        ctx: commands.Context,
        category: str,
    ):
        """
        Search news by category or set up news notifications.
        """
        if category not in NEWS_CATEGORY:
            await ctx.send(
                embed=MsgFormatter.get(
                    ctx,
                    "News",
                    __("Invalid category."),
                ),
            )
            return

        await ctx.send(
            embed=MsgFormatter.get(
                ctx,
                "News",
                __("This feature is not yet supported."),
            ),
        )

    @category.autocomplete("category")
    async def news_category_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ):
        ls = [
            app_commands.Choice(name=v, value=v)
            for v in NEWS_CATEGORY
            if current.lower() in v.lower()
        ]

        return ls


class NotificationButtonOn(discord.ui.Button):
    def __init__(self, keyword: str, provider: str, msg_id: int):
        super().__init__(style=discord.ButtonStyle.green, label=__("Subscribe"))

        self.keyword = keyword
        self.provider = provider
        self.msg_id = msg_id

    async def callback(self, interaction: discord.Interaction):
        self.fv = NotificationModal(
            self.keyword, interaction.user, self.msg_id, self, self.view
        )
        await interaction.response.send_modal(self.fv)
        self.view.stop()


class NotificationButtonOff(discord.ui.Button):
    def __init__(self, keyword: str, provider: str, msg_id: int):
        super().__init__(style=discord.ButtonStyle.gray, label=__("Unsubscribe"))

        self.keyword = keyword
        self.provider = provider
        self.msg_id = msg_id

    async def callback(self, interaction: discord.Interaction):
        self.disabled = True
        self.label = __("Unsubscribed")
        self.style = discord.ButtonStyle.red
        remove_from_scheduler(interaction.channel_id, self.provider, self.keyword)
        key = (interaction.channel_id, self.provider, self.keyword)

        if localStorage.dict_include("discord_news_registry", key):
            localStorage.dict_pop("discord_news_registry", key)

            DiscordEventLogEntry.Add(
                self.msg_id,
                "NewsByKeywordUnsubscribed",
                {
                    "query": self.keyword,
                    "requester": interaction.user.id,
                },
            )

        await interaction.response.edit_message(view=self.view)
        self.view.stop()


def get_user_local_current_time(member: discord.member):
    user = DiscordUser.get_one_or_none(id=member.id)

    if user is None:
        tz = pytz.timezone("UTC")
    else:
        tz = pytz.timezone(user.timezone)

    d = datetime.now(pytz.utc).astimezone(tz)

    lt = d.strftime("%H:%M")

    dt = tz.utcoffset(datetime.now()).total_seconds() / 3600
    offset = "GMT{:+}".format(int(dt))

    return lt, offset


class NotificationModal(discord.ui.Modal):
    summary = discord.ui.TextInput(
        label="Notification time",
        default="",
        placeholder="hour:minute",
        required=True,
        max_length=5,
    )

    def __init__(
        self,
        keyword: str,
        member: discord.member,
        msg_id: int,
        button: discord.ui.Button,
        view: discord.ui.View,
        **kwargs,
    ) -> None:
        self.keyword = keyword
        self.msg_id = msg_id
        self.button = button
        self.view = view

        lt, offset = get_user_local_current_time(member)

        NotificationModal.summary.label = __(
            "Notification time (Your time zone is {offset})"
        ).format(offset=offset)
        NotificationModal.summary.default = lt
        super().__init__(title=f"{__('Subscribe to News')} ({keyword})", **kwargs)

    @database.using_database
    async def on_submit(self, interaction: discord.Interaction):
        registry = localStorage["discord_news_registry"]

        if registry is None:
            localStorage["discord_news_registry"] = {}

        timestamp = datetime.strptime(self.summary.value, "%H:%M")

        data = NewsNotifyData(
            interaction.user.id,
            interaction.channel_id,
            self.msg_id,
            timestamp.hour,
            timestamp.minute,
            self.keyword,
            datetime.now(pytz.UTC),
        )

        key = (data.channel_id, data.provider, data.keyword)
        if not localStorage.dict_include("discord_news_registry", key):
            localStorage.dict_update("discord_news_registry", {key: data})

            await add_to_scheduler(interaction.client, data)

            DiscordEventLogEntry.Add(
                data.msg_id,
                "NewsByKeywordSubscribed",
                {
                    "query": data.keyword,
                    "provider": data.provider,
                    "created_at": str(data.created_at),
                    "time": f"{data.hour:02d}:{data.minute:02d}",
                    "requester": interaction.user.id,
                },
            )

        self.button.disabled = True
        self.button.label = __("Subscribed")
        self.button.style = discord.ButtonStyle.gray

        await interaction.response.edit_message(view=self.view)

    async def on_error(
        self, error: Exception, interaction: discord.Interaction
    ) -> None:
        await interaction.response.send_message(
            __("Oops! Something went wrong."), ephemeral=True
        )

        traceback.print_tb(error.__traceback__)


async def setup(bot: commands.Bot):
    """
    News
    """
    await bot.add_cog(News(bot))
