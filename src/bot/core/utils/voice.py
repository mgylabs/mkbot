from discord.ext import commands


async def validate_voice_client(ctx: commands.Context):
    if ctx.voice_client != None:
        return True
    else:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
            return True
        else:
            return False
