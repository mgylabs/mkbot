#!/bin/bash

cd "$(dirname "$0")/.."

source .venv/bin/activate

if [ "$1" == "compile" ]; then
    pybabel compile -d locales -D mkbot
else
    python "tools/pygettext.py" -p locales -d mkbot -v -D --no-location src/bot src/lib
    pybabel compile -d locales -D mkbot
fi
