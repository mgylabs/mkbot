import discord
from discord.ext import commands
import asyncio
from APIKey import DISCORD_TOKEN

client = commands.Bot(command_prefix='??')

@client.event
async def on_ready():
    print('Logged in')

@client.command(pass_context = True)
async def delete(ctx, amount):
    channel = ctx.message.channel
    messages = []

    if type(amount) == int:
        await channel.purge(limit=int(amount))
        await channel.send('%d Messages deleted' %amount)
        await asyncio.sleep(3)
        await channel.purge(limit=1)
    
    elif amount == 'all':
        async for message in channel.history(limit=200):
            messages.append(message)
        
        amount = len(messages)
        await channel.purge(limit=amount)
        await channel.send('%d Messages deleted' %amount) 

client.run(DISCORD_TOKEN)