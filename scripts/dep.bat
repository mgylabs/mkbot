@echo off
setlocal
cd "%~dp0.."

@ If /i "%1" == "nlu" (
    poetry install --no-root -E full
) Else (
    poetry install --no-root
)

endlocal
