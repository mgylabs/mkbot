import logging
import os

import aiofiles
import aiohttp
import discord

from core.utils.config import VERSION
from core.utils.MsgFormat import MsgFormatter

log = logging.getLogger(__name__)


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
    async def run(cls, bot):
        if (not VERSION.is_canary()) and (not cls.exist_flag()):
            await cls.write_flag()
            await cls.send_release_note(bot)

    @classmethod
    def exist_flag(cls):
        return os.path.isfile("msu.flag")

    @classmethod
    async def write_flag(cls):
        async with aiofiles.open("msu.flag", "wt") as f:
            await f.write("flag")

    @classmethod
    async def send_release_note(cls, channel: discord.TextChannel):
        note_api_url = f"https://api.github.com/repos/mgylabs/mulgyeol-mkbot/releases/tags/{VERSION.tag}"
        note_url = (
            f"https://github.com/mgylabs/mulgyeol-mkbot/releases/tag/{VERSION.tag}"
        )
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            async with session.get(note_api_url) as res:
                js = await res.json()
                note = ReleaseNote(js["body"])
        if note.description == "":
            note.description = f"Welcome to the {VERSION.tag} release of MK Bot."
        embed = MsgFormatter.push(
            f"Mulgyeol MK Bot {VERSION.tag} Release 🎉",
            note.description
            + f"\nPlease see the [Release Note]({note_url}) for more information.",
            note.fields,
        )
        await channel.send(embed=embed)
