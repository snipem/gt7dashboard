#!/bin/bash

# This script should be used on MacOS when Python is a managed environment;
# i.e.: when Python is installed via Homebrew or similar package managers
#
# @author MBDesu

cd "$(dirname "$0")"

python3 -m venv ./venv
source ./venv/bin/activate
python3 -m pip install -r requirements.txt
python3 helper/download_cars_csv.py
python3 -m bokeh serve .
