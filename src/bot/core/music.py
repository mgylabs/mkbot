import asyncio
import json
import time

import aiohttp
import discord
import youtube_dl
from bs4 import BeautifulSoup
from discord.ext import commands

from .utils import listener
from .utils.MGCert import Level, MGCertificate
from .utils.MsgFormat import MsgFormatter

song_list_dict = dict()


class Song:
    def addSong(self, title, url):
        self.url = url
        self.title = title

    def searchSong(self, content, number):
        self.url = (
            "https://www.youtube.com/watch?v="
            + content[number]["videoRenderer"]["videoId"]
        )
        self.title = ""
        for i in content[number]["videoRenderer"]["title"]["runs"]:
            self.title += i["text"]
        self.channel = content[number]["videoRenderer"]["longBylineText"]["runs"][0][
            "text"
        ]
        self.published_time = content[number]["videoRenderer"]["publishedTimeText"][
            "simpleText"
        ]
        self.viewCount = content[number]["videoRenderer"]["viewCountText"]["simpleText"]
        self.length = content[number]["videoRenderer"]["lengthText"]["simpleText"]


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    async def player(self, ctx: commands.Context):
        if ctx.voice_client == None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
                await self.playMusic(ctx)
            else:
                await ctx.send(
                    embed=MsgFormatter.get(
                        ctx,
                        "Usage Error",
                        "You are not in any voice channel. Please join a voice channel to use Music bot.",
                    )
                )
                raise commands.CommandError("Author not connected to a voice channel.")

    async def playMusic(self, ctx):
        guild_id = ctx.message.guild.id
        try:
            song_list_dict[guild_id][0]
        except KeyError:
            song_list_dict[guild_id] = [0, list()]

        def next():
            if len(song_list_dict[guild_id][1]) > song_list_dict[guild_id][0]:
                song_list_dict[guild_id][0] += 1
                fut = asyncio.run_coroutine_threadsafe(
                    self.playMusic(ctx), self.bot.loop
                )
                try:
                    fut.result()
                except:
                    pass

        try:
            await ctx.send(
                embed=MsgFormatter.get(
                    ctx,
                    "Now Playing",
                    song_list_dict[guild_id][1][song_list_dict[guild_id][0]].title
                    + "  "
                    + song_list_dict[guild_id][1][song_list_dict[guild_id][0]].length,
                )
            )
        except IndexError:
            await ctx.send(
                embed=MsgFormatter.get(
                    ctx,
                    "Skip failed",
                    "You cannot skip because the song Queue is empty.",
                )
            )

        ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(
                None,
                lambda: ydl.extract_info(
                    song_list_dict[guild_id][1][song_list_dict[guild_id][0]].url,
                    download=False,
                ),
            )
            musicFile = info["formats"][0]["url"]
        FFMPEG_OPTIONS = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn",
        }
        try:
            ctx.voice_client.play(
                discord.FFmpegPCMAudio(musicFile, **FFMPEG_OPTIONS),
                after=lambda e: next(),
            )
        except discord.errors.ClientException:
            pass

    @commands.command(aliases=["p"])
    @MGCertificate.verify(level=Level.TRUSTED_USERS)
    async def play(self, ctx: commands.Context, song=""):
        """
        Plays the keyword searched or plays the song in queue
        {commandPrefix}play "keyword"
        {commandPrefix}play
        {commandPrefix}p "keyword"
        {commandPrefix}p
        Searches the keyword in Youtube and puts it in queue
        If there is no keyword inputted and the player isn't playing anything, it starts the player
        """
        guild_id = ctx.message.guild.id
        try:
            song_list_dict[guild_id][0]
        except KeyError:
            song_list_dict[guild_id] = [0, list()]

        if song == "":
            if ctx.voice_client.is_playing:
                await ctx.send(
                    embed=MsgFormatter.get(
                        ctx,
                        "Already Playing",
                        "The player is already playing "
                        + song_list_dict[guild_id][1][
                            song_list_dict[guild_id][0]
                        ].title,
                    )
                )
            elif ctx.voice_client.is_paused():
                ctx.voice_client.resume()
                await ctx.send(
                    embed=MsgFormatter.get(
                        ctx,
                        "Player Resumed",
                        "Now playing: "
                        + song_list_dict[guild_id][1][
                            song_list_dict[guild_id][0]
                        ].title,
                    )
                )
            elif len(song_list_dict[guild_id][1]) == song_list_dict[guild_id][0]:
                await ctx.send(
                    embed=MsgFormatter.get(
                        ctx,
                        "No Song in Queue",
                        "The player doesn't have any song to play. Use {commandPrefix}search to add songs in queue",
                    )
                )
            else:
                await self.playMusic(ctx)
        else:
            if isinstance(song, tuple):
                song = " ".join(song)

            if "youtube.com" in song:
                client_session = aiohttp.ClientSession(raise_for_status=True)
                async with client_session.get(
                    "https://www.youtube.com/results?search_query=" + song
                ) as r:
                    if r.status != 200:
                        raise commands.CommandError("Undefined")
                    text = await r.text()
                soup = BeautifulSoup(text, "lxml")
                title = str(soup.find("title"))[7:-8]
                song_list_dict[guild_id][1].append(Song().addSong(title, song))
                await ctx.message.delete()
                await ctx.send(
                    embed=MsgFormatter.get(
                        ctx, song_list_dict[guild_id][1][-1].title, " in Queue"
                    )
                )
                await self.player(ctx)

            else:
                client_session = aiohttp.ClientSession(raise_for_status=True)
                async with client_session.get(
                    "https://www.youtube.com/results?search_query=" + song
                ) as r:
                    if r.status != 200:
                        raise commands.CommandError("Undefined")
                    text = await r.text()
                soup = BeautifulSoup(text, "lxml")
                J = str(soup.find_all("script")[27])
                J = J.split("var ytInitialData = ")[1].split(";<")[0]

                s = json.loads(J)

                a, b = 0, 0
                while True:
                    content = s["contents"]["twoColumnSearchResultsRenderer"][
                        "primaryContents"
                    ]["sectionListRenderer"]["contents"][0]["itemSectionRenderer"][
                        "contents"
                    ]
                    if ("videoRenderer" in content[a]) and (
                        "badges" not in content[a]["videoRenderer"]
                    ):
                        song_ = Song()
                        song_.searchSong(content, a)
                        song_list_dict[guild_id][1].append(song_)
                        break
                    a += 1
                await ctx.message.delete()
                await ctx.send(
                    embed=MsgFormatter.get(
                        ctx,
                        song + " searched",
                        song_list_dict[guild_id][1][-1].title
                        + "\n Length: "
                        + song_list_dict[guild_id][1][-1].length,
                    )
                )
                await self.player(ctx)

    @commands.command(aliases=["pp"])
    @MGCertificate.verify(level=Level.TRUSTED_USERS)
    async def pause(self, ctx: commands.Context):
        """
        Pauses the song that is playing
        {commandPrefix}pause
        {commandPrefix}pp
        Cannot pause the player if the player is already paused
        """
        guild_id = ctx.message.guild.id
        try:
            song_list_dict[guild_id][0]
        except KeyError:
            song_list_dict[guild_id] = [0, list()]

        if ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send(
                embed=MsgFormatter.get(
                    ctx,
                    "Player Paused",
                    "Paused at: "
                    + song_list_dict[guild_id][1][song_list_dict[guild_id][0]].title,
                )
            )
        else:
            await ctx.send(
                embed=MsgFormatter.get(
                    ctx,
                    "Player Already Paused",
                    "Paused at: "
                    + song_list_dict[guild_id][1][song_list_dict[guild_id][0]].title,
                )
            )

    @commands.command(aliases=["ss"])
    @MGCertificate.verify(level=Level.TRUSTED_USERS)
    async def skip(self, ctx: commands.Context):
        """
        Skips the song that is playing and plays the next song in queue
        {commandPrefix}skip
        {commandPrefix}ss
        """
        guild_id = ctx.message.guild.id
        try:
            song_list_dict[guild_id][0]
        except KeyError:
            song_list_dict[guild_id] = [0, list()]

        if (not ctx.voice_client.is_playing()) and song_list_dict[guild_id][0] == len(
            song_list_dict[guild_id][1]
        ):
            await ctx.send(
                embed=MsgFormatter.get(
                    ctx,
                    "Not Playing Error",
                    "The player isn't playing anything. Add a song to skip.",
                )
            )
        else:
            ctx.voice_client.stop()
            await ctx.send(
                embed=MsgFormatter.get(
                    ctx,
                    "Song Skipped",
                    "Skipped "
                    + song_list_dict[guild_id][1][song_list_dict[guild_id][0]].title,
                )
            )
            await self.playMusic(ctx)

    @commands.command()
    @MGCertificate.verify(level=Level.TRUSTED_USERS)
    async def stop(self, ctx: commands.Context):
        """
        Stops Player
        {commandPrefix}stop
        """
        ctx.voice_client.stop()
        await ctx.send(embed=MsgFormatter.get(ctx, "Player Stopped"))

    @commands.command(aliases=["q"])
    @MGCertificate.verify(level=Level.TRUSTED_USERS)
    async def queue(self, ctx: commands.Context):
        """
        Shows songs in queue
        {commandPrefix}queue
        {commandPrefix}q
        """
        guild_id = ctx.message.guild.id
        try:
            song_list_dict[guild_id][0]
        except KeyError:
            song_list_dict[guild_id] = [0, list()]

        message = ""
        for i in range(len(song_list_dict[guild_id][1]) - song_list_dict[guild_id][0]):
            message += (
                str(i + 1)
                + ". "
                + song_list_dict[guild_id][1][i + song_list_dict[guild_id][0]].title
                + " - "
                + song_list_dict[guild_id][1][i + song_list_dict[guild_id][0]].length
                + "\n"
            )
        await ctx.send(embed=MsgFormatter.get(ctx, "Song Queue", message))

    @commands.command(aliases=["s"])
    @MGCertificate.verify(level=Level.TRUSTED_USERS)
    async def search(self, ctx: commands.Context, *song):
        """
        Searches music in youtube
        {commandPrefix}search "keyword"
        {commandPrefix}s "keyword"
        Shows 5 candidates that you can choose using emotes
        """
        guild_id = ctx.message.guild.id
        try:
            song_list_dict[guild_id][0]
        except KeyError:
            song_list_dict[guild_id] = [0, list()]

        song = " ".join(song)
        reactions = ["1⃣", "2⃣", "3⃣", "4⃣", "5⃣"]

        if song == "":
            await ctx.send(
                embed=MsgFormatter.get(
                    ctx, "No Search Word Error", "Please Enter a word."
                )
            )

        elif "youtube.com" in song:
            client_session = aiohttp.ClientSession(raise_for_status=True)
            async with client_session.get(
                "https://www.youtube.com/results?search_query=" + song
            ) as r:
                if r.status != 200:
                    raise commands.CommandError("Undefined")
                text = await r.text()
            soup = BeautifulSoup(text, "lxml")
            title = str(soup.find("title"))[7:-8]
            song_list_dict[guild_id][1].append(Song().addSong(title, song))
            await ctx.message.delete()
            await ctx.send(
                embed=MsgFormatter.get(
                    ctx, song_list_dict[guild_id][1][-1].title, " in Queue"
                )
            )
            await self.player(ctx)

        else:
            client_session = aiohttp.ClientSession(raise_for_status=True)
            async with client_session.get(
                "https://www.youtube.com/results?search_query=" + song
            ) as r:
                if r.status != 200:
                    raise commands.CommandError("Undefined")
                text = await r.text()
            soup = BeautifulSoup(text, "lxml")
            J = str(soup.find_all("script")[27])
            J = J.split("var ytInitialData = ")[1].split(";<")[0]

            s = json.loads(J)

            a, b = 0, 0
            search_song_list = list()
            while True:
                content = s["contents"]["twoColumnSearchResultsRenderer"][
                    "primaryContents"
                ]["sectionListRenderer"]["contents"][0]["itemSectionRenderer"][
                    "contents"
                ]
                if ("videoRenderer" in content[a]) and (
                    "badges" not in content[a]["videoRenderer"]
                ):
                    song_ = Song()
                    song_.searchSong(content, a)
                    search_song_list.append(song_)
                    b += 1
                if b == 5:
                    break
                a += 1

            async def check_reaction(botmsg, timeout):
                time.sleep(timeout)
                added = False
                cached_msg = discord.utils.get(self.bot.cached_messages, id=botmsg.id)
                for reaction in cached_msg.reactions:
                    if reaction.count >= 2:
                        song_list_dict[guild_id][1].append(
                            search_song_list[reactions.index(str(reaction.emoji))]
                        )
                        added = True
                        await ctx.send(
                            embed=MsgFormatter.get(
                                ctx,
                                "Chose " + song_list_dict[guild_id][1][-1].title,
                                song_list_dict[guild_id][1][-1].title
                                + " - "
                                + song_list_dict[guild_id][1][-1].length
                                + "\n added in queue",
                            )
                        )
                        await self.player(ctx)
                        break
                if not added:
                    await ctx.send(
                        embed=MsgFormatter.get(
                            ctx,
                            "Timeout Error",
                            "No reaction was added. Please add a reaction to choose a song",
                        )
                    )

            timeout = 3

            msg = ""
            for i in range(len(search_song_list)):
                msg += (
                    str(i + 1)
                    + ". "
                    + search_song_list[i].title
                    + " - "
                    + search_song_list[i].length
                    + "\n"
                )
            botmsg = await ctx.send(
                embed=MsgFormatter.get(
                    ctx, f"{song} searched, {timeout} seconds to choose", msg
                )
            )

            for reaction in reactions:
                await botmsg.add_reaction(reaction)

            while timeout > 0:
                await asyncio.sleep(timeout)
                timeout -= 1
                await botmsg.edit(
                    embed=MsgFormatter.get(
                        ctx, f"{song} searched, {timeout} seconds to choose", msg
                    )
                )

            await check_reaction(botmsg, timeout=3)


def setup(bot: commands.Bot):
    bot.add_cog(Music(bot))
