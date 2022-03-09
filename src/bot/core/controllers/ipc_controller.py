import logging
import threading
from urllib.parse import parse_qs, quote, unquote

from core.controllers.shell.music_controller import FFPlayer
from core.services.ipc_serivce import IPCService
from discord_host import BotStateFlags, DiscordBotManger
from MGBotBuilder import Request
from MGBotBuilder.exceptions import CommandNotFoundError
from shell_host import shell

log = logging.getLogger(__name__)

shell_sema = threading.BoundedSemaphore()
discord_sema = threading.BoundedSemaphore()


class IPCController:
    def __init__(self, port) -> None:
        self.discord_manger = None
        self.ipc_service = IPCService()
        self.ipc_service.set_port(port)

    def on_receive(self, data):
        args = parse_qs(data)

        if "shell" in args.get("action"):
            with shell_sema:
                print("By Shell", args.get("request", ""))
                try:
                    shell.bind(
                        Request(
                            "shell",
                            unquote(args.get("request", "")[0]),
                            send=self.send_response,
                            wait_for_response=self.wait_for_response,
                        )
                    )
                except CommandNotFoundError as e:
                    log.debug(e)
                    self.send_response("Command Not Found!")
            return

        with discord_sema:
            if "enableDiscordBot" in args.get("action"):

                def callback(exit_code):
                    self.ipc_service.send(
                        f"action=disableDiscordBot&exitcode={exit_code}"
                    )

                if BotStateFlags.online:
                    return

                self.discord_manger = DiscordBotManger(callback)
                self.discord_manger.start()
                BotStateFlags.online = True
                self.ipc_service.send("action=enableDiscordBot")
            elif "disableDiscordBot" in args.get("action"):
                if not BotStateFlags.online:
                    self.ipc_service.send("action=disableDiscordBot&exitcode=0")
                    return

                with BotStateFlags.Terminate():
                    while self.discord_manger.is_alive():
                        pass

    def send_response(self, data):
        self.ipc_service.send(f"action=shell&response={quote(data)}")

    def on_disconnect(self):
        FFPlayer.stop()

    def wait_for_response(self, callback):
        def outer(text):
            args = parse_qs(text)
            if "shell" in args.get("action"):
                callback(unquote(args.get("request", "")[0]))
            else:
                self.on_receive(text)
                self.ipc_service.wait_for_response(outer)

        self.ipc_service.wait_for_response(outer)

    def run(self):
        self.ipc_service.run(self.on_receive, self.on_disconnect)
