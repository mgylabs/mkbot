import datetime
import re

import aiohttp
from discord.ext import commands
from mgylabs.utils import logger
from mgylabs.utils.config import CONFIG

from .utils.exceptions import UsageError
from .utils.MGCert import Level, MGCertificate
from .utils.MsgFormat import MsgFormatter

log = logger.get_logger(__name__)

base_url = "https://mgylabs.herokuapp.com"
accessToken = None


async def refresh_token(session):
    global accessToken
    async with session.post(
        base_url + "/auth/token/refresh",
        data={"refresh": CONFIG.mgylabsToken},
    ) as r:
        if r.status == 200:
            js = await r.json()
            CONFIG.mgylabsToken = js["refresh"]
            accessToken = js["access"]
        else:
            js = await r.json()
            log.debug(js)
            raise UsageError(
                js["detail"]
                if "detail" in js
                else "Invalid token: Before using this command, the administrator must create a token by entering `/generate mgylabs <username> <password>` in the local shell."
            )


async def get_hls(session, vid):
    headers = {"Authorization": "Bearer " + accessToken}

    async with session.get(
        base_url + f"/highlighter/v1/twitch/{vid}", params={"limit": 3}, headers=headers
    ) as r:
        js = await r.json()
        return r.status, js


def text_for_human(data: dict, url):
    builder = []

    for h in data["highlights"]:
        s = datetime.timedelta(seconds=h["start"])
        e = datetime.timedelta(seconds=h["end"])
        pr = round(h["probability"] * 100, 2)

        mm, ss = divmod(s.seconds, 60)
        hh, mm = divmod(mm, 60)
        hms = "%dh%02dm%02ds" % (hh, mm, ss)
        builder.append(f"[{s} ~ {e}]({url}?t={hms}) | {pr}")

    return "\n".join(builder)


@commands.command(aliases=["hl"])
@commands.max_concurrency(1)
@commands.cooldown(1, 60, commands.BucketType.user)
@MGCertificate.verify(level=Level.TRUSTED_USERS)
async def highlighter(ctx: commands.Context, url):
    """
    Finds Highlights From Recorded Live Videos

    {commandPrefix}highlighter `https://www.twitch.tv/videos/123456789`
    {commandPrefix}hl `https://www.twitch.tv/videos/123456789`

    * Note!
    Before using this command, the administrator must create a token by entering `/generate mgylabs <username> <password>` in the local shell.
    """
    if m := re.search(
        "(?:https:\/\/)?(?:www[.])?twitch[.]tv\/videos\/(?P<vid>\d+)",
        url,
        re.IGNORECASE,
    ):
        vid = m.group("vid")
        url = m.group(0)
        print(vid, url)
    else:
        raise UsageError(f"{url} is not a valid URL.")

    async with ctx.typing():
        async with aiohttp.ClientSession() as session:
            if accessToken == None:
                await refresh_token(session)

            for _ in range(2):
                status, js = await get_hls(session, vid)

                if status == 200:
                    await ctx.send(
                        embed=MsgFormatter.get(
                            ctx, f"Highlighter for {url}", text_for_human(js, url)
                        )
                    )
                    break
                elif status in [404, 503]:
                    await ctx.send(
                        embed=MsgFormatter.get(ctx, "Highlighter", js["notice"])
                    )
                    break
                elif status == 401:
                    await refresh_token(session)
                else:
                    log.debug(f"[{status}] " + str(js))
                    raise UsageError("Unknown Error")
            else:
                log.debug(f"[{status}] " + str(js))
                raise UsageError("Unknown Error")


async def setup(bot: commands.Bot):
    bot.add_command(highlighter)
