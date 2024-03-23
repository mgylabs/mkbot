import platform

import discord
from discord.ext import commands

from mgylabs.i18n import __
from mgylabs.utils.config import CONFIG, VERSION

Msg_Color = None


def get_color():
    global Msg_Color
    if Msg_Color == None:
        c = CONFIG.messageColor
        c = c.replace("#", "")
        Msg_Color = int(c, 16)
        return Msg_Color
    else:
        return Msg_Color


def color_to_int(code):
    return int(code.replace("#", ""), 16)


class MsgFormatter:
    avatar_url: str = None

    @staticmethod
    def set_avatar_url(avatar_url):
        MsgFormatter.avatar_url = avatar_url

    @staticmethod
    def get(
        ctx_or_iaction,
        title=None,
        description=None,
        fields: list = [],
        show_req_user=True,
        *,
        thumbnail_url: str = None,
        image_url: str = None,
        color: str = None,
        url: str = None,
    ):
        if color is None:
            color = get_color()
        else:
            color = color_to_int(color)

        if not description:
            description = ""

        embed = discord.Embed(
            title=title,
            description=description.format(commandPrefix=CONFIG.commandPrefix),
            color=color,
            url=url,
            # timestamp=datetime.datetime.utcnow(),
        )

        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)

        if image_url:
            embed.set_image(url=image_url)

        for fd in fields:
            embed.add_field(**fd)

        if show_req_user:
            user_id = None
            if isinstance(ctx_or_iaction, commands.Context):
                user_id = ctx_or_iaction.author.id
            elif isinstance(ctx_or_iaction, discord.Interaction):
                user_id = ctx_or_iaction.user.id

            if user_id:
                embed.add_field(
                    name="Requested by", value="<@{}>".format(user_id), inline=False
                )

        if CONFIG.showFeedbackLink:
            embed.add_field(
                value="[{0}](https://discord.gg/3RpDwjJCeZ)".format(
                    __("Give Feedback ▷")
                ),
                name="",
                inline=False,
            )

        embed.set_footer(
            text="Powered by Mulgyeol MK Bot",
            # icon_url=MsgFormatter.avatar_url,
        )

        return embed

    @staticmethod
    def simple(
        title,
        description=None,
        fields: list = [],
        *,
        thumbnail_url: str = None,
        image_url: str = None,
        color: str = None,
        url: str = None,
    ):
        if color is None:
            color = get_color()
        else:
            color = color_to_int(color)

        if not description:
            description = ""

        embed = discord.Embed(
            title=title,
            description=description.format(commandPrefix=CONFIG.commandPrefix),
            color=color,
            url=url,
        )

        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)

        if image_url:
            embed.set_image(url=image_url)

        for fd in fields:
            embed.add_field(**fd)

        if CONFIG.showFeedbackLink:
            embed.add_field(
                value="[{0}](https://discord.gg/3RpDwjJCeZ)".format(
                    __("Give Feedback ▷")
                ),
                name="",
                inline=False,
            )

        embed.set_footer(
            text="Powered by Mulgyeol MK Bot",
            # icon_url=MsgFormatter.avatar_url,
        )

        return embed

    @staticmethod
    def push(title, description="", fields: list = []):
        embed = discord.Embed(
            title=title,
            description=description,
            color=get_color(),
            # timestamp=datetime.datetime.utcnow(),
        )

        for fd in fields:
            embed.add_field(**fd)

        if CONFIG.showFeedbackLink:
            embed.add_field(
                value="[{0}](https://discord.gg/3RpDwjJCeZ)".format(
                    __("Give Feedback ▷")
                ),
                name="",
                inline=False,
            )

        embed.set_footer(
            text="Powered by Mulgyeol MK Bot",
            # icon_url=MsgFormatter.avatar_url,
        )

        return embed

    @staticmethod
    def abrt(ctx_or_iaction, issue_link, tb, show_req_user=True):
        description = (
            __(
                "ABRT has detected an unknown error.\nPlease [create an issue](%s) at GitHub with below logs to help fix this problem."
            )
            % issue_link
        )
        env = f"Version: {VERSION}\nCommit: {VERSION.commit}\nOS: {platform.platform().replace('-', ' ')}"

        embed = discord.Embed(
            title=f":rotating_light:  {__('Automatic Bug Reporting Tool')}",
            description=f"{description}\n\n```{tb}\n\n{env}```",
            color=color_to_int("#FF0000"),
            # timestamp=datetime.datetime.utcnow(),
        )

        if show_req_user:
            if isinstance(ctx_or_iaction, commands.Context):
                user_id = ctx_or_iaction.author.id
            elif isinstance(ctx_or_iaction, discord.Interaction):
                user_id = ctx_or_iaction.user.id

            embed.add_field(name="Requested by", value="<@{}>".format(user_id))

        if CONFIG.showFeedbackLink:
            embed.add_field(
                value="[{0}](https://discord.gg/3RpDwjJCeZ)".format(
                    __("Give Feedback ▷")
                ),
                name="",
                inline=False,
            )

        embed.set_footer(
            text="Powered by Mulgyeol MK Bot",
            # icon_url=MsgFormatter.avatar_url,
        )
        return embed
