import itertools

import discord
from discord.ext import commands

from mgylabs.i18n import _L, __
from mgylabs.i18n.utils import get_user_locale_code
from mgylabs.utils.config import CONFIG
from mgylabs.utils.version import VERSION

translate = __


def render_help_text(text: str):
    return text.format(commandPrefix=CONFIG.commandPrefix)


class Paginator(commands.Paginator):
    def add_line(self, line: str = "_ _", *, empty: bool = False) -> None:
        return super().add_line(line, empty=empty)


class CommandHelp(commands.DefaultHelpCommand):
    formatter = None

    def __init__(self, formatter):
        super().__init__(
            show_parameter_descriptions=False,
            paginator=commands.Paginator(None, None),
            command_attrs={"help": _L("Shows this message")},  # Lazy Translate
        )
        if CommandHelp.formatter == None:
            CommandHelp.formatter = formatter

        self.paginator: Paginator = Paginator(prefix=None, suffix=None)

    async def prepare_help_command(self, ctx, command, /) -> None:
        self.arguments_heading = __("Arguments:")
        self.commands_heading = __("Commands:")
        self.default_argument_description = __("No description given")
        self.no_category = __("General")

        return await super().prepare_help_command(ctx, command)

    async def send_bot_help(self, mapping) -> None:
        ctx = self.context
        bot = ctx.bot

        if bot.description:
            # <description> portion
            self.paginator.add_line(bot.description, empty=True)

        note = self.get_opening_note()
        if note:
            self.paginator.add_line(note, empty=True)

        no_category = f"\u200b{self.no_category}:"

        def get_category(command, *, no_category=no_category):
            cog = command.cog
            return cog.qualified_name + ":" if cog is not None else no_category

        def get_category_with_translate(command, *, no_category=no_category):
            cog = command.cog
            return (
                translate(cog.qualified_name) + ":" if cog is not None else no_category
            )

        filtered = await self.filter_commands(bot.commands, sort=True, key=get_category)
        max_size = self.get_max_size(filtered)
        to_iterate = itertools.groupby(filtered, key=get_category_with_translate)

        before_paginator_size = len(self.paginator)
        # Now we can add the commands to the page.
        for category, cmds in to_iterate:
            if len(self.paginator) != before_paginator_size:
                self.paginator.add_line()

            cmds = (
                sorted(cmds, key=lambda c: c.name) if self.sort_commands else list(cmds)
            )
            self.add_indented_commands(cmds, heading=category, max_size=max_size)

        note = self.get_app_commands_help()
        if note:
            self.paginator.add_line()
            self.paginator.add_line(note)

        note = self.get_ending_note()
        if note:
            self.paginator.add_line()
            self.paginator.add_line(note)

        await self.send_pages()

    def get_opening_note(self) -> str:
        description = f"> {__('Mulgyeol MK Bot is an Open Source Local-Hosted Discord Bot.')}\n> {__('Everyone can contribute to MK Bot project on %s.') % '<https://github.com/mgylabs/mkbot>'}"
        if VERSION != None:
            version_desc = (
                f"{__('Version')} {VERSION.base_version}.{VERSION.commit[:7]} Canary\n\n**{__('Be warned: Canary can be unstable.')}**"
                if VERSION.is_canary()
                else f"{__('Version')} {VERSION}"
            )
        else:
            version_desc = "Test Mode"

        return f"Mulgyeol MK Bot {__('Help')}\n{version_desc}\n\n{description}"

    def get_app_commands_help(self):
        bot = self.context.bot

        cmd_builder = [__("Slash Command:")]
        menu_builder = [__("Context Menu:")]
        cmds = bot.tree._get_all_commands()
        for command in cmds:
            if isinstance(command, discord.app_commands.ContextMenu):
                menu_builder.append(f"{self.indent * ' '}- {translate(command.name)}")
            else:
                cmd_builder.append(
                    f"{self.indent * ' '}`/{command.name}` - {render_help_text(translate(command.description))}"
                )

        if len(cmd_builder) == 1:
            if self.context.guild is not None:
                cmd_builder.append(
                    f"{self.indent * ' '}⚠️ {__('Slash commands are not set up for use in this guild(ID: %s).') % self.context.guild.id}\n{self.indent * ' '}{__('For more information, See %s') % '<https://github.com/mgylabs/mkbot/wiki/Discord-Bot-User-Guide#activate-slash-commands>'}"
                )
                builder = cmd_builder
            else:
                builder = []
        else:
            builder = cmd_builder + [""] + menu_builder

        return "\n".join(builder)

    def add_indented_commands(self, cmds, *, heading, max_size=None, prefix=True):
        # """Indents a list of commands after the specified heading.
        # The formatting is added to the :attr:`paginator`.
        # The default implementation is the command name indented by
        # :attr:`indent` spaces, padded to ``max_size`` followed by
        # the command's :attr:`Command.short_doc` and then shortened
        # to fit into the :attr:`width`.
        # Parameters
        # -----------
        # commands: Sequence[:class:`Command`]
        #     A list of commands to indent for output.
        # heading: :class:`str`
        #     The heading to add to the output. This is only added
        #     if the list of commands is greater than 0.
        # max_size: Optional[:class:`int`]
        #     The max size to use for the gap between indents.
        #     If unspecified, calls :meth:`get_max_size` on the
        #     commands parameter.
        # """

        if not cmds:
            return

        self.paginator.add_line(heading)
        max_size = max_size or self.get_max_size(cmds)

        for command in cmds:
            name = command.name
            entry = "{0}`{1}` - {2}".format(
                self.indent * " ",
                f"{self.context.clean_prefix}{name}" if prefix else name,
                render_help_text(translate(command.short_doc)),
            )
            self.paginator.add_line(self.shorten_text(entry))

    def add_command_formatting(self, command: commands.Command, /) -> None:
        # """A utility function to format the non-indented block of commands and groups.

        # .. versionchanged:: 2.0

        #     ``command`` parameter is now positional-only.

        # .. versionchanged:: 2.0
        #     :meth:`.add_command_arguments` is now called if :attr:`.show_parameter_descriptions` is ``True``.

        # Parameters
        # ------------
        # command: :class:`Command`
        #     The command to format.
        # """

        if command.description:
            self.paginator.add_line(command.description, empty=True)

        signature = self.get_command_signature(command)
        self.paginator.add_line(signature, empty=True)

        if command.help:
            try:
                self.paginator.add_line(
                    render_help_text(translate(command.help)), empty=True
                )
            except RuntimeError:
                for line in render_help_text(translate(command.help)).splitlines():
                    self.paginator.add_line(line)
                self.paginator.add_line()

        if self.show_parameter_descriptions:
            self.add_command_arguments(command)

    async def send_group_help(self, group, /) -> None:
        self.add_command_formatting(group)

        filtered = await self.filter_commands(group.commands, sort=self.sort_commands)
        self.add_indented_commands(
            filtered, heading=self.commands_heading, prefix=False
        )

        if filtered:
            note = self.get_ending_note()
            if note:
                self.paginator.add_line()
                self.paginator.add_line(note)

        await self.send_pages()

    def get_ending_note(self) -> str:
        ctx = self.context
        bot = ctx.bot

        command_name = self.invoked_with
        note = (
            __(
                "Type {0} command for more info on a command.\n"
                "You can also type {0} category for more info on a category."
            ).format(f"{self.context.clean_prefix}{command_name}")
            + "_ _\n_ _\n© Mulgyeol Labs 2023"
        )

        if get_user_locale_code(ctx.author.id) == "ko":
            chat_note = (
                f'> **`BETA`** ***"{bot.user.mention} 신나는 음악 틀어줘"*** 와 같이 채팅을 통해 명령어를 사용할 수 있어요!'
                f"\n> 봇을 @멘션({bot.user.mention}) 하고 말을 걸어보세요.\n\n"
            )

            note = chat_note + note

        return note

    async def send_pages(self):
        # """A helper utility to send the page output from :attr:`paginator` to the destination."""
        destination = self.get_destination()
        for page in self.paginator.pages:
            await destination.send(page)
