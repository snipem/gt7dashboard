@echo off

set GT7_PLAYSTATION_IP=<EDIT ME CONSOLE IP ADDRESS>

pip3 install -r requirements.txt

python helper/download_cars_csv.py

python -m bokeh serve .

pause
