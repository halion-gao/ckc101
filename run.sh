#!/bin/bash
set -e

# Change directory to the workspace directory
cd "$(dirname "$0")"

# Check if venv exists, if not create it
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate venv
echo "Activating virtual environment..."
source .venv/bin/activate

# Install requirements
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Run the Flask app
echo "Starting SRE Flask application on port 19191..."
python3 src/app.py
