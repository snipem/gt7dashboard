# gt7telemetry
Python script to display GT7 telemetry data.

**Needs to be run from the terminal**, and works best with a terminal of at least 92 x 42 characters. The output is in a separate buffer, but you can comment out lines 10-29 to just write to your current terminal (might want to clear the terminal first).

Run like this (substitute with your own console's LAN IP address):

    python3 gt7telemetry.py 129.168.1.123

This work is based purely on the shoulders of others. Python script originally from https://github.com/lmirel/mfc/blob/master/clients/gt7racedata.py

Thanks to the help of the people of GTPlanet, specifically the thread https://www.gtplanet.net/forum/threads/gt7-is-compatible-with-motion-rig.410728 and people like Nenkai, Stoobert and more.

If anyone can gain anything from this, feel free to do so!!

![Screenshot of output](https://user-images.githubusercontent.com/3602224/182450262-56992d54-409d-4fb7-bfec-35b04dc7f6aa.png)

## Requirements
You will need python 3.x installed, and you need to install the salsa20 module via pip:

    pip3 install salsa20
