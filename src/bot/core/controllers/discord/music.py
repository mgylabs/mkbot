import asyncio
from typing import Union

import aiohttp
import discord
from bs4 import BeautifulSoup
from discord.ext import commands
from yt_dlp import YoutubeDL

from .utils.exceptions import NonFatalError, UsageError
from .utils.MGCert import Level, MGCertificate
from .utils.MsgFormat import MsgFormatter
from .utils.voice import validate_voice_client

song_list_dict = dict()


def human_duration(duration):
    if duration is None:
        return "Live"

    duration = int(duration)
    hours, remainder = divmod(duration, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours == 0:
        if minutes == 0:
            human_duration = "0:{:02}".format(int(seconds))
        else:
            human_duration = "{}:{:02}".format(int(minutes), int(seconds))
    else:
        human_duration = "{}:{:02}:{:02}".format(int(hours), int(minutes), int(seconds))

    return human_duration


class Song:
    def addSong(self, title, url, user=None):
        self.url = url
        self.title = title
        self.length = ""
        self.user = user

    def searchSong(self, url, title, length, user=None):
        self.url = url
        self.title = title
        self.length = length
        self.user = user

        return self


async def ytsearch(text, count):
    ls = []

    ydl_opts = {
        "noplaylist": True,
        "skip_download": True,
        "extract_flat": True,
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }
    with YoutubeDL(ydl_opts) as ydl:
        loop = asyncio.get_event_loop()
        infos = await loop.run_in_executor(
            None,
            lambda: ydl.extract_info(
                f"ytsearch{count}:{text}",
                download=False,
            )["entries"],
        )

    for info in infos:
        music_url = info["url"]
        title: str = info["title"]
        duration: int = info["duration"]

        ls.append(Song().searchSong(music_url, title, human_duration(duration)))

    return ls


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    async def player(self, ctx: commands.Context):
        if await validate_voice_client(ctx):
            await self.playMusic(ctx)
        else:
            raise UsageError(
                "You are not in any voice channel. Please join a voice channel to use Music bot."
            )

    async def playMusic(self, ctx: commands.Context, skip=False):
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
                fut.result()

        if not skip:
            try:
                await ctx.send(
                    embed=MsgFormatter.get(
                        ctx,
                        "Now Playing",
                        song_list_dict[guild_id][1][song_list_dict[guild_id][0]].title
                        + "  "
                        + song_list_dict[guild_id][1][
                            song_list_dict[guild_id][0]
                        ].length,
                    )
                )
            except IndexError:
                await ctx.send(
                    embed=MsgFormatter.get(
                        ctx,
                        "End of Song Queue",
                        "The song queue is now empty. Add songs using {commandPrefix}play or {commandPrefix}search to play more",
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
        with YoutubeDL(ydl_opts) as ydl:
            loop = asyncio.get_event_loop()
            try:
                info = await loop.run_in_executor(
                    None,
                    lambda: ydl.extract_info(
                        song_list_dict[guild_id][1][song_list_dict[guild_id][0]].url,
                        download=False,
                    ),
                )
                musicFile = info["url"]
            except IndexError:  # end of queue, after=next error
                raise NonFatalError("End of queue")

        FFMPEG_OPTIONS = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn",
        }
        try:
            source = await discord.FFmpegOpusAudio.from_probe(
                musicFile, **FFMPEG_OPTIONS
            )
            ctx.voice_client.play(
                source,
                after=lambda e: next(),
            )
        except (discord.errors.ClientException, UnboundLocalError) as e:
            raise commands.CommandError(str(e))

    @commands.command(aliases=["p"])
    @MGCertificate.verify(level=Level.TRUSTED_USERS)
    async def play(self, ctx: commands.Context, *song):
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

        if not await validate_voice_client(ctx):
            raise UsageError(
                "You are not in any voice channel. Please join a voice channel to use Music bot."
            )

        if len(song) == 0:
            if ctx.voice_client.is_playing():
                await self.playMusic(ctx)
                await ctx.send(
                    embed=MsgFormatter.get(
                        ctx,
                        "Already Playing",
                        "The player is already playing"
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
            if len(song) > 1:
                song = " ".join(song)
            else:
                song = song[0]

            if "youtube.com" in song:
                if song[:11] != "https://www.":
                    song = "https://www." + song[song.index("y") :]
                async with aiohttp.ClientSession(raise_for_status=True) as session:
                    async with session.get(song) as r:
                        text = await r.text()
                soup = BeautifulSoup(text, "lxml")
                title = str(soup.find("title"))[7:-8]
                song_ = Song()
                song_.addSong(title, song)
                song_list_dict[guild_id][1].append(song_)
                await ctx.message.delete()
                await ctx.send(
                    embed=MsgFormatter.get(
                        ctx, song_list_dict[guild_id][1][-1].title, " in Queue"
                    )
                )
                if not ctx.voice_client.is_playing():
                    await self.player(ctx)

            else:
                ls = await ytsearch(song, 1)
                t = ls[0]
                t.user = ctx.author

                song_list_dict[guild_id][1].append(t)

                await ctx.send(
                    embed=MsgFormatter.get(
                        ctx,
                        song + " in Queue",
                        song_list_dict[guild_id][1][-1].title
                        + "\n Length: "
                        + song_list_dict[guild_id][1][-1].length,
                    )
                )
                if not ctx.voice_client.is_playing():
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
            await self.playMusic(ctx, skip=True)

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
            music = song_list_dict[guild_id][1][i + song_list_dict[guild_id][0]]
            message += (
                f"{str(i + 1)}. `{music.length} `{music.title} - {music.user.mention}\n"
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
        reactions = ["1⃣", "2⃣", "3⃣", "4⃣", "5⃣", "❌"]

        if song == "":
            await ctx.send(
                embed=MsgFormatter.get(
                    ctx, "No Search Word Error", "Please Enter a word."
                )
            )
        else:
            search_msg: discord.Message = await ctx.send(f"🔍 Searching... `{song}`")

            search_song_list = await ytsearch(song, 5)

            for s in search_song_list:
                s.user = ctx.author

            async def check_reaction(botmsg: discord.Message, timeout):
                await asyncio.sleep(timeout)
                added = False
                cached_msg = discord.utils.get(self.bot.cached_messages, id=botmsg.id)
                await botmsg.delete()
                for reaction in cached_msg.reactions:
                    if reaction.count >= 2:
                        added = True
                        if reactions.index(str(reaction.emoji)) == 5:
                            break
                        song_list_dict[guild_id][1].append(
                            search_song_list[reactions.index(str(reaction.emoji))]
                        )
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
                        if not ctx.voice_client.is_playing():
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

            msg = "\n".join(
                f"{reactions[i]} `{search_song_list[i].length}` {search_song_list[i].title}"
                for i in range(len(search_song_list))
            )

            await search_msg.edit(
                content=f"🔍 Search results for `{song}`, choose in 30 seconds."
            )
            botmsg: discord.Message = await ctx.send(
                embed=MsgFormatter.get(ctx, None, msg)
            )

            for reaction in reactions:
                await botmsg.add_reaction(reaction)

            def check(r: discord.Reaction, u: Union[discord.Member, discord.User]):
                return (
                    u.id == ctx.author.id
                    and r.message.channel.id == ctx.channel.id
                    and str(r.emoji) in reactions
                )

            try:
                reaction, _ = await ctx.bot.wait_for(
                    "reaction_add", check=check, timeout=30.0
                )
            except asyncio.TimeoutError:
                return
            else:
                await search_msg.delete()

            await check_reaction(botmsg, timeout=0)


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
