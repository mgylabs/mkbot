@echo off
setlocal
cd "%~dp0.."
poetry install --no-root
endlocal
