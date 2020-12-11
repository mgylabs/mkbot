# Mulgyeol MK Bot

Mulgyeol MK Bot is an open source local-hosted discord Bot.  
Self-host discord bot on your own local Windows PC.

## Features

- [x] TTS voices
- [x] Message Deleter
- [x] Simple Poll
- [x] Roulette
- [x] Translation with Conversation Mode
- [x] Local Hosting
- [x] User Access Control

![docs/preview.png](docs/preview.png)

## Installing

### Mulgyeol MK Bot Stable
* See [Release Note for Stable](https://github.com/mgylabs/mulgyeol-mkbot/releases/latest) for downloading stable release

### Mulgyeol MK Bot Canary
> Be warned: Canary can be unstable.
* See [Release Note for Nightly](https://github.com/mgylabs/mulgyeol-mkbot/releases/latest) for downloading nightly build


## Development Guide

~"Category:Bot" ~"Category:MSU" ~"Category:Console"

1. Enter the following commands in terminal.

```bat
.\scripts\venv.bat
.\scripts\prepare.bat
```

2. Edit `config.json`, `mgcert.json` at `src\data` directory.

- config.json

```json
{
  "discordToken": "Your Bot TOKEN",
  "kakaoToken": "Your KakaoTalk REST API Token",
  "__DEBUG_MODE__": true
}
```

- mgcert.json

```json
{
  "adminUsers": ["admin_username#0000"],
  "trustedUsers": ["trusted_username#0000"]
}
```

---

> :warning: **WARNING**: `.gitlab-ci.yml`, `Procfile`, `runtime.txt`, `requirements.txt` are required when running the program on the server, so errors may occur when changing.

For more infomation, See [Project Wiki](https://gitlab.com/mgylabs/mulgyeol-mkbot/-/wikis/home).
