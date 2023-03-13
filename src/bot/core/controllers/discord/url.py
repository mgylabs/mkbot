from urllib.parse import urljoin

import aiohttp
import discord
from bs4 import BeautifulSoup
from discord import app_commands
from discord.ext import commands

from mgylabs.i18n import _
from mgylabs.utils import logger

from .utils.MGCert import Level, MGCertificate
from .utils.MsgFormat import MsgFormatter

log = logger.get_logger(__name__)


def get_useragent():
    return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"


def get_meta_content(soup: BeautifulSoup, *args, **kwargs):
    return t.get("content") if (t := soup.find("meta", *args, **kwargs)) else None


async def extract_url(url: str):
    async with aiohttp.ClientSession(
        headers={"User-Agent": get_useragent()}, raise_for_status=True
    ) as session:
        async with session.get(url) as r:
            request_url = r.url
            text = await r.text()

    soup = BeautifulSoup(text, "lxml")

    name = get_meta_content(soup, property="og:site_name") or get_meta_content(
        soup, {"name": "application-name"}
    )
    title = get_meta_content(soup, property="og:title") or soup.title.get_text()
    description = get_meta_content(soup, property="og:description")
    image_url = urljoin(str(request_url), get_meta_content(soup, property="og:image"))
    color = get_meta_content(soup, {"name": "theme-color"})

    return name, title, description, image_url, color


@app_commands.command(name="url")
@app_commands.describe()
@MGCertificate.verify(level=Level.TRUSTED_USERS)
async def link(interaction: discord.Interaction, url: str):
    """
    Replace URL with its title.
    """
    try:
        name, title, description, image_url, color = await extract_url(url)
    except Exception as e:
        log.exception(e)
        await interaction.response.send_message(
            embed=MsgFormatter.get(interaction, _("Invalid URL"), show_req_user=False),
            ephemeral=True,
        )
    else:
        embed = MsgFormatter.simple(
            title, description, url=url, color=color, thumbnail_url=image_url
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    bot.tree.add_command(link)
