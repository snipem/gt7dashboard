import itertools
from typing import List

from bokeh.layouts import layout
from bokeh.plotting import figure, show, column

import pickle

from gt7lap import Lap

def get_best_lap(laps: List[Lap]):
	return sorted(laps, key=lambda x: x.LapTime, reverse=False)[0]

def get_brake_points(lap):
	x = []
	y = []
	for i, b in enumerate(lap.DataBraking):
		if i>0:
			if lap.DataBraking[i-1] == 0 and lap.DataBraking[i] > 0:
				x.append(lap.PositionsZ[i])
				y.append(lap.PositionsX[i])

	return x, y

def plot_session_analysis(laps: List[Lap]):

	with open('data/new.pickle', 'wb') as f:
		pickle.dump(laps, f)


	TOOLTIPS = [
		("index", "$index"),
		("value", "$y"),
		("desc", "@desc"),
	]

	RACE_LINE_TOOLTIPS = [
		("index", "$index"),
		("desc", "@desc"),
	]

	s1 = figure(title="Braking", x_axis_label="Ticks", y_axis_label="Value", width=1200, height=250, y_range=(0, 100), tooltips=TOOLTIPS)
	s2 = figure(title="Throttle", x_axis_label="Ticks", y_axis_label="Value", width=s1.width, height=250, x_range=s1.x_range, y_range=(0, 100), tooltips=TOOLTIPS)
	s3 = figure(title="Speed", x_axis_label="Ticks", y_axis_label="Value", width=s1.width, height=500, x_range=s1.x_range, tooltips=TOOLTIPS)
	s_tire_slip = figure(title="Tire Slip", x_axis_label="Ticks", y_axis_label="Value", width=s1.width, height=200, x_range=s1.x_range, tooltips=TOOLTIPS)
	s_race_line = figure(title="Race Line", x_axis_label="z", y_axis_label="x", width=500, height=500, tooltips=RACE_LINE_TOOLTIPS)

	# Limit plotted laps by available colors
	colors = ["magenta", "blue", "green", "red", "black", "grey", "purple"]

	for idx, lap in enumerate(laps[:len(colors)]):

		brake_points_x, brake_points_y = get_brake_points(lap)

		s1.line(list(range(len(lap.DataBraking))),lap.DataBraking, legend_label=lap.Title, line_width=1, color=colors[idx])
		s2.line(list(range(len(lap.DataThrottle))), lap.DataThrottle, legend_label=lap.Title, line_width=1, color=colors[idx])
		s3.line(list(range(len(lap.DataSpeed))), lap.DataSpeed, legend_label=lap.Title, line_width=1, color=colors[idx])
		s_tire_slip.line(list(range(len(lap.DataTires))), lap.DataTires, legend_label=lap.Title, line_width=1, color=colors[idx])
		s_race_line.line(lap.PositionsZ, lap.PositionsX, legend_label=lap.Title, line_width=1, color=colors[idx])

		for i, _ in enumerate(brake_points_x):
			s_race_line.scatter(brake_points_x[i], brake_points_y[i], marker="circle", size=10, fill_color=colors[idx])

	# show the results

	s1.legend.click_policy="hide"
	s2.legend.click_policy="hide"
	s3.legend.click_policy="hide"
	s_tire_slip.legend.click_policy="hide"
	s_race_line.legend.click_policy="hide"

	s1.axis.visible = False
	s2.axis.visible = False
	s3.axis.visible = False
	s_race_line.axis.visible = False

	show(layout(children=[
		[s3, s_race_line],
		[s_tire_slip],
		[s2],
		[s1],
	]))

if __name__ == "__main__":
	with open('data/lagunaseca6laps.pickle', 'rb') as f:
		l = pickle.load(f)

	plot_session_analysis(l)
