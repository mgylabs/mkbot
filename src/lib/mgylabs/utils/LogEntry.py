import json

from mgylabs.db.models import DiscordBotCommandEventLog, DiscordBotRequestLog


class DiscordRequestLogEntry:
    @classmethod
    def add(cls, ctx, message, user_perm):
        return (
            DiscordBotRequestLog(
                ctx.bot.user.id,
                message.author.id,
                message.id,
                None if message.guild is None else message.guild.id,
                message.channel.id,
                user_perm,
                ctx.command.name,
                ctx.message.content,
                ctx.message.created_at,
            )
            .save()
            .id
        )


class DiscordCommandEventLogEntry:
    @classmethod
    def add(cls, ctx, event, properties={}):
        DiscordBotCommandEventLog(
            request_id=ctx.mkbot_request_id,
            event=event,
            properties=json.dumps(properties),
        ).save()
