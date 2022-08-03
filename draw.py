import itertools
from typing import List

from bokeh.palettes import Paired
from bokeh.plotting import figure, show, column
import pickle

from gt7lap import Lap


def show_race_data(laps: List[Lap]):

	with open('new.pickle', 'wb') as f:
		pickle.dump(laps, f)

	s1 = figure(title="Braking", x_axis_label="Ticks", y_axis_label="Value", width=1000, height=250, y_range=(0, 100))
	s2 = figure(title="Throttle", x_axis_label="Ticks", y_axis_label="Value", width=s1.width, height=s1.height, x_range=s1.x_range, y_range=(0, 100))
	s3 = figure(title="Speed", x_axis_label="Ticks", y_axis_label="Value", width=s1.width, height=s1.height, x_range=s1.x_range)

	colors = ["red", "blue"]

	for idx, lap in enumerate(laps):
		s1.line(list(range(len(lap.DataBraking))),lap.DataBraking, legend_label=("Lap %d" % idx), line_width=1, color=colors[idx])
		s2.line(list(range(len(lap.DataThrottle))), lap.DataThrottle, legend_label=("Lap %d" % idx), line_width=1, color=colors[idx])
		s3.line(list(range(len(lap.DataSpeed))), lap.DataSpeed, legend_label=("Lap %d" % idx), line_width=1, color=colors[idx])
	# show the results
	show(column(width=500, children=[s3, s2, s1]))

if __name__ == "__main__":
	with open('twolaps.pickle', 'rb') as f:
		l = pickle.load(f)

	show_race_data(l)

def get_best_lap(laps: List[Lap]):
	return sorted(laps, key=lambda x: x.LapTime, reverse=False)[0]
