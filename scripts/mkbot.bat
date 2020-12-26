@echo off
setlocal
cd "%~dp0.."

@ If EXIST "build\MKBot.exe" (
    start build\MKBot-OSS.exe --debug
)
endlocal