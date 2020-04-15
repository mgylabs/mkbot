import asyncio
import discord
from discord.ext import commands
import requests
from APIKey import DISCORD_TOKEN, KAKAO_REST_TOKEN

client = commands.Bot(command_prefix='$$')

def user_bot(m):
    return m.author == client.user

@client.event
async def on_ready():
    print('Logged in')

@client.command(pass_context = True)
async def join(ctx):
    channel = ctx.message.channel
    voice_channel = ctx.author.voice.channel
    await voice_channel.connect()
    await channel.send('joined %s' %voice_channel.name)
    await asyncio.sleep(3)
    await channel.purge(limit=10, check=user_bot)

@client.command(pass_context = True)
async def leave(ctx):
    channel = ctx.message.channel
    voice_channel = ctx.author.voice.channel
    await voice_channel.disconnect()
    await channel.send('leaved %s' %voice_channel.name)
    await asyncio.sleep(3)
    await channel.purge(limit=10, check=user_bot)

@client.command(pass_context = True)
async def joinhere(ctx):
    channel = ctx.message.channel
    voice_channel = ctx.author.voice.channel
    await voice_channel.move_to(voice_channel.id)

@client.command(pass_context = True)
async def delete(ctx, amount):
    channel = ctx.message.channel
    messages = []

    if amount.isdigit:
        await channel.purge(limit=int(amount))
        await channel.send('%s Messages deleted' %amount)
        await asyncio.sleep(3)
        await channel.purge(limit=10, check=user_bot)
    
    elif amount == 'all':
        async for message in channel.history(limit=200):
            messages.append(message)
        
        amount = len(messages)
        await channel.purge(limit=amount)
        await channel.send('%s Messages deleted' %amount) 
        await asyncio.sleep(3)
        await channel.purge(limit=10, check=user_bot)

@client.command(pass_context = True)
async def tts(ctx, content):
    channel = ctx.message.channel
    voice_channel = ctx.author.voice.channel

    url = "kakaoi-newtone-openapi.kakao.com"
    headers = {
        'Host': 'kakaoi-newtone-openapi.kakao.com/v1/synthesize',
        'Content-Type': 'application/xml',
        'X-DSS-Service': 'DICTATION',
        'Authorization': 'KakaoAK '+KAKAO_REST_TOKEN,
    }
    data = {'<speak>그는 그렇게 말했습니다.<voice name': '"MAN_DIALOG_BRIGHT">잘 지냈어? 나도 잘 지냈어.</voice><voice name="WOMAN_DIALOG_BRIGHT" speechStyle="SS_ALT_FAST_1">금요일이 좋아요.</voice></speak>'}
    response = requests.post('https://kakaoi-newtone-openapi.kakao.com/v1/synthesize', headers=headers, data=data)
    
    #join the voice channel and play
    if voice_channel != None:
        vc = await voice_channel.connect()
        vc.play(discord.FFmmpegPCMAudio('response'))
        if not vc.is_playing():
            await asyncio.sleep(3)
        vc.stop()
        await vc.disconnect()
    else:
        await channel.send('You are not in any voice channel. Please join a voice channel to use TTS')





client.run(DISCORD_TOKEN)