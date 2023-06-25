#!/bin/bash

pip3 install -r requirements.txt

python3 helper/download_cars_csv.py

GT7_PLAYSTATION_IP=<EDIT ME CONSOLE IP ADDRESS> python3 -m bokeh serve .
