import copy
import os
from typing import List, Tuple

import bokeh.application
import pandas as pd
from bokeh.driving import linear
from bokeh.layouts import layout
from bokeh.models import Select, Paragraph, ColumnDataSource, TableColumn, DataTable, HTMLTemplateFormatter, Button, Div
from bokeh.models.widgets import Tabs, Panel
from bokeh.plotting import curdoc, Figure
from bokeh.plotting import figure
from bokeh.plotting.figure import Figure

import gt7communication
from gt7helper import secondsToLaptime, get_speed_peaks_and_valleys, load_laps_from_pickle, save_laps_to_pickle, \
    list_lap_files_from_path, LapFile, calculate_time_diff_by_distance
from gt7lap import Lap
from gt7plot import get_x_axis_depending_on_mode, get_best_lap, get_median_lap


def pd_data_frame_from_lap(laps: List[Lap], best_lap: int) -> pd.core.frame.DataFrame:
    df = pd.DataFrame()
    for i, lap in enumerate(laps):
        time_diff = ""
        if best_lap == lap.LapTime:
            # lap_color = 35 # magenta
            # TODO add some formatting
            pass
        elif lap.LapTime < best_lap:  # LapTime cannot be smaller than bestlap, bestlap is always the smallest. This can only mean that lap.LapTime is from an earlier race on a different track
            time_diff = "-"
        elif best_lap > 0:
            time_diff = secondsToLaptime(-1 * (best_lap / 1000 - lap.LapTime / 1000))

        df_add = pd.DataFrame([{'number': lap.Number,
                                'time': secondsToLaptime(lap.LapTime / 1000),
                                'diff': time_diff,
                                'fuelconsumed': "%d" % (lap.FuelConsumed),
                                'fullthrottle': "%d" % (lap.FullThrottleTicks / lap.LapTicks * 1000),
                                'throttleandbreak': "%d" % (lap.ThrottleAndBrakesTicks / lap.LapTicks * 1000),
                                'fullbreak': "%d" % (lap.FullBrakeTicks / lap.LapTicks * 1000),
                                'nothrottle': "%d" % (lap.NoThrottleNoBrakeTicks / lap.LapTicks * 1000),
                                'tyrespinning': "%d" % (lap.TiresSpinningTicks / lap.LapTicks * 1000),
                                }], index=[i])
        df = pd.concat([df, df_add])

    return df


def get_data_from_lap(lap: Lap, title: str, distance_mode: bool):
    # breakpoints_x, breakpoints_y = get_brake_points(lap)
    data = {
        'throttle': lap.DataThrottle,
        'brake': lap.DataBraking,
        'speed': lap.DataSpeed,
        'time': lap.DataTime,
        'tires': lap.DataTires,
        'ticks': list(range(len(lap.DataSpeed))),
        'coast': lap.DataCoasting,
        'raceline_y': lap.PositionsY,
        'raceline_x': lap.PositionsX,
        'raceline_z': lap.PositionsZ,
        # 'breakpoints_x' : breakpoints_x,
        # 'breakpoints_y' : breakpoints_y,
        'distance': get_x_axis_depending_on_mode(lap, distance_mode),
        # 'title': title,
    }

    return data


def get_throttle_velocity_diagram_for_best_lap_and_last_lap(laps: List[Lap], distance_mode: bool, width: int) -> tuple[
    Figure, Figure, Figure, Figure, Figure, list[ColumnDataSource]]:
    TOOLTIPS = [
        ("index", "$index"),
        ("value", "$y"),
        ("Speed", "@speed kmh"),
        ("Throttle", "@throttle%"),
        ("Brake", "@brake%"),
        ("Coast", "@coast%"),
        ("Distance", "@distance m"),
    ]
    colors = ["blue", "magenta", "green"]
    legends = ["Last Lap", "Best Lap", "Median Lap"]

    f_speed = figure(y_axis_label="Speed", width=width,
                     height=250, tooltips=TOOLTIPS, active_drag="box_zoom")

    f_time_diff = figure(title="Telemetry - Last, Best, Median", y_axis_label="Time / Diff", width=width,
                         height=int(f_speed.height / 2), tooltips=TOOLTIPS, active_drag="box_zoom")

    f_throttle = figure(x_range=f_speed.x_range, y_axis_label="Throttle", width=width,
                        height=int(f_speed.height / 2), tooltips=TOOLTIPS, active_drag="box_zoom")
    f_braking = figure(x_range=f_speed.x_range, y_axis_label="Braking", width=width,
                       height=int(f_speed.height / 2), tooltips=TOOLTIPS, active_drag="box_zoom")

    f_coasting = figure(x_range=f_speed.x_range, y_axis_label="Coasting", width=width,
                        height=int(f_speed.height / 2), tooltips=TOOLTIPS, active_drag="box_zoom")

    # f_speed.xaxis.visible = False
    f_speed.toolbar.autohide = True

    f_throttle.xaxis.visible = False
    f_throttle.toolbar.autohide = True

    f_braking.xaxis.visible = False
    f_braking.toolbar.autohide = True

    f_coasting.xaxis.visible = False
    f_coasting.toolbar.autohide = True

    sources = []

    time_diff_source = ColumnDataSource(data={})
    f_time_diff.line(x="index", y='timedelta', source=time_diff_source, legend_label="Time Diff", line_width=1, color="red", line_alpha=1)
    sources.append(time_diff_source)

    for color, legend in zip(colors, legends):
        source = ColumnDataSource(data={})
        sources.append(source)

        f_speed.line(x='distance', y='speed', source=source, legend_label=legend, line_width=1, color=color,
                     line_alpha=1)
        f_throttle.line(x='distance', y='throttle', source=source, legend_label=legend, line_width=1, color=color,
                        line_alpha=1)
        f_braking.line(x='distance', y='brake', source=source, legend_label=legend, line_width=1, color=color,
                       line_alpha=1)
        f_coasting.line(x='distance', y='coast', source=source, legend_label=legend, line_width=1, color=color,
                        line_alpha=1)

        # line_speed = f.line(x='speed', y='distance', source=source, legend_label=lap.Title, line_width=1, color=colors[i])

    f_speed.legend.click_policy = "hide"
    f_throttle.legend.click_policy = f_speed.legend.click_policy
    f_braking.legend.click_policy = f_speed.legend.click_policy
    f_coasting.legend.click_policy = f_speed.legend.click_policy

    return f_time_diff, f_speed, f_throttle, f_braking, f_coasting, sources


p = figure(plot_width=1000, plot_height=600)
r1 = p.line([], [], color="green", line_width=2)
r2 = p.line([], [], color="blue", line_width=2)
r3 = p.line([], [], color="red", line_width=2)

ds1 = r1.data_source
ds2 = r2.data_source
ds3 = r3.data_source

# def on_server_loaded(server_context):
app = bokeh.application.Application

# Share the gt7comm connection between sessions by storing them as an application attribute
if not hasattr(app, "gt7comm"):
    playstation_ip = os.environ.get("GT7_PLAYSTATION_IP")
    load_laps_path = os.environ.get("GT7_LOAD_LAPS_PATH")

    if not playstation_ip:
        raise Exception("No IP set in env var GT7_PLAYSTATION_IP")

    app.gt7comm = gt7communication.GT7Communication(playstation_ip)

    if load_laps_path:
        app.gt7comm.load_laps(load_laps_from_pickle(load_laps_path), replace_other_laps=True)

    app.gt7comm.start()

source = ColumnDataSource(pd_data_frame_from_lap([], best_lap=app.gt7comm.session.best_lap))

# FIXME Not working correctly
template = """<div style="color:<%= 
                (function colorfromint(){
                    if (diff == "")
                        {return('magenta')}
                    }()) %>;"> 
                <%= value %>
            </div>
            """
formatter = HTMLTemplateFormatter(template=template)

columns = [
    TableColumn(field='number', title='#', formatter=formatter),
    TableColumn(field='time', title='Time', formatter=formatter),
    TableColumn(field='diff', title='Diff', formatter=formatter),
    TableColumn(field='fuelconsumed', title='Fuel Consumed', formatter=formatter),
    TableColumn(field='fullthrottle', title='Full Throttle', formatter=formatter),
    TableColumn(field='fullbreak', title='Full Break', formatter=formatter),
    TableColumn(field='nothrottle', title='No Throttle', formatter=formatter),
    TableColumn(field='tyrespinning', title='Tire Spin', formatter=formatter)
]

f_time_diff, f_speed, f_throttle, f_braking, f_coasting, data_sources = get_throttle_velocity_diagram_for_best_lap_and_last_lap(
    [], True, 1000)

t_lap_times = DataTable(source=source, columns=columns)
t_lap_times.width = 1000
t_lap_times.min_height = 20

##### Race line

RACE_LINE_TOOLTIPS = [
    ("index", "$index"),
    ("Breakpoint", "")
]

race_line_width = 250
speed_diagram_width = 1200
total_width = race_line_width + speed_diagram_width
s_race_line = figure(title="Race Line",
                     x_axis_label="z", y_axis_label="x", width=race_line_width, height=race_line_width,
                     tooltips=RACE_LINE_TOOLTIPS)
s_race_line.axis.visible = False
# s_race_line.toolbar.autohide = True
s_race_line.legend.click_policy = "hide"
# s_race_line.add_layout(Legend(), 'center')

last_lap_race_line = s_race_line.line(x="raceline_z", y="raceline_x", legend_label="Last Lap", line_width=1,
                                      color="blue")
best_lap_race_line = s_race_line.line(x="raceline_z", y="raceline_x", legend_label="Best Lap", line_width=1,
                                      color="magenta")

laps_stored = []
session_stored = None
connection_status_stored = None


def update_connection_info():
    div_connection_info.text = ""
    if app.gt7comm.is_connected():
        div_connection_info.text += "<p title='Connected'>🟢</p>"
    else:
        div_connection_info.text += "<p title='Disconnected'>🔴</p>"


@linear()
def update_lap_change(step):
    # time, x, y, z = from_csv(reader).next()
    global laps_stored
    global session_stored
    global connection_status_stored

    laps = app.gt7comm.get_laps()

    if app.gt7comm.session != session_stored:
        update_tuning_info()
        session_stored = copy.copy(app.gt7comm.session)

    if app.gt7comm.is_connected() != connection_status_stored:
        update_connection_info()
        connection_status_stored = copy.copy(app.gt7comm.is_connected())

    # This saves on cpu time, 99.9% of the time this is true
    if laps == laps_stored:
        return

    if len(laps) > 0:

        last_lap = laps[0]
        update_speed_peak_and_valley_diagram(div_last_lap, last_lap, "Last Lap")

        if len(laps) > 1:
            best_lap = get_best_lap(laps)
            update_speed_peak_and_valley_diagram(div_best_lap, best_lap, "Best Lap")

    update_time_table(laps)
    update_speed_velocity_graph(laps)

    laps_stored = laps.copy()


def update_speed_velocity_graph(laps: List[Lap]):
    if len(laps) == 0:  # Show nothing
        last_lap = Lap()
        best_lap = Lap()
        median_lap = Lap()
    elif len(laps) == 1:  # Only show last lap
        last_lap = laps[0]
        best_lap = Lap()  # Use empty lap for best
        median_lap = Lap()  # Use empty lap for median
    elif len(laps) == 2:  # Only show last and best lap
        last_lap = laps[0]
        best_lap = get_best_lap(laps)
        median_lap = Lap()  # Use empty lap for median
    else:  # Fill all laps
        last_lap = laps[0]
        best_lap = get_best_lap(laps)
        median_lap = get_median_lap(laps)

    last_lap_data = get_data_from_lap(last_lap, title="Last: %s" % last_lap.Title, distance_mode=True)
    best_lap_data = get_data_from_lap(best_lap, title="Best: %s" % last_lap.Title, distance_mode=True)

    data_sources[0].data = calculate_time_diff_by_distance(best_lap, last_lap)
    data_sources[1].data = last_lap_data
    data_sources[2].data = best_lap_data
    data_sources[3].data = get_data_from_lap(median_lap, title="Median: %s" % last_lap.Title, distance_mode=True)

    last_lap_race_line.data_source.data = last_lap_data
    best_lap_race_line.data_source.data = best_lap_data


def update_time_table(laps: List[Lap]):
    print("Adding %d laps to table" % len(laps))
    t_lap_times.source.data = ColumnDataSource.from_df(
        pd_data_frame_from_lap(laps, best_lap=app.gt7comm.session.best_lap))
    t_lap_times.trigger('source', t_lap_times.source, t_lap_times.source)


@linear()
def update(step):
    # time, x, y, z = from_csv(reader).next()
    last_package = app.gt7comm.get_last_data()
    ds1.data['x'].append(last_package.package_id)
    ds2.data['x'].append(last_package.package_id)
    ds3.data['x'].append(last_package.package_id)
    ds1.data['y'].append(last_package.carSpeed)
    ds2.data['y'].append(last_package.throttle)
    ds3.data['y'].append(last_package.brake)
    ds1.trigger('data', ds1.data, ds1.data)
    ds2.trigger('data', ds2.data, ds2.data)
    ds3.trigger('data', ds3.data, ds3.data)


def reset_button_handler(event):
    print("reset button clicked")
    div_best_lap.text = ""
    div_last_lap.text = ""
    app.gt7comm.reset()


def save_button_handler(event):
    path = save_laps_to_pickle(app.gt7comm.laps)
    print("Saved %d laps as %s" % (len(app.gt7comm.laps), path))


# l = get_session_layout(gt7comm.get_laps(), True)

def load_laps_handler(attr, old, new):
    print("Loading %s" % new)
    app.gt7comm.load_laps(load_laps_from_pickle(new), replace_other_laps=True)


# df = pd.DataFrame({
#     'SubjectID': ['Subject_01','Subject_02','Subject_03'],
#     'Result_1': ['Positive','Negative','Negative'],
#     'Result_3': ['Negative','Invalid','Positive'],
#     'Result_4': ['Positive','Negative','Negative'],
#     'Result_5': ['Positive','Positive','Negative']
# })

# show(myTable)

reset_button = Button(label="Save")
reset_button.on_click(save_button_handler)

save_button = Button(label="Reset")
save_button.on_click(reset_button_handler)

tuning_info = Div(width=200, height=100)

div_last_lap = Div(width=200, height=125)
div_best_lap = Div(width=200, height=125)
div_connection_info = Div(width=200, height=125)


def bokeh_tuple_for_list_of_laps(lapfiles: List[LapFile]):
    tuples = []
    for lapfile in lapfiles:
        tuples.append(tuple((lapfile.path, lapfile.__str__())))
    return tuples


stored_lap_files = bokeh_tuple_for_list_of_laps(list_lap_files_from_path("data"))

select_title = Paragraph(text="Load Laps:", align="center")
select = Select(value="laps", options=stored_lap_files)
select.on_change("value", load_laps_handler)


def update_speed_peak_and_valley_diagram(div, lap, title):
    table = """<table>"""

    peak_speed_data_x, peak_speed_data_y, valley_speed_data_x, valley_speed_data_y = get_speed_peaks_and_valleys(lap)

    table += "<tr><th colspan=\"3\">%s - %s</th></tr>" % (title, lap.Title)

    table = table + "<tr><th>#</th><th>Peak</th><th>Position</th></tr>"
    for i, dx in enumerate(peak_speed_data_x):
        table = table + "<tr><td>%d.</td><td>%d kmh</td><td>%d</td></tr>" % (
            i + 1, peak_speed_data_x[i], peak_speed_data_y[i])

    table = table + "<tr><th>#</th><th>Valley</th><th>Position</th></tr>"
    for i, dx in enumerate(valley_speed_data_x):
        table = table + "<tr><td>%d.</td><td>%d kmh</td><td>%d</td></tr>" % (
            i + 1, valley_speed_data_x[i], valley_speed_data_y[i])

    table = table + """</table>"""
    div.text = table


def update_tuning_info():
    tuning_info.text = """<p>Max Speed: <b>%d</b> kmh</p>
    <p>Min Body Height: <b>%d</b> mm</p>""" % (app.gt7comm.session.max_speed, app.gt7comm.session.min_body_height)


l1 = layout(children=[
    [f_time_diff], # TODO Have to calculate differences
    [f_speed, s_race_line, div_connection_info],
    [f_throttle, div_last_lap, div_best_lap],
    [f_braking],
    [f_coasting],
    # [p],
    [t_lap_times, layout(children=[tuning_info])],
    [reset_button, save_button, select_title, select],
])

# l1 = layout([[fig1, fig2]], sizing_mode='fixed')
l2 = layout([[reset_button, save_button], [t_lap_times]], sizing_mode='fixed')

tab1 = Panel(child=l1, title="Get Faster")
tab2 = Panel(child=l2, title="Race")
tabs = Tabs(tabs=[tab1, tab2])

curdoc().add_root(tabs)

# Add a periodic callback to be run every 500 milliseconds
# curdoc().add_periodic_callback(update, 60) # best would be 16ms, 60ms is smooth enough

# This will only trigger once per lap, but we check every second if anything happened
curdoc().add_periodic_callback(update_lap_change, 1000)
