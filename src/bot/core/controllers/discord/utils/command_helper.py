import discord
from discord.ext import commands

cmd_dict = None


class AppCommandDict:
    cmd_dict: dict = {}

    @classmethod
    def parse(cls, app_cmds: list[discord.app_commands.AppCommand]):
        for cmd in app_cmds:
            if cmd.type == discord.AppCommandType.chat_input:
                cls.cmd_dict[cmd.name] = cmd
                if cmd.options:
                    cls.cmd_dict.update(
                        {
                            sub.qualified_name: sub
                            for sub in cmd.options
                            if isinstance(sub, discord.app_commands.AppCommandGroup)
                        }
                    )

    @classmethod
    def get(cls, name: str) -> discord.app_commands.AppCommand:
        return cls.cmd_dict.get(name)


def get_command_mention_or_name(bot: commands.Bot, cmds: list[str]):
    app_commands = []
    msg_commands = []

    cmds = sorted(cmds)

    for name in cmds:
        if cmd := AppCommandDict.get(name):
            app_commands.append(cmd.mention)
            continue

        if cmd := bot.get_command(name):
            msg_commands.append(f"`{bot.command_prefix}{cmd.qualified_name}`")
            continue

    return app_commands + msg_commands


def send(ctx_or_iaction, *args, push=False, **kwagrs):
    if isinstance(ctx_or_iaction, commands.Context):
        if push:
            return ctx_or_iaction.channel.send(*args, **kwagrs)
        else:
            return ctx_or_iaction.send(*args, **kwagrs)
    elif isinstance(ctx_or_iaction, discord.Interaction):
        if push:
            return ctx_or_iaction.channel.send(*args, **kwagrs)
        else:
            return ctx_or_iaction.response.send_message(*args, **kwagrs)
