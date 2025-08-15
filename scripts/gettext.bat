@echo off
setlocal
cd "%~dp0.."

call .venv\Scripts\activate

@ If /i "%1" == "compile" (
    pybabel compile -d locales -D mkbot
) Else If /i "%1" == "update" (
    python "tools/pygettext.py" -p locales -d mkbot -v -D --no-location src/bot src/lib
    pybabel update -i locales/mkbot.pot -d locales -D mkbot
) Else (
    python "tools/pygettext.py" -p locales -d mkbot -v -D --no-location src/bot src/lib
    pybabel compile -d locales -D mkbot
)

endlocal
