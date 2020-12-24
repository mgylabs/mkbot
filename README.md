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
* See [Release Note for Nightly](https://github.com/mgylabs/mulgyeol-mkbot/releases/tag/canary) for downloading nightly build

### Build from Source
#### Install dependencies
* Visual Studio Code
* python 3.7
* NSIS 3.x
* msbuild 16.x

#### Build and Package
1. Enter the following a command in terminal.
```bat
.\scripts\venv.bat
```

2. Go into `vscode`, press <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>B</kbd> and select `build` to start the build task.

3. When `build` task is complete, press <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>B</kbd> again and select `package`.

4. Run `package\MKBotSetup.exe` to install `MK Bot`.

> **Note:** If you install MK Bot manually, MK Bot will not auto-update when new builds are released so you will need to regularly build and install from source to receive all the latest fixes and improvements.

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

For more infomation, See [Project Wiki](https://github.com/mgylabs/mulgyeol-mkbot/wiki/How-to-Contribute).
