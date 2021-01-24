from discord.ext import commands


class NonFatalError(commands.CommandError):
    def __init__(self, *args):
        super().__init__(*args)


class UsageError(commands.CommandError):
    def __init__(self, *args):
        super().__init__(*args)
