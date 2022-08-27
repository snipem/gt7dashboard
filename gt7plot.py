import sys
from typing import List

from bokeh.layouts import layout
from bokeh.plotting import figure, show, output_file, save
from bokeh.plotting.figure import Figure

import pickle

from gt7helper import get_x_axis_depending_on_mode, get_brake_points, \
	get_best_lap, get_median_lap
from gt7lap import Lap

def get_throttle_velocity_diagram(lap: Lap, distance_mode: bool, title: str, color: str, width: int) -> Figure:
	x_axis = get_x_axis_depending_on_mode(lap, distance_mode)
	TOOLTIPS = [
		("index", "$index"),
		("value", "$y"),
	]
	f = figure(title="Speed/Throttle - "+title, x_axis_label="Distance", y_axis_label="Value", width=width, height=500, tooltips=TOOLTIPS)
	f.line(x_axis, lap.data_throttle, legend_label=lap.title, line_width=1, color=color, line_alpha=0.5)
	f.line(x_axis, lap.data_speed, legend_label=lap.title, line_width=1, color=color)
	return f


def get_session_layout(laps: List[Lap], distance_mode=True):

	TOOLTIPS = [
		("index", "$index"),
		("distance", "$x"),
		("value", "$y"),
		("desc", "@desc"),
	]

	RACE_LINE_TOOLTIPS = [
		("index", "$index"),
		("Breakpoint", "")
	]

	race_line_width = 500
	speed_diagram_width = 1200
	total_width = race_line_width + speed_diagram_width

	braking_diagram = figure(title="Braking", x_axis_label="Distance", y_axis_label="Value", width=total_width, height=250, y_range=(0, 100), tooltips=TOOLTIPS)
	throttle_diagram = figure(title="Throttle", x_axis_label="Distance", y_axis_label="Value", width=total_width, height=250, x_range=braking_diagram.x_range, y_range=(0, 100), tooltips=TOOLTIPS)
	speed_diagram = figure(title="Speed", x_axis_label="Distance", y_axis_label="Value", width=speed_diagram_width, height=500, x_range=braking_diagram.x_range, tooltips=TOOLTIPS)
	s_tire_slip = figure(title="Tire Slip", x_axis_label="Distance", y_axis_label="Value", width=total_width, height=200, x_range=braking_diagram.x_range, tooltips=TOOLTIPS)
	s_race_line = figure(title="Race Line", x_axis_label="z", y_axis_label="x", width=500, height=500, tooltips=RACE_LINE_TOOLTIPS)
	# s_magic_numbers_1 = figure(title="0x94", x_axis_label="Distance", y_axis_label="Value", width=total_width, height=200, x_range=braking_diagram.x_range, tooltips=TOOLTIPS)
	# s_magic_numbers_2 = figure(title="0x98", x_axis_label="Distance", y_axis_label="Value", width=total_width, height=200, x_range=braking_diagram.x_range, tooltips=TOOLTIPS)
	# s_magic_numbers_3 = figure(title="0x9c", x_axis_label="Distance", y_axis_label="Value", width=total_width, height=200, x_range=braking_diagram.x_range, tooltips=TOOLTIPS)
	# s_magic_numbers_4 = figure(title="0xA0", x_axis_label="Distance", y_axis_label="Value", width=total_width, height=200, x_range=braking_diagram.x_range, tooltips=TOOLTIPS)

	# Limit plotted laps by available colors
	colors = ["blue", "magenta", "green", "red", "black", "grey", "purple"]

	for idx, lap in enumerate(laps[:len(colors)]):

		brake_points_x, brake_points_y = get_brake_points(lap)

		x_axis = get_x_axis_depending_on_mode(lap, distance_mode)

		braking_diagram.line(x_axis, lap.data_braking, legend_label=lap.title, line_width=1, color=colors[idx])
		throttle_diagram.line(x_axis, lap.data_throttle, legend_label=lap.title, line_width=1, color=colors[idx])
		speed_diagram.line(x_axis, lap.data_speed, legend_label=lap.title, line_width=1, color=colors[idx])
		s_tire_slip.line(x_axis, lap.data_tires, legend_label=lap.title, line_width=1, color=colors[idx])
		s_race_line.line(lap.data_position_z, lap.data_position_x, legend_label=lap.title, line_width=1, color=colors[idx])

		for i, _ in enumerate(brake_points_x):
			s_race_line.scatter(brake_points_x[i], brake_points_y[i], marker="circle", size=10, fill_color=colors[idx])

	# s_magic_numbers_1.line(x_axis, lap.Magic0x94, legend_label="0x94", line_width=1, color="red")
	# s_magic_numbers_2.line(x_axis, lap.Magic0x98, legend_label="0x98", line_width=1, color="blue")
	# s_magic_numbers_3.line(x_axis, lap.Magic0x9C, legend_label="0x9C", line_width=1, color="green")
	# s_magic_numbers_4.line(x_axis, lap.Magic0xA0, legend_label="0xA0", line_width=1, color="black")

	# show the results

	braking_diagram.legend.click_policy="hide"
	throttle_diagram.legend.click_policy="hide"
	speed_diagram.legend.click_policy="hide"
	s_tire_slip.legend.click_policy="hide"
	s_race_line.legend.click_policy="hide"

	# braking_diagram.axis.visible = False
	# throttle_diagram.axis.visible = False
	# speed_diagram.axis.visible = False
	s_race_line.axis.visible = False

	current_lap_throttle_velocity_diagram = get_throttle_velocity_diagram(laps[0], distance_mode, "Last Lap", "blue", total_width)
	best_lap = get_best_lap(laps)
	best_lap_throttle_velocity_diagram = get_throttle_velocity_diagram(best_lap, distance_mode, "Best Lap", "magenta", total_width)

	l = layout(children=[
		[speed_diagram, s_race_line],
		[current_lap_throttle_velocity_diagram],
		[best_lap_throttle_velocity_diagram],
		[s_tire_slip],
		#[throttle_diagram],
		[braking_diagram],
		# [s_magic_numbers_1],
		# [s_magic_numbers_2],
		# [s_magic_numbers_3],
		# [s_magic_numbers_4],
	])

	return l

def plot_session_analysis(laps: List[Lap], distance_mode=True, open_in_browser=True):

	with open('data/new.pickle', 'wb') as f:
		pickle.dump(laps, f)

	output_file(filename="analysis_latest.html")

	l = get_session_layout(laps, distance_mode)

	if open_in_browser:
		show(l)
	else:
		save(l)

if __name__ == "__main__":
	with open(sys.argv[1], 'rb') as f:
		l = pickle.load(f)

	plot_session_analysis([l[0], get_best_lap(l), get_median_lap(l)])
