# Mulgyeol MK Bot

Mulgyeol MK Bot is an open source local-hosted discord Bot.  
Self-host discord bot on your own local Windows PC.

<div align="center">
  <a href="https://github.com/mgylabs/mkbot"><img src="https://user-images.githubusercontent.com/58393346/107910325-882aff80-6f9d-11eb-992d-115948014d3b.png" alt="Mulgyeol MK Bot"></a>
</div>

[![Crowdin](https://badges.crowdin.net/mkbot/localized.svg)](https://crowdin.com/project/mkbot)

## Features

- [x] TTS voices
- [x] Message Deleter
- [x] Simple Poll
- [x] Roulette
- [x] Translation with Conversation Mode
- [x] Music
- [x] Local Hosting
- [x] User Access Control

![docs/preview.png](https://user-images.githubusercontent.com/58393346/107910752-58c8c280-6f9e-11eb-969f-0b3c96f45221.png)

## Installing

### Mulgyeol MK Bot Stable

- See [Release Note for Stable](https://github.com/mgylabs/mkbot/releases/latest) for downloading stable release

### Mulgyeol MK Bot Canary

> Be warned: Canary can be unstable.

- See [Release Note for Nightly](https://github.com/mgylabs/mkbot/releases/tag/canary) for downloading nightly build

### Build from Source

#### Install dependencies

- Visual Studio Code
- Python 3.10
- Inno Setup 6.2
- msbuild 16.5

#### Build and Package

1. Enter the following a command in terminal.

```bat
.\scripts\venv.bat
```

2. Go into `vscode`, press <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>B</kbd> and select `build` to start the build task.

3. When `build` task is complete, press <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>B</kbd> again and select `package`.

4. Run `MKBotSetup-Pre.exe` to install `MK Bot`.

> **Note**  
> If you install MK Bot manually, MK Bot will not auto-update when new builds are released so you will need to regularly build and install from source to receive all the latest fixes and improvements.

## Development Guide

1. Enter the following commands in terminal.

```bat
.\scripts\venv.bat
.\scripts\prepare.bat
```

2. Edit `config.json`, `mgcert.json` at `src\data` directory.

- config.json

```jsonc
{
  "discordToken": "Your Discord Bot Token",
  "discordAppCmdGuilds": [123456789123456789],  //Your Discord Guild ID
  "kakaoToken": "Your KakaoTalk REST API Token"
}
```

- mgcert.json

```jsonc
{
  "adminUsers": ["admin_username#0000"],
  "trustedUsers": ["trusted_username#0000"]
}
```

---

For more infomation, See [Project Wiki](https://github.com/mgylabs/mkbot/wiki/How-to-Contribute).
