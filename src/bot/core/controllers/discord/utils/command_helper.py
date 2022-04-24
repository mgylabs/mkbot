import discord
from discord.ext import commands


def send(ctx_or_iaction, *args, **kwagrs):
    if isinstance(ctx_or_iaction, commands.Context):
        return ctx_or_iaction.send(*args, **kwagrs)
    elif isinstance(ctx_or_iaction, discord.Interaction):
        return ctx_or_iaction.response.send_message(*args, **kwagrs)
