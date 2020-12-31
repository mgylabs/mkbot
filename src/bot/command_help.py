from discord.ext import commands

from core.utils.config import VERSION


class CommandHelp(commands.DefaultHelpCommand):
    formatter = None

    def __init__(self, formatter):
        super().__init__(
            no_category="General", paginator=commands.Paginator(None, None)
        )
        if CommandHelp.formatter == None:
            CommandHelp.formatter = formatter

    def add_indented_commands(self, commands, *, heading, max_size=None):
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

        if not commands:
            return

        if len(self.paginator) != 0:
            self.paginator.add_line()

        self.paginator.add_line(heading)
        max_size = max_size or self.get_max_size(commands)

        for command in commands:
            name = command.name
            entry = "{0}`{1}` - {2}".format(self.indent * " ", name, command.short_doc)
            self.paginator.add_line(self.shorten_text(entry))

    async def send_pages(self):
        """A helper utility to send the page output from :attr:`paginator` to the destination."""

        description = "> MK Bot is an Open Source Local-Hosted Discord Bot\n> Everyone can contribute to MK Bot project on https://github.com/mgylabs/mulgyeol-mkbot"
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
                f"Mulgyeol MK Bot Help\n{version_desc}\n\n{description}\n\n{page}\n\n© Mulgyeol Labs 2021"
            )
