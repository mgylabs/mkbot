# Discord Bot
Discord Bot developed by Michael Kwon and Mycroft Kang  
API provided by: https://discordapp.com/developers/applications

>  This project is managed by @MGYLBot.

## Features
* [ ] TTS voices
* [x] Message Deleter
* [ ] Chat Bot

## Auto Deploy

* `Merge Request`를 통해 master 브랜치로 병합되면, 소스코드가 **MK Bot(Server)** 운영서버로 자동 배포됩니다.

## Development Guide

* 소스코드를 Test 할 목적으로 Bot을 실행하려면, **MK Bot(Dev)** 계정을 사용해야 합니다.

1. Enter the following command in terminal.

```
pip install -r requirements.txt
```

2. Make a `APIKey.py` at `src/` directory.

```python
# src/APIKey.py
DISCORD_TOKEN = 'Your Bot TOKEN'
```
Do not push `APIKey.py`.

> :warning: **WARNING**: `.gitlab-ci.yml`, `Procfile`, `runtime.txt`, `requirements.txt` are required when running the program on the server, so errors may occur when changing.

For more infomation, See [Project Wiki](https://gitlab.com/mgylabs/discord-bot/-/wikis/home).

## How to Push into master
>  모든 변경사항은 새로운 브랜치를 만들어 push 한 뒤, master 브랜치로 Merge Request를 생성해야 합니다.

1.  Create a new branch.
2.  Push into the branch.
3.  Create a new Merge Request.
4.  When you add a ~AutoMerge label to the Merge Request, @MGYLBot will automatically merge it when requirements are met.

[Learn more](https://gitlab.com/mgylabs/developer/taehyeokkang/MGLabsBot/-/wikis/Auto-Merge)
* See also, !3  