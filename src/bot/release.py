import os

import aiofiles
import aiohttp

from core.controllers.discord.utils.MsgFormat import MsgFormatter
from mgylabs.db.storage import localStorage
from mgylabs.i18n import _
from mgylabs.utils import logger
from mgylabs.utils.version import VERSION

log = logger.get_logger(__name__)


class Field:
    def __init__(self, name, value, inline=False) -> None:
        self.name = name
        self.value = value
        self.inline = inline

    def to_dict(self):
        return {"name": self.name, "value": self.value, "inline": self.inline}


class ReleaseNote:
    def __init__(self, rel_body) -> None:
        self.body = rel_body.splitlines()
        self.body = [x for x in self.body if x != ""]
        self.render()

    def render(self):
        header = []
        value = {}
        name = None
        for t in self.body:
            if t.startswith("## "):
                name = t.replace("## ", "")
                value[name] = []
                continue
            elif name != None and t.startswith("* "):
                value[name].append(t)
            elif name == None:
                header.append(t)
        self.description = "\n".join(header)
        self.fields = [Field(k, "\n".join(v)).to_dict() for k, v in value.items()]


class ReleaseNotify:
    @classmethod
    async def run(cls, user_id, send):
        if (VERSION.is_release_build()) and (not VERSION.is_prerelease()):
            if not cls.exist_flag():
                localStorage["release_notify_user_ids"] = []
                await cls.write_flag()

            user_ids = localStorage["release_notify_user_ids"]

            if user_id not in user_ids:  # pylint: disable=unsupported-membership-test
                localStorage["release_notify_user_ids"] += [user_id]

                await cls.send_release_note(send)

    @classmethod
    def exist_flag(cls):
        return os.path.isfile("release.flag")

    @classmethod
    async def write_flag(cls):
        async with aiofiles.open("release.flag", "wt") as f:
            await f.write("flag")

    @classmethod
    async def send_release_note(cls, send):
        note_api_url = (
            f"https://api.github.com/repos/mgylabs/mkbot/releases/tags/{VERSION.tag}"
        )
        note_url = f"https://github.com/mgylabs/mkbot/releases/tag/{VERSION.tag}"
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            async with session.get(note_api_url) as res:
                js = await res.json()
                note = ReleaseNote(js["body"])
        if note.description == "":
            note.description = _("Welcome to the %s release of MK Bot.") % VERSION.tag
        embed = MsgFormatter.push(
            f"Mulgyeol MK Bot {VERSION.tag} {_('Release')} 🎉",
            note.description
            + "\n"
            + _("Please see the [Release Note](%s) for more information.") % note_url,
            note.fields,
        )
        await send(embed=embed)
