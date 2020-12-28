@echo off
setlocal
cd "%~dp0.."
@ If NOT EXIST ".venv" (
    python -m venv .venv
)
call .venv\Scripts\activate
pip install -r requirements.txt
endlocal
