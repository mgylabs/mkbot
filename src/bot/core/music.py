from discord.ext import commands
from .utils.MGCert import MGCertificate, Level
import discord
from .utils.MsgFormat import MsgFormatter
import requests
from bs4 import BeautifulSoup
import json
import youtube_dl

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
        for i in content[number]['videoRenderer']['title']['runs']:
            self.title += i['text']
        self.channel = content[number]['videoRenderer']['longBylineText']['runs'][0]['text']
        self.published_time = content[number]['videoRenderer']['publishedTimeText']['simpleText']
        self.viewCount = content[number]['videoRenderer']['viewCountText']['simpleText']
        self.length = content[number]['videoRenderer']['lengthText']['simpleText']

    def printSong(self):
        # markdown?
        print()
        return


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    def playMusic(self, ctx, song):
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(song.url, download=False)
            musicFile = info['formats'][0]['url']
        FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
        ctx.voice_client.play(discord.FFmpegPCMAudio(
            musicFile, **FFMPEG_OPTIONS))

    @commands.command(aliases=['p'])
    @MGCertificate.verify(level=Level.TRUSTED_USERS)
    async def play(self, ctx: commands.Context, song=''):
        pass

    @commands.command(aliases=['pp'])
    @MGCertificate.verify(level=Level.TRUSTED_USERS)
    async def pause(self, ctx: commands.Context):
        pass

    @commands.command(aliases=['q'])
    @MGCertificate.verify(level=Level.TRUSTED_USERS)
    async def queue(self, ctx: commands.Context):
        pass

    @commands.command(aliases=['s'])
    @MGCertificate.verify(level=Level.TRUSTED_USERS)
    async def search(self, ctx: commands.Context, song):
        """
        Music command
        """
        # to be moved to another method that manages music play
        if ctx.voice_client == None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send(embed=MsgFormatter.get(ctx, "Usage Error", "You are not in any voice channel. Please join a voice channel to use Music bot."))
                raise commands.CommandError(
                    "Author not connected to a voice channel.")

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
                if ('videoRenderer' in content[a]) and (not 'badges' in content[a]['videoRenderer']):
                    song_ = Song()
                    song_.searchSong(content, a)
                    song_list.append(song_)
                    b += 1
                if b == 4:
                    break
                a += 1
            await ctx.message.delete()
            # to be worked on
            await ctx.send(embed=MsgFormatter.get(ctx, song + ' searched', song_list[0].title + '\n Length: ' + song_list[0].length))
        if discord.VoiceClient.is_playing():
            self.playMusic(ctx, song_list[songQueue])


def setup(bot: commands.Bot):
    bot.add_cog(Music(bot))
