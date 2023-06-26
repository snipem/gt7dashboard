#!/bin/bash

cd "$(dirname "$0")"

pip3 install -r requirements.txt

python3 helper/download_cars_csv.py

GT7_PLAYSTATION_IP=<EDIT_CONSOLE_IP_ADDRESS> python3 -m bokeh serve .
