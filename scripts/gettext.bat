@echo off
setlocal
cd "%~dp0.."

call .venv\Scripts\activate
python "tools/pygettext.py" -p locales -d mkbot -v -D src/bot src/lib
pybabel update -i locales\mkbot.pot -d locales -D mkbot
pybabel compile -d locales -D mkbot

endlocal
