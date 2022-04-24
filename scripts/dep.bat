@echo off
setlocal
cd "%~dp0.."

@ If /i "%1" == "dpy" (
    pip install -U git+https://github.com/Rapptz/discord.py.git@master
)

endlocal
