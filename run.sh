#!/bin/bash

# Virtual environment path (named with postfix to avoid conflicts with other projects)
VENV_DIR=".venv-gt7dashboard"

# Create virtual environment if it doesn't exist yet
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Install dependencies
pip install -r requirements.txt

# Download cars CSV
python helper/download_cars_csv.py

# Run bokeh server
python -m bokeh serve .
