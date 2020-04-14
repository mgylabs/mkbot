# Discord Bot
Discord Bot developed by Michael Kwon and Mycroft Kang  
API provided by: https://discordapp.com/developers/applications

>  This project is managed by @MGYLBot.

## Features
* TTS voices
* Message Deleter
* Chat Bot

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

## How to Push into Master

1.  Create a New Branch.
2.  Push into the Branch.
3.  Create a New Merge Request.
4.  When you add a `AutoMerge` label to the Merge Request, @MGYLBot will automatically merge it when requirements are met.

[Learn more](https://gitlab.com/mgylabs/developer/taehyeokkang/MGLabsBot/-/wikis/Auto-Merge)
* See also, !3  