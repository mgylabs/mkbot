@echo off
setlocal
cd "%~dp0.."

cd src/bot
poetry run python discord_host.py

endlocal
