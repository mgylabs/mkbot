import discord
import asyncio
from APIKey import DISCORD_TOKEN

class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as', self.user)

    async def on_message(self, message):
        # don't respond to ourselves
        if message.author == self.user:
            return

        print('{}: {}'.format(message.author, message.content))
        
        if message.content == 'ping':
            await message.channel.send('pong')
        elif message.content == 'Hello':
            await message.channel.send('Hello, {}!'.format(message.author))

client = MyClient()
client.run(DISCORD_TOKEN)