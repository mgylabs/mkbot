from discord.ext import commands
from .utils.MGCert import MGCertificate, Level
from .utils.MsgFormat import MsgFormatter
import requests
from bs4 import BeautifulSoup


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
        self.song_list = dict()

    @commands.Cog.listener
    @MGCertificate.verify(level=Level.TRUSTED_USERS)
    async def play(self, ctx: commands.Context, command, song):
        """
        Music command
        """
        if "youtube.com" in song:
            r = requests.get("song")
            soup = BeautifulSoup(r.text, 'lxml')
            title = soup.find('title)')[7:-8]
            song_list[title] = song
        else:
            song = "test"
        await ctx.send(embed=MsgFormatter.get(ctx, title, " in Queue"))

    # async def list(self, ctx: commands.Context):


def setup(bot: commands.Bot):
    bot.add_cog(Music)
