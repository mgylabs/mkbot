import webbrowser

from MGBotBuilder import CommandConsole

from core.controllers.shell.account_controller import account_controller
from core.controllers.shell.music_controller import music_controller

shell = CommandConsole()


@shell.command("/help")
def show_help(ctx):
    webbrowser.open("https://github.com/mgylabs/mkbot/wiki/Local-Shell-User-Guide")
    ctx.send("Open in browser...")


shell.extend(music_controller)
shell.extend(account_controller)
