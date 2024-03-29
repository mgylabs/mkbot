import asyncio
from typing import Union

import aiohttp
import discord
from bs4 import BeautifulSoup
from discord.ext import commands
from yt_dlp import YoutubeDL

from core.controllers.discord.utils import Emoji
from mgylabs.db import database
from mgylabs.i18n import I18nExtension, __
from mgylabs.utils import logger

from .utils.exceptions import UsageError
from .utils.MGCert import Level, MGCertificate
from .utils.MsgFormat import MsgFormatter
from .utils.voice import validate_voice_client

log = logger.get_logger(__name__)

guild_sl = dict()


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


class SongList:
    def __init__(self, guildID):
        self.queue = 0
        self.guildID = guildID
        self.slist = list()
        self.auto = False

    # if song exists in songList (initialized)
    def songExists(self):
        if len(self.slist) > 0:
            return True
        else:
            return False

    # add song to list
    def addSong(self, song):
        self.slist.append(song)

    # return song that is playing
    def songPlaying(self):
        return self.slist[self.queue]

    # next song to be played
    def songNext(self):
        return self.slist[self.queue + 1]

    def lastSong(self):
        return self.slist[-1]


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


async def nextSong(gid, bot):
    # fetch next song from yt, then return as Song

    song_url = guild_sl[gid].songPlaying().url

    async def open_song():
        async with aiohttp.ClientSession() as session:
            async with session.get(song_url) as resp:
                soup = BeautifulSoup(await resp.read(), "lxml")
                b = soup.find_all("script")[-5]
                J1 = str(b).split("var ytInitialData = ")
                u = J1[1].find("url")
                next_url = "https://youtube.com" + J1[1][u + 6 : u + 26]
        return next_url

    next_url = await open_song()
    song_ = (await ytsearch(next_url, 1))[0]
    song_.user = bot
    guild_sl[gid].addSong(song_)
    return song_


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
        self.tmp_id = {}

    async def player(self, ctx: commands.Context):
        if await validate_voice_client(ctx):
            await self.playMusic(ctx)
        else:
            raise UsageError(
                __(
                    "You are not in any voice channel. Please join a voice channel to use Music bot."
                )
            )

    async def playMusic(self, ctx: commands.Context, skip=False):
        gid = ctx.message.guild.id
        try:
            guild_sl[gid]
        except KeyError:
            sl = SongList(gid)
            guild_sl[gid] = sl

        @database.using_database
        def next():
            I18nExtension.set_current_locale_by_user(ctx.author.id)

            async def next_task():
                # no more songs left to play
                if (
                    len(guild_sl[gid].slist) <= guild_sl[gid].queue + 1
                    and guild_sl[gid].auto
                ):
                    await nextSong(gid, self.bot.user)

                guild_sl[gid].queue += 1
                await self.playMusic(ctx)

            # enough songs to play
            if len(guild_sl[gid].slist) > guild_sl[gid].queue or guild_sl[gid].auto:
                fut = asyncio.run_coroutine_threadsafe(next_task(), self.bot.loop)
                fut.result()

        if not skip:
            try:
                await ctx.send(
                    embed=MsgFormatter.get(
                        ctx,
                        __("Now Playing"),
                        guild_sl[gid].songPlaying().title
                        + "  "
                        + guild_sl[gid].songPlaying().length,
                    )
                )
            except IndexError:
                await ctx.send(
                    embed=MsgFormatter.get(
                        ctx,
                        __("End of Song Queue"),
                        __(
                            "The song queue is now empty. Add songs using {commandPrefix}play or {commandPrefix}search to play more"
                        ),
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
                        guild_sl[gid].songPlaying().url,
                        download=False,
                    ),
                )
                musicFile = info["url"]
            except IndexError:  # end of queue, after=next error
                log.info("End of queue")
                return

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

        {commandPrefix}play -auto "keyword"
        {commandPrefix}play -a "keyword"
        Turns autoplay on and automatically plays next song
        """
        gid = ctx.message.guild.id
        self.tmp_id[gid] = ctx.message.channel.id
        try:
            guild_sl[gid]
        except KeyError:
            sl = SongList(gid)
            guild_sl[gid] = sl

        if not await validate_voice_client(ctx):
            raise UsageError(
                __(
                    "You are not in any voice channel. Please join a voice channel to use Music bot."
                )
            )

        if "-auto" in song or "-a" in song:
            guild_sl[gid].auto = True
            song = song[1:]
            await ctx.send(
                embed=MsgFormatter.get(
                    ctx,
                    __("Autoplay turned on"),
                    __("Next song will be automatically recommended"),
                )
            )

        elif "-off" in song or "-o" in song:
            guild_sl[gid].auto = False
            song = song[1:]
            await ctx.send(
                embed=MsgFormatter.get(
                    ctx,
                    __("Autoplay turned off"),
                    __("Next song will not be automatically recommended"),
                )
            )

        if len(song) == 0:
            if ctx.voice_client.is_playing():
                await self.playMusic(ctx)
                await ctx.send(
                    embed=MsgFormatter.get(
                        ctx,
                        __("Already Playing"),
                        __("The player is already playing")
                        + guild_sl[gid].songPlaying().title,
                    )
                )
            elif ctx.voice_client.is_paused():
                ctx.voice_client.resume()
                await ctx.send(
                    embed=MsgFormatter.get(
                        ctx,
                        __("Player Resumed"),
                        __("Now playing: %s") % guild_sl[gid].songPlaying().title,
                    )
                )
            elif len(guild_sl[gid].slist) == guild_sl[gid].queue:
                await ctx.send(
                    embed=MsgFormatter.get(
                        ctx,
                        __("No Song in Queue"),
                        __(
                            "The player doesn't have any song to play. Use {commandPrefix}search to add songs in queue"
                        ),
                    )
                )
            else:
                await self.playMusic(ctx)
        else:
            if len(song) > 1:
                song = " ".join(song)
            else:
                song = song[0]

            ls = await ytsearch(song, 1)
            t = ls[0]
            t.user = ctx.author

            guild_sl[gid].addSong(t)

            await ctx.send(
                embed=MsgFormatter.get(
                    ctx,
                    __("%s in Queue") % song,
                    __("{title}\n Length: {length}").format(
                        title=guild_sl[gid].lastSong().title,
                        length=guild_sl[gid].lastSong().length,
                    ),
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
        gid = ctx.message.guild.id
        try:
            guild_sl[gid]
        except KeyError:
            sl = SongList(gid)
            guild_sl[gid] = sl

        if ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send(
                embed=MsgFormatter.get(
                    ctx,
                    __("Player Paused"),
                    __("Paused at: %s") % guild_sl[gid].songPlaying().title,
                )
            )
        else:
            await ctx.send(
                embed=MsgFormatter.get(
                    ctx,
                    __("Player Already Paused"),
                    __("Paused at: %s") % guild_sl[gid].songPlaying().title,
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
        gid = ctx.message.guild.id
        try:
            guild_sl[gid]
        except KeyError:
            sl = SongList(gid)
            guild_sl[gid] = sl

        if (not ctx.voice_client.is_playing()) and guild_sl[gid].queue == len(
            guild_sl[gid].slist
        ):
            await ctx.send(
                embed=MsgFormatter.get(
                    ctx,
                    __("Not Playing Error"),
                    __("The player isn't playing anything. Add a song to skip."),
                )
            )
        else:
            ctx.voice_client.stop()

    @commands.command()
    @MGCertificate.verify(level=Level.TRUSTED_USERS)
    async def stop(self, ctx: commands.Context):
        """
        Stops Player
        {commandPrefix}stop
        """
        ctx.voice_client.stop()
        ctx.voice_client.pause()
        await ctx.send(embed=MsgFormatter.get(ctx, __("Player Stopped")))

    @commands.command(aliases=["q"])
    @MGCertificate.verify(level=Level.TRUSTED_USERS)
    async def queue(self, ctx: commands.Context):
        """
        Shows songs in queue
        {commandPrefix}queue
        {commandPrefix}q
        """
        gid = ctx.message.guild.id
        try:
            guild_sl[gid]
        except KeyError:
            sl = SongList(gid)
            guild_sl[gid] = sl

        message = ""
        for i in range(len(guild_sl[gid].slist) - guild_sl[gid].queue):
            music = guild_sl[gid].slist[i + guild_sl[gid].queue]
            message += (
                f"{str(i + 1)}. `{music.length}`{music.title} - {music.user.mention}\n"
            )
        await ctx.send(embed=MsgFormatter.get(ctx, __("Song Queue"), message))

    @commands.command(aliases=["s"])
    @MGCertificate.verify(level=Level.TRUSTED_USERS)
    async def search(self, ctx: commands.Context, *song):
        """
        Searches music in youtube
        {commandPrefix}search "keyword"
        {commandPrefix}s "keyword"
        Shows 5 candidates that you can choose using emotes
        """
        gid = ctx.message.guild.id
        self.tmp_id[gid] = ctx.message.channel.id
        try:
            guild_sl[gid]
        except KeyError:
            sl = SongList(gid)
            guild_sl[gid] = sl

        song = " ".join(song)
        reactions = ["1⃣", "2⃣", "3⃣", "4⃣", "5⃣", "❌"]

        if song == "":
            await ctx.send(
                embed=MsgFormatter.get(
                    ctx, __("No Search Word Error"), __("Please Enter a word.")
                )
            )
        else:
            search_msg: discord.Message = await ctx.send(
                f"{Emoji.typing} " + __("Searching... `%s`") % song
            )

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
                        guild_sl[gid].addSong(
                            search_song_list[reactions.index(str(reaction.emoji))]
                        )
                        await ctx.send(
                            embed=MsgFormatter.get(
                                ctx,
                                __("Chose %s") % guild_sl[gid].lastSong().title,
                                __("{title} - {length}\nadded in queue").format(
                                    title=guild_sl[gid].lastSong().title,
                                    length=guild_sl[gid].lastSong().length,
                                ),
                            )
                        )
                        if not ctx.voice_client.is_playing():
                            await self.player(ctx)
                        break
                if not added:
                    await ctx.send(
                        embed=MsgFormatter.get(
                            ctx,
                            __("Timeout Error"),
                            __(
                                "No reaction was added. Please add a reaction to choose a song"
                            ),
                        )
                    )

            msg = "\n".join(
                f"{reactions[i]} `{search_song_list[i].length}` {search_song_list[i].title}"
                for i in range(len(search_song_list))
            )

            await search_msg.edit(
                content=__("🔍 Search results for `%s`, choose in 30 seconds.") % song
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

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not before.channel or before.channel.guild.id not in self.tmp_id:
            return

        channel = before.channel.guild.get_channel(self.tmp_id[before.channel.guild.id])
        if not member.id == self.bot.user.id:
            if after.channel is None:
                voice = before.channel.guild.voice_client
                if voice.is_playing() and not voice.is_paused():
                    await voice.disconnect()
                    await channel.send(
                        embed=MsgFormatter.get(
                            self,
                            __("left {} due to inactivity").format(before.channel.name),
                            show_req_user=False,
                        )
                    )
                else:
                    await voice.disconnect()
                    await channel.send(
                        embed=MsgFormatter.get(
                            self,
                            __("left {} due to inactivity").format(before.channel.name),
                            show_req_user=False,
                        )
                    )
        else:
            # bot forcefully disconnected
            await channel.send(
                embed=MsgFormatter.get(
                    self,
                    __("left {}").format(before.channel.name),
                    show_req_user=False,
                ),
            )


# @register_intent("command::music::play", "play")
# def cmd_play(intent: Intent):
#     if query := intent.get_an_entity("music_query"):
#         return f"play {query}"
#     else:
#         return "play"


# @register_intent("command::music::skip", "skip")
# def cmd_skip(intent: Intent):
#     return "skip"


# @register_intent("command::music::stop", "stop")
# def cmd_stop(intent: Intent):
#     return "stop"


async def setup(bot: commands.Bot):
    """Music"""
    await bot.add_cog(Music(bot))
