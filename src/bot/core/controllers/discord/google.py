import aiohttp
import discord
from bs4 import BeautifulSoup
from discord.ext import commands

from core.controllers.discord.utils import Emoji
from core.controllers.discord.utils.MGCert import Level, MGCertificate
from core.controllers.discord.utils.MsgFormat import MsgFormatter
from mgylabs.i18n import __
from mgylabs.utils.LogEntry import DiscordEventLogEntry


def get_useragent():
    return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"


async def _req(term, results, lang, start, proxies):
    headers = {"User-Agent": get_useragent()}

    async with aiohttp.ClientSession(headers=headers, raise_for_status=True) as session:
        async with session.get(
            "https://www.google.com/search",
            params=dict(
                q=term,
                num=results + 2,  # Prevents multiple requests
                hl=lang,
                start=start,
            ),
        ) as r:
            text = await r.text()
            return text


class SearchResult:
    def __init__(self, url, title, description):
        self.url = url
        self.title = title
        self.description = description

    def __repr__(self):
        return f"SearchResult(url={self.url}, title={self.title}, description={self.description})"


async def search(
    term, num_results=1, lang="en", proxy=None, advanced=False, sleep_interval=0
):
    escaped_term = term

    # Proxy
    proxies = None
    if proxy:
        if proxy.startswith("https"):
            proxies = {"https": proxy}
        else:
            proxies = {"http": proxy}

    # Fetch
    # Send request
    text = await _req(escaped_term, 1, lang, 0, proxies)

    # Parse
    soup = BeautifulSoup(text, "html.parser")
    result_block = soup.find_all("div", attrs={"class": "g"})
    for result in result_block:
        # Find link, title, description
        link = result.find("a", href=True)
        title = result.find("h3")
        description_box = result.find("div", {"style": "-webkit-line-clamp:2"})
        if description_box:
            description = description_box.find("span")
            if link and title and description:
                if advanced:
                    return SearchResult(link["href"], title.text, description.text)
                else:
                    return link["href"]


@commands.hybrid_command()
@MGCertificate.verify(level=Level.TRUSTED_USERS)
async def google(ctx: commands.Context, *, query):
    """
    Search on Google.
    """
    search_msg: discord.Message = await ctx.send(
        f"{Emoji.typing} " + __("Searching... `%s`") % query
    )

    result: SearchResult = await search(query, advanced=True)

    if result:
        await search_msg.edit(
            content=__("🔍 Google search results for `{query}`").format(query=query),
            embed=MsgFormatter.get(
                ctx,
                None,
                f"[{result.title}]({result.url})\n{result.description}",
            ),
        )

        DiscordEventLogEntry.Add(
            ctx,
            "GoogleSearchSucceeded",
            {
                "query": query,
                "title": result.title,
                "url": result.url,
                "description": result.description,
            },
        )
    else:
        await search_msg.edit(
            content=__("🚫 No results were found for `{query}`").format(query=query)
        )

        DiscordEventLogEntry.Add(ctx, "GoogleSearchFailed", {"query": query})


async def setup(bot: commands.Bot):
    bot.add_command(google)
