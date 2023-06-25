$GT7_PLAYSTATION_IP = "<EDIT ME CONSOLE IP ADDRESS>"

pip install -r requirements.txt

python helper/download_cars_csv.py

python -m bokeh serve .

Read-Host -Prompt "Press Enter to continue..."