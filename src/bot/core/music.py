from discord.ext import commands
from .utils.MGCert import MGCertificate, Level
from .utils.MsgFormat import MsgFormatter
import requests
from bs4 import BeautifulSoup
import json

song_list = list()


class Song():
    def addSong(self, title, url):
        self.url = url
        self.title = title

    def searchSong(self, content, number):
        self.url = 'https://www.youtube.com/watch?v=' + \
            content[number]['videoRenderer']['videoId']
        self.description = content[number]['videoRenderer']['descriptionSnippet']['runs']
        self.title = ''
        for i in self.description:
            self.title += i['text']
        self.channel = content[number]['videoRenderer']['longBylineText']['runs'][0]['text']
        self.published_time = content[number]['videoRenderer']['publishedTimeText']['simpleText']
        self.viewCount = content[number]['videoRenderer']['viewCountText']['simpleText']
        self.length = content[number]['videoRenderer']['lengthText']['simpleText']

    def printSong(self):
        # markdown?
        print()


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.command(aliases=['m'])
    @MGCertificate.verify(level=Level.TRUSTED_USERS)
    async def search(self, ctx: commands.Context, song):
        """
        Music command
        """

        if "youtube.com" in song:
            r = requests.get(song)
            soup = BeautifulSoup(r.text, 'lxml')
            title = str(soup.find('title'))[7:-8]
            song_list.append(Song.addSong(title, song))
            await ctx.message.delete()
            await ctx.send(embed=MsgFormatter.get(ctx, song_list[-1].title, " in Queue"))

        else:
            r = requests.get(
                "https://www.youtube.com/results?search_query=" + song)
            soup = BeautifulSoup(r.text, 'lxml')
            J = str(soup.find_all('script')[27])
            J = J.split('var ytInitialData = ')[1].split(';<')[0]

            s = json.loads(J)

            a = 0
            b = 0

            while True:
                content = s['contents']['twoColumnSearchResultsRenderer']['primaryContents'][
                    'sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents']
                if not 'badges' in content[a]['videoRenderer'].keys():
                    song_ = Song()
                    song_.searchSong(content, a)
                    song_list.append(song_)
                    b += 1
                if b == 4:
                    break
                a += 1
            await ctx.message.delete()
            await ctx.send(embed=MsgFormatter.get(ctx, song + ' searched', song_list[0].title))


def setup(bot: commands.Bot):
    bot.add_cog(Music(bot))
