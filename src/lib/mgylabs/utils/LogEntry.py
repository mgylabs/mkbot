import json

import discord
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
                "message",
                ctx.message.content,
                ctx.message.created_at,
            )
            .save()
            .id
        )

    @classmethod
    def add_for_iaction(cls, interaction: discord.Interaction, user_perm):
        return (
            DiscordBotRequestLog(
                interaction.client.user.id,
                interaction.user.id,
                interaction.id,
                None if interaction.guild is None else interaction.guild_id,
                interaction.channel_id,
                user_perm,
                interaction.data["name"],
                "slash",
                json.dumps(interaction.data),
                interaction.created_at,
            )
            .save()
            .id
        )


class DiscordCommandEventLogEntry:
    @classmethod
    def add(cls, ctx, event, properties={}):
        DiscordBotCommandEventLog(
            message_id=ctx.message.id,
            event=event,
            properties=json.dumps(properties),
        ).save()

    @classmethod
    def add_for_iaction(cls, interaction: discord.Interaction, event, properties={}):
        DiscordBotCommandEventLog(
            message_id=interaction.id,
            event=event,
            properties=json.dumps(properties),
        ).save()
