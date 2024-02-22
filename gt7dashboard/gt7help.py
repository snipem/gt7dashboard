from bokeh.models import Div

from gt7dashboard import gt7helper

SPEED_VARIANCE = f"""Displays the speed deviation of the fastest laps within a {gt7helper.DEFAULT_FASTEST_LAPS_PERCENT_THRESHOLD * 100}% time difference threshold of the fastest lap.
Replay laps are ignored. The speed deviation is calculated as the standard deviation between these fastest laps.

With a perfect driver in an ideal world, this line would be flat. In a real world situation, you will get an almost flat line, 
with bumps at the corners and long straights. This is where even your best laps deviate.

You may get some insights for improvement on your consistency if you look at the points of the track where this line is bumpy.

The list on the right hand side shows your best laps that are token into consideration for the speed variance.
"""

HEADER = """The red or green button reflects the current connection status to Gran Turismo 7. i.e. if there was a packet received successfully in the last second, the button will turn green.

Next is a brief description of the last and reference lap. The reference lap can be selected on the right side."""
RACE_LINE_MINI = """This is a race line map with the last lap (blue) and the reference lap (magenta). Zoom in for more details.

This map is helpful if you are using the index number of a graph to quickly determine where in the lap a measurement was taken.

See the tab 'Race Line' for a more detailed race line."""
MANUAL_CONTROLS = """'Log Lap Now' will log a lap now even you have not crossed the finished line. This is helpful for missions or license tests where the end of a test is not necessarily identical with the finish line.

The checkbox 'Record Replays' will allow you to record replays. Be careful since also background action before and after a time trial is counted as a replay. This is when a car drives on the track in the background of the menu.

In the 'Best Lap' dropdown list you can select the reference lap. Usually this will point to the best lap of the session.
"""

TIME_DIFF = """ This is a graph for showing the relative time difference between the last lap and the reference lap.
Everything under the solid bar at 0 is slower than the reference lap. Everything above is slower than the reference lap.

If you see a bump in this graph to the top or the bottom this means that you were slower or faster at this point respectively.
"""
LAP_CONTROLS = """You can reset all laps with the 'Reset Laps' button. This is helpful if you are switching tracks or cars in a session. Otherwise the different tracks will mix in the dashboard.
'Save Laps' will save your recorded laps to a file. You can load the laps afterwards with the dropdown list to the right."""
SPEED_DIAGRAM = """The total speed of the laps selected. This value is in km/h. or mph. depending on your in-game setting"""
THROTTLE_DIAGRAM = """This is the amount of throttle pressure from 0% to 100% of the laps selected."""
BRAKING_DIAGRAM = """This is the amount of braking pressure from 0% to 100% of the laps selected."""
COASTING_DIAGRAM = """This is the amount of coasting from 0% to 100% of the laps selected. Coasting is when neither throttle nor brake are engaged."""
GEAR_DIAGRAM = """This is the current gear of the laps selected."""
RPM_DIAGRAM = "This is the current RPM of the laps selected."
BOOST_DIAGRAM = "This is the current Boost in x100 kPa of the laps selected."
TIRE_DIAGRAM = """This is the relation between the speed of the tires and the speed of the car. If your tires are faster than your car, your tires might be spinning. If they are slower, your tires might be blocking. Use this judge your car control."""

SPEED_PEAKS_AND_VALLEYS = """A list of speed peaks and valleys for the selected laps. We assume peaks are straights (s) and valleys are turns (T). Use this to compare the difference in speed between the last lap and the reference lap on given positions of the race track."""
TIME_TABLE = """A table with logged information of the session. # is the number of the lap as reported by the game. There might be multiple laps of the same number if you restarted a session. Time and Diff are self-explaining. Info will hold additional meta data, for example if this lap was a replay.
Fuel Consumed is the amount of fuel consumed in the lap.

What follows know are simple metrics for the characteristics of the lap. This is counted as ticks, which means instances when the game reported a state. For example Full Throttle = 500 means that you were on full throttle during 500 instances when the game sent its telemetry.
The same goes for Full Break, Coast and Tire Spin. Use this to easily compare your laps.

You can click on one of these laps to add them to the diagrams above. These laps will be deleted if you reset the view or reload the page.

Car will hold the car name. You will have to have the `db/cars.csv` file downloaded for this to work.
"""
FUEL_MAP = """This fuel map will help to determine the fuel setting of your car. The game does not report the current fuel setting, so this map is relative.
The current fuel setting will always be at 0. If you want to change the fuel to a leaner setting count downwards with the amount of steps left. For example: If you are at fuel setting 2 in the game and want to go to the games fuel setting 5, have a look at Fuel Lvl. 3 in this map.
It will give you a raw assumption of the laps and time remaining and the assumed time difference in lap time for the new setting."""
TUNING_INFO = """Here is some useful information you may use for tuning. Such as Max Speed and minimal body height in relation to the track. The later seems to be helpful when determining the possible body height."""

RACE_LINE_BIG = """This is a race line map with the last lap (blue) and the reference lap (magenta). This diagram does also feature spead peaks (▴) and valleys (▾) as well as throttle, brake and coasting zones.

The thinner line of the two is your last lap. The reference line is the thicker translucent line. If you want to make out differences in the race line have a look at the middle of the reference lap line and your line. You may zoom in to spot the differences and read the values on peaks and valleys.
"""

YAW_RATE_DIAGRAM = """This is the yaw rate per second of your car. Use this to determine the Maximum Rotation Point (MRP). At this point you should normally accelerate."""


def get_help_div(help_text_resource):
    return Div(text=get_help_text_resource(help_text_resource), width=7, height=5)


def get_help_text_resource(help_text_resource):
    return f"""
    <div title="{help_text_resource}">?⃝</div>
    """
