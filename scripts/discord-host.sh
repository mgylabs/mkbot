#!/bin/bash

cd "$(dirname "$0")/.."

cd src/bot
poetry run python discord_host.py
