@echo off
setlocal
cd "%~dp0.."
@ If NOT EXIST ".venv" (
    python -m venv .venv
)
poetry install --no-root
endlocal
