import asyncio
import discord
from discord.ext import commands
import requests
from APIKey import TOKEN
from MGCert import MGCertificate, Level
from MsgFormat import MsgFormatter
import datetime

client = commands.Bot(command_prefix='//')
cert = MGCertificate('../data/mgcert.json')
replyformat = None

def user_bot(m):
    return m.author == client.user

@client.event
async def on_ready():
    print('Logged in')
    global replyformat
    replyformat = MsgFormatter(client.user.avatar_url)
    activity = discord.Game(name="//help로 도움말을 이용하세요", type=3)
    await client.change_presence(status=discord.Status.online, activity=activity)

@client.command(pass_context = True)
@cert.verify()
async def join(ctx):
    """
    명령어를 입력한 유저가 있는 음성 채널을 입장합니다
    """
    channel = ctx.message.channel
    voice_channel = ctx.author.voice.channel
    await voice_channel.connect()
    await ctx.message.delete()
    await channel.send(embed=replyformat.get(ctx, 'joined {}'.format(voice_channel.name, ctx.author.id)))

@client.command(pass_context = True)
@cert.verify()
async def leave(ctx):
    """
    명령어를 입력한 유저가 있는 음성채널을 퇴장합니다
    """
    channel = ctx.message.channel
    voice_channel = ctx.author.voice.channel
    await ctx.message.delete()
    for x in client.voice_clients:
        if(x.guild == ctx.message.guild):
            await x.disconnect()
            await channel.send(embed=replyformat.get(ctx, 'leaved {}'.format(voice_channel.name, ctx.author.id)))

@client.command(pass_context = True)
@cert.verify()
async def delete(ctx, amount):
    """
    메세지를 삭제합니다.
    //delete amount : amount 만큼의 최근 메세지를 삭제합니다.
    //delete all : 모든 메세지(최대 200개)를 삭제합니다.
    """
    channel = ctx.message.channel
    messages = []

    await ctx.message.delete()

    if amount.isdigit():
        await channel.purge(limit=int(amount)+1)
        await channel.send(embed=replyformat.get(ctx, '{} Messages deleted'.format(amount, ctx.author.id)))
    
    elif amount == 'all':
        async for message in channel.history(limit=200):
            messages.append(message)
        
        amount = len(messages)
        await channel.purge(limit=amount)
        await channel.send(embed=replyformat.get(ctx, '{} Messages deleted'.format(amount, ctx.author.id)))

@client.command(pass_context = True)
@cert.verify()
async def tts(ctx, *args):
    """
    TTS 목소리를 사용할 수 있습니다.
    //tts [option] "내용" : 내용에 있는 내용을 말합니다. 내용에 띄어쓰기가 있는 경우에도 큰 따옴표로 감싸지 않아도 됩니다.

    *사용예시*
    //tts "내용"
    //tts -m "내용"
    //tts -w "내용": -m 은 남성 목소리로 말하고 -w 는 여성 목소리로 말합니다. 기본은 남성입니다.
    """
    channel = ctx.message.channel
    url = "kakaoi-newtone-openapi.kakao.com"
    headers = {
        'Content-Type': 'application/xml',
        'Authorization': 'KakaoAK '+TOKEN['KAKAO_REST_TOKEN'],
    }

    if ctx.voice_client == None:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send(embed=replyformat.get(ctx, "Usage Error", "You are not in any voice channel. Please join a voice channel to use TTS."))
            raise commands.CommandError("Author not connected to a voice channel.")
    
    if args[0][0] == '-':
        voice = args[0]
        string = ' '.join(args[1:])
        if voice.upper() == '-M':
            vs = 'MAN_DIALOG_BRIGHT'
        elif voice.upper() == '-W':
            vs = 'WOMAN_DIALOG_BRIGH'
        else:
            await ctx.send(embed=replyformat.get(ctx, "Usage Error", "Invalid parameter. For more information, type `//help tts`."))
            raise commands.CommandError("Error")
    else:
        string = ' '.join(args)
        vs = 'MAN_DIALOG_BRIGHT'
    
    data = '<speak><voice name="{}">{}</voice></speak>'.format(vs, string).encode('utf-8')
    response = requests.post('https://kakaoi-newtone-openapi.kakao.com/v1/synthesize', headers=headers, data=data)
    
    with open('temp.mp3', 'wb') as f:
        f.write(response.content)

    ctx.voice_client.play(discord.FFmpegPCMAudio('temp.mp3'))

    await ctx.message.delete()
    embed = replyformat.get(ctx, string, '[MK Bot](https://gitlab.com/mgylabs/discord-bot) said on behalf of <@{}>'.format(ctx.author.id))
    embed.set_author(name=ctx.message.author.name, icon_url=ctx.message.author.avatar_url)
    await ctx.send(embed=embed)

@client.command(pass_context = True)
@cert.verify(level=Level.ADMIN_USERS)
async def logout(ctx):
    """
    봇을 종료합니다. (관리자 권한 필요)
    """
    await ctx.send(embed=replyformat.get(ctx, "Logs out of Discord and closes all connections"))
    print('Logged out')
    await client.logout()

client.run(TOKEN['DISCORD_TOKEN'])