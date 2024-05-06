import json

import discord
from discord.ext import commands

from mgylabs.db.models import DiscordBotCommandEventLog, DiscordBotRequestLog


def json2str(js: dict):
    return json.dumps(js, ensure_ascii=False, default=str)


class DiscordRequestLogEntry:
    @classmethod
    def add(cls, ctx, message, user_perm):
        return DiscordBotRequestLog.create(
            bot_id=ctx.bot.user.id,
            user_id=message.author.id,
            msg_id=message.id,
            guild_id=None if message.guild is None else message.guild.id,
            channel_id=message.channel.id,
            user_perm=user_perm,
            command=ctx.command.name,
            command_type="message",
            raw=ctx.message.content,
            created_at=ctx.message.created_at,
        ).id

    @classmethod
    def add_for_iaction(cls, interaction: discord.Interaction, user_perm):
        return DiscordBotRequestLog.create(
            bot_id=interaction.client.user.id,
            user_id=interaction.user.id,
            msg_id=interaction.id,
            guild_id=None if interaction.guild is None else interaction.guild_id,
            channel_id=interaction.channel_id,
            user_perm=user_perm,
            command=interaction.data["name"],
            command_type="slash",
            raw=json2str(interaction.data),
            created_at=interaction.created_at,
        ).id

    @classmethod
    def add_for_chat(cls, ctx, message, user_perm, command_name, detail):
        return DiscordBotRequestLog.create(
            bot_id=ctx.bot.user.id,
            user_id=message.author.id,
            msg_id=message.id,
            guild_id=None if message.guild is None else message.guild.id,
            channel_id=message.channel.id,
            user_perm=user_perm,
            command=command_name,
            command_type="chat",
            raw=json2str(detail),
            created_at=ctx.message.created_at,
        ).id


class DiscordEventLogEntry:
    @classmethod
    def Add(cls, ctx_or_msg_id, event, properties={}):
        if isinstance(ctx_or_msg_id, commands.Context):
            cls._add(ctx_or_msg_id, event, properties)
        elif isinstance(ctx_or_msg_id, discord.Interaction):
            cls._add_for_iaction(ctx_or_msg_id, event, properties)
        elif isinstance(ctx_or_msg_id, int):
            cls._add_by_log_id(ctx_or_msg_id, event, properties)
        else:
            raise TypeError("Inappropriate argument type: Context or Interaction only")

    @classmethod
    def _add(cls, ctx, event, properties={}):
        DiscordBotCommandEventLog.create(
            request_id=DiscordBotRequestLog.get_one(msg_id=ctx.message.id).id,
            event=event,
            properties=json2str(properties),
        )

    @classmethod
    def _add_by_log_id(cls, msg_id, event, properties={}):
        DiscordBotCommandEventLog.create(
            request_id=DiscordBotRequestLog.get_one(msg_id=msg_id).id,
            event=event,
            properties=json2str(properties),
        )

    @classmethod
    def _add_for_iaction(cls, interaction: discord.Interaction, event, properties={}):
        DiscordBotCommandEventLog.create(
            request_id=DiscordBotRequestLog.get_one(msg_id=interaction.id).id,
            event=event,
            properties=json2str(properties),
        )
