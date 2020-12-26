from discord.ext import commands
from .utils.MGCert import MGCertificate, Level
from .utils.MsgFormat import MsgFormatter
import requests
from bs4 import BeautifulSoup
import json


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
        self.song_list = dict()

    @commands.command(aliases=['m'])
    @MGCertificate.verify(level=Level.TRUSTED_USERS)
    async def play(self, ctx: commands.Context, song):
        """
        Music command
        """
        if "youtube.com" in song:
            r = requests.get(song)
            soup = BeautifulSoup(r.text, 'lxml')
            title = str(soup.find('title'))[7:-8]
            self.song_list[title] = song

        else:
            r = requests.get(
                "https://www.youtube.com/results?search_query=" + song)
            soup = BeautifulSoup(r.text, 'lxml')
            J = str(soup.find_all('script')[27])
            J = J.split('var ytInitialData = ')[1].split(';<')[0]

            s = json.loads(J)

            content = s['contents']['twoColumnSearchResultsRenderer']['primaryContents'][
                'sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents'][0:4]
            # 5개 노래 전부 하게 변경
            url = 'https://www.youtube.com/watch?v=' + \
                content[0]['videoRenderer']['videoId']
            description = content[0]['videoRenderer']['descriptionSnippet']['runs']
            title = ''
            for i in description:
                title += i['text']
            channel = content[0]['videoRenderer']['longBylineText']['runs'][0]['text']
            published_time = content[0]['videoRenderer']['publishedTimeText']['simpleText']
            viewCount = content[0]['videoRenderer']['viewCountText']['simpleText']
            length = content[0]['videoRenderer']['lengthText']['simpleText']

        await ctx.delete()
        await ctx.send(embed=MsgFormatter.get(ctx, title, " in Queue"))

    # async def list(self, ctx: commands.Context):


def setup(bot: commands.Bot):
    bot.add_cog(Music(bot))
