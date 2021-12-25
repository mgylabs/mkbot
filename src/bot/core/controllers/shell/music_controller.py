import queue
import re
import subprocess
import threading
import traceback

import simpleaudio as sa
import youtube_dl
from MGBotBuilder import VirtualCommandConsole
from mgylabs.utils.config import CONFIG

music_controller = VirtualCommandConsole()

song_queue = queue.Queue()
search_pending = []

REPEAT_OPTION_KEY = "shell.music.repeat"


def is_youtube_url(data):
    m = re.match(r"(https:\/\/)?(www[.])?youtube.com\/", data, re.IGNORECASE)
    return bool(m)


def human_info(title, duration):
    human_duration = f"{duration // 60}:{duration % 60}"
    return f"{title} ({human_duration})"


class Song:
    def __init__(self, title, duration, url) -> None:
        self.title = title
        self.duration = duration
        self.url = url
        self.human_info = human_info(self.title, self.duration)


class FFPlayer:
    process = None
    repeat = CONFIG.get(REPEAT_OPTION_KEY, False)
    stop_flag = False

    @classmethod
    def is_playing(cls):
        return cls.process is not None and cls.process.poll() is None

    @classmethod
    def stop(cls):
        if cls.is_playing():
            cls.stop_flag = True
            cls.process.kill()

    @classmethod
    def skip(cls):
        if cls.is_playing():
            cls.process.kill()

    @classmethod
    def play(cls, song: Song, callback):
        if cls.is_playing() and not song_queue.empty():
            return

        try:
            cls.process = subprocess.Popen(
                [
                    "ffplay",
                    "-reconnect",
                    "1",
                    "-reconnect_streamed",
                    "1",
                    "-reconnect_delay_max",
                    "5",
                    "-i",
                    song.url,
                    "-vn",
                    "-autoexit",
                    "-nodisp",
                ],
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            cls.process.wait()
        except FileNotFoundError:
            print("FFPlay not found")
            raise Exception("FFPlay not found")

        if cls.repeat:
            song_queue.put_nowait(song)

        if not cls.stop_flag:
            callback()
        else:
            cls.stop_flag = False


class Player:
    process = None
    player: sa.PlayObject = None

    @classmethod
    def is_process_running(cls):
        return cls.process is not None and cls.process.poll() is None

    @classmethod
    def is_playing(cls):
        return cls.player is not None and cls.player.is_playing()

    @classmethod
    def stop(cls):
        return cls.player is not None and cls.player.stop()

    @classmethod
    def play(cls, music_url):
        if cls.is_process_running():
            cls.process.kill()

        if cls.is_playing():
            cls.player.stop()

        try:
            cls.process = subprocess.Popen(
                [
                    "ffmpeg",
                    "-reconnect",
                    "1",
                    "-reconnect_streamed",
                    "1",
                    "-reconnect_delay_max",
                    "5",
                    "-i",
                    music_url,
                    "-f",
                    "s16le",
                    "-ar",
                    "48000",
                    "-ac",
                    "2",
                    "-loglevel",
                    "warning",
                    "-vn",
                    "pipe:1",
                ],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.PIPE,
            )
        except FileNotFoundError:
            print("FFmpeg not found")
            raise Exception("FFmpeg not found")
        try:
            data = cls.process.stdout.read()
            cls.player = sa.play_buffer(data, 2, 2, 48000)
        except Exception:
            traceback.print_exc()


def add_to_song_queue(send, song: Song):
    if FFPlayer.is_playing():
        song_queue.put_nowait(song)
        send(song.human_info + " in Queue")
    else:
        song_queue.put_nowait(song)
        play_music_safe(send)


def play_music(send):
    try:
        song: Song = song_queue.get_nowait()
    except Exception:
        send("End of Queue")
        return
    send("Now Playing: " + song.human_info)
    try:
        FFPlayer.play(song, lambda: play_music(send))
    except Exception as e:
        send(str(e))

    song_queue.task_done()


class PlayerManager(threading.Thread):
    def __init__(self, send):
        super().__init__()
        self.daemon = True
        self.send = send

    def run(self):
        play_music(self.send)


player_manger: PlayerManager = None


def play_music_safe(send):
    global player_manger
    if player_manger is None or not player_manger.is_alive():
        player_manger = PlayerManager(send)
        player_manger.start()


@music_controller.command("/(play|p)")
def play(ctx):
    play_music_safe(ctx.send)


@music_controller.command("/(play|p) <song>")
def play_song(ctx, song):
    ydl_opts = {
        "noplaylist": True,
        "skip_download": True,
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
        if is_youtube_url(song):
            try:
                info = ydl.extract_info(song, download=False)
            except youtube_dl.utils.DownloadError:
                ctx.send(f"{song} is not a valid URL.")
                return
        else:
            info = ydl.extract_info(f"ytsearch:{song}", download=False,)[
                "entries"
            ][0]

    music_url = info["formats"][0]["url"]
    title: str = info["title"]
    duration: int = info["duration"]

    add_to_song_queue(ctx.send, Song(title, duration, music_url))


@music_controller.command("/(search|s) <text>")
def search(ctx, text):
    global search_pending
    ydl_opts = {
        "noplaylist": True,
        "skip_download": True,
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
        infos = ydl.extract_info(
            f"ytsearch5:{text}",
            download=False,
        )["entries"]

    builder = []
    search_pending = []

    for i, info in enumerate(infos):
        music_url = info["formats"][0]["url"]
        title: str = info["title"]
        duration: int = info["duration"]
        song = Song(title, duration, music_url)

        search_pending.append(song)
        builder.append(f"{i+1}. {song.human_info}")

    ctx.send("\n".join(builder))

    def callback(text: str):
        if text.isdigit():
            s = int(text)
            if 1 <= s <= 5:
                add_to_song_queue(ctx.send, search_pending[s - 1])
                return

        ctx.send("Invalid!")

    ctx.wait_for_response(callback)


@music_controller.command("/stop")
def stop(ctx):
    FFPlayer.stop()
    ctx.send("Stop")


@music_controller.command("/skip")
def skip(ctx):
    FFPlayer.skip()


@music_controller.command("/(queue|q)")
def show_queue(ctx):
    builder = [
        f"{i+1}. {elem.human_info}" for i, elem in enumerate(list(song_queue.queue))
    ]

    if len(builder) == 0:
        ctx.send("Queue\nEmpty!")
    else:
        ctx.send("Queue\n" + "\n".join(builder))


@music_controller.command("/(repeat|r)")
def repeat(ctx):
    if FFPlayer.repeat:
        FFPlayer.repeat = False
        CONFIG[REPEAT_OPTION_KEY] = FFPlayer.repeat
        ctx.send("Repeat mode was deactivated.")
    else:
        FFPlayer.repeat = True
        CONFIG[REPEAT_OPTION_KEY] = FFPlayer.repeat
        ctx.send("Repeat mode was activated.")
