#!/bin/bash

pip3 install -r requirements.txt

python3 helper/download_cars_csv.py

python3 -m bokeh serve .
