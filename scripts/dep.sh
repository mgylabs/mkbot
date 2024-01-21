#!/bin/bash
cd "$(dirname "$0")/.."

if [ "$1" == "nlu" ]; then
    poetry install --no-root -E full
else
    poetry install --no-root
fi
