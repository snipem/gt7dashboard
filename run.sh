#!/bin/bash

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info[0])')
PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info[1])')

if [ "$PYTHON_MAJOR" -ne 3 ] || [ "$PYTHON_MINOR" -lt 9 ] || [ "$PYTHON_MINOR" -gt 12 ]; then
    echo "❌ Error: Python version must be between 3.9 and 3.12 (found: $PYTHON_VERSION)"
    exit 1
fi

echo "✓ Python $PYTHON_VERSION detected"

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
