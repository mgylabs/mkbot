@echo off
cd "%~dp0.."

@ If EXIST "build\MKBot.exe" (
    start build\MKBot.exe --debug
)