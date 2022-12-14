import itertools

import discord
from discord.ext import commands

from mgylabs.utils.version import VERSION


class CommandHelp(commands.DefaultHelpCommand):
    formatter = None

    def __init__(self, formatter):
        super().__init__(
            no_category="General", paginator=commands.Paginator(None, None)
        )
        if CommandHelp.formatter == None:
            CommandHelp.formatter = formatter

    async def send_bot_help(self, mapping) -> None:
        ctx = self.context
        bot = ctx.bot

        if bot.description:
            # <description> portion
            self.paginator.add_line(bot.description, empty=True)

        no_category = f"\u200b{self.no_category}:"

        def get_category(command, *, no_category=no_category):
            cog = command.cog
            return cog.qualified_name + ":" if cog is not None else no_category

        filtered = await self.filter_commands(bot.commands, sort=True, key=get_category)
        max_size = self.get_max_size(filtered)
        to_iterate = itertools.groupby(filtered, key=get_category)

        # Now we can add the commands to the page.
        for category, cmds in to_iterate:
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

    def get_app_commands_help(self):
        bot = self.context.bot

        cmd_builder = ["Slash Command:"]
        menu_builder = ["Context Menu:"]
        cmds = bot.tree._get_all_commands(guild=self.context.guild)
        for command in cmds:
            if isinstance(command, discord.app_commands.ContextMenu):
                menu_builder.append(f"{self.indent * ' '}`{command.name}`")
            else:
                cmd_builder.append(
                    f"{self.indent * ' '}`/{command.name}` - {command.description}"
                )

        if len(cmd_builder) == 1:
            if self.context.guild is not None:
                cmd_builder.append(
                    f"{self.indent * ' '}⚠️ Slash commands are not set up for use in this guild(ID: {self.context.guild.id}).\n{self.indent * ' '}For more information, See https://github.com/mgylabs/mkbot/wiki/Discord-Bot-User-Guide#activate-slash-commands"
                )
                builder = cmd_builder
            else:
                builder = []
        else:
            builder = cmd_builder + [""] + menu_builder

        return "\n".join(builder)

    def add_indented_commands(self, cmds, *, heading, max_size=None):
        """Indents a list of commands after the specified heading.
        The formatting is added to the :attr:`paginator`.
        The default implementation is the command name indented by
        :attr:`indent` spaces, padded to ``max_size`` followed by
        the command's :attr:`Command.short_doc` and then shortened
        to fit into the :attr:`width`.
        Parameters
        -----------
        commands: Sequence[:class:`Command`]
            A list of commands to indent for output.
        heading: :class:`str`
            The heading to add to the output. This is only added
            if the list of commands is greater than 0.
        max_size: Optional[:class:`int`]
            The max size to use for the gap between indents.
            If unspecified, calls :meth:`get_max_size` on the
            commands parameter.
        """

        if not cmds:
            return

        if len(self.paginator) != 0:
            self.paginator.add_line()

        self.paginator.add_line(heading)
        max_size = max_size or self.get_max_size(cmds)

        for command in cmds:
            name = command.name
            entry = "{0}`{1}` - {2}".format(
                self.indent * " ",
                f"{self.context.clean_prefix}{name}",
                command.short_doc,
            )
            self.paginator.add_line(self.shorten_text(entry))

    async def send_pages(self):
        """A helper utility to send the page output from :attr:`paginator` to the destination."""

        description = "> Mulgyeol MK Bot is an Open Source Local-Hosted Discord Bot\n> Everyone can contribute to MK Bot project on https://github.com/mgylabs/mkbot"
        if VERSION != None:
            version_desc = (
                f"Version {VERSION.base_version}.{VERSION.commit[:7]} Canary\n\n**Be warned: Canary can be unstable.**"
                if VERSION.is_canary()
                else f"Version {VERSION}"
            )
        else:
            version_desc = "Test Mode"

        for page in self.paginator.pages:
            page = page.rstrip()
            await self.context.send(
                f"Mulgyeol MK Bot Help\n{version_desc}\n\n{description}\n\n{page}\n\n© Mulgyeol Labs 2022"
            )
