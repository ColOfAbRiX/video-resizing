#!/bin/bash

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        echo "Virtual environment not found. Running setup first..."
        source setup.sh
    fi
fi

python resize_all.py "$@"
