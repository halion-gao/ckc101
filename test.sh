#!/bin/bash
set -e

# Change directory to the workspace directory
cd "$(dirname "$0")"

# Activate venv if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "Virtual environment (.venv) not found. Please run run.sh first to set up the environment, or run:"
    echo "python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Run pytest on the test directory
echo "Running test suite..."
pytest test/
