# Discord Bot
Discord Bot developed by Mulgyeol Labs  
API provided by: https://discordapp.com/developers/applications

>  This project is managed by @myftbot

## Features
* [x] TTS voices
* [x] Message Deleter
* [x] Local Hosting
* [x] User Access Control

![docs/preview.png](docs/preview.png)

## Auto Deploy

* `Merge Request`를 통해 master 브랜치로 병합되면, 소스코드가 **MK Bot(Server)** 운영서버로 자동 배포됩니다.

## Development Guide

1. Enter the following command in terminal.

```bat
.\scripts\env.bat
```

2. Make `config.json`, `mgcert.json` at `src/data` directory.
* config.json
```json
{
    "KAKAO_REST_TOKEN":"Your KakaoTalk REST API Token",
    "DISCORD_TOKEN":"Your Bot TOKEN"
}
```
* mgcert.json
```json
{
    "admin_users":["admin_username#0000"],
    "trusted_users":["trusted_username#0000"]
}
```
Do not push `src/data/config.json`, `src/data/mgcert.json`.

> :warning: **WARNING**: `.gitlab-ci.yml`, `Procfile`, `runtime.txt`, `requirements.txt` are required when running the program on the server, so errors may occur when changing.

For more infomation, See [Project Wiki](https://gitlab.com/mgylabs/discord-bot/-/wikis/home).

## How to Push into master
>  모든 변경사항은 새로운 브랜치를 만들어 push 한 뒤, master 브랜치로 Merge Request를 생성해야 합니다.

1.  Create a new branch.
2.  Push into the branch.
3.  Create a new Merge Request.
4.  When you add a ~AutoMerge label to the Merge Request, @myftbot will automatically merge it when requirements are met.

[Learn more](https://gitlab.com/mgylabs/developer/taehyeokkang/MGLabsBot/-/wikis/Auto-Merge)