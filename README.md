# Discord Bot
Discord Bot developed by Michael Kwon and Mycroft Kang  
API provided by: https://discordapp.com/developers/applications

>  This project is managed by @MGYLBot.

## Features
* [ ] TTS voices
* [x] Message Deleter
* [ ] Chat Bot

## Development Guide

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

For more infomation, See [Project Wiki](https://gitlab.com/mgylabs/discord-bot/-/wikis/home).

## How to Push into Dev
>  모든 변경사항은 새로운 브랜치를 만들어 push 한 뒤, Dev 브랜치로 Merge Request를 생성해야 합니다.

1.  Create a new branch.
2.  Push into the branch.
3.  Create a new Merge Request.
4.  When you add a `AutoMerge` label to the Merge Request, @MGYLBot will automatically merge it when requirements are met.

[Learn more](https://gitlab.com/mgylabs/developer/taehyeokkang/MGLabsBot/-/wikis/Auto-Merge)
* See also, !3  