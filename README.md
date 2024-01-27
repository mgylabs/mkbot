# Mulgyeol MK Bot

Mulgyeol MK Bot is an open source local-hosted discord bot.  
Self-host discord bot on your own local Windows PC.

[![python](https://img.shields.io/badge/python-3.10-blue)](https://www.python.org/downloads)
[![Build and Test](https://github.com/mgylabs/mkbot/actions/workflows/build.yml/badge.svg)](https://github.com/mgylabs/mkbot/actions/workflows/build.yml)
[![Crowdin](https://badges.crowdin.net/mkbot/localized.svg)](https://crowdin.com/project/mkbot)

<div align="center">
  <a href="https://github.com/mgylabs/mkbot"><img src="https://user-images.githubusercontent.com/58393346/107910325-882aff80-6f9d-11eb-992d-115948014d3b.png" alt="Mulgyeol MK Bot"></a>
</div>

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

### Mulgyeol MK Bot Beta

> Preview upcoming features before they’re released.

- See [Release Note for Beta](https://github.com/mgylabs/mkbot/releases/tag/beta) for downloading beta release

### Mulgyeol MK Bot Canary

> Be warned: Canary can be unstable.

- See [Release Note for Nightly](https://github.com/mgylabs/mkbot/releases/tag/canary) for downloading nightly build

### Build from Source

#### Install dependencies

- Visual Studio Code
- Python 3.10
- [Poetry](https://python-poetry.org/docs/#installing-with-the-official-installer)
- Inno Setup 6.2
- msbuild 16.5

#### Build and Package

1. Enter the following a command in terminal.

```bat
.\scripts\dep.bat
```

2. Go into `vscode`, press <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>B</kbd> and select `build` to start the build task.

3. When `build` task is complete, press <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>B</kbd> again and select `package`.

4. Run `MKBotSetup-Pre.exe` to install `MK Bot`.

> [!Note]
> If you install MK Bot manually, MK Bot will not auto-update when new builds are released so you will need to regularly build and install from source to receive all the latest fixes and improvements.

---

## Contributing

There are many ways in which you can participate in this project, for example:

- [Submit bugs and feature requests](https://github.com/mgylabs/mkbot/issues), and help us verify as they are checked in
- Review [source code changes](https://github.com/mgylabs/mkbot/pulls)

If you are interested in fixing issues and contributing directly to the code base,
please see the document [How to Contribute](https://github.com/mgylabs/mkbot/wiki/How-to-Contribute), which covers the following:

- [How to build and run from source](https://github.com/mgylabs/mkbot/wiki/How-to-Contribute)
- [The development workflow, including debugging and running tests](https://github.com/mgylabs/mkbot/wiki/How-to-Contribute#debugging)
- [Contributing to translations](https://crowdin.com/project/mkbot)

## Development Guide

1. Enter the following commands in terminal.

```bat
.\scripts\dep.bat
.\scripts\prepare.bat
```

2. Edit `config.json`, `mgcert.json` at `src\data` directory.

- config.json

```jsonc
{
  "discordToken": "Your Discord Bot Token",
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

For more infomation, See [Project Wiki](https://github.com/mgylabs/mkbot/wiki/How-to-Contribute).
