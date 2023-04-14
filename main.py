import copy
import itertools
import logging
import os
import time
from typing import List

import bokeh.application
from bokeh.driving import linear
from bokeh.layouts import layout
from bokeh.models import (
    Select,
    Paragraph,
    ColumnDataSource,
    TableColumn,
    DataTable,
    Button,
    Div, CheckboxGroup, TabPanel, Tabs,
)
from bokeh.palettes import Set3_12 as palette
from bokeh.plotting import curdoc
from bokeh.plotting import figure

import gt7communication
import gt7diagrams
import gt7helper
from gt7helper import (
    load_laps_from_pickle,
    save_laps_to_pickle,
    list_lap_files_from_path,
    calculate_time_diff_by_distance,
)
from gt7lap import Lap

# set logging level to debug
logging.getLogger().setLevel(logging.DEBUG)


def update_connection_info():
    div_connection_info.text = ""
    if app.gt7comm.is_connected():
        div_connection_info.text += "<p title='Connected'>🟢</p>"
    else:
        div_connection_info.text += "<p title='Disconnected'>🔴</p>"


def update_reference_lap_select(laps):
    reference_lap_select.options = [
        tuple(("-1", "Best Lap"))
    ] + gt7helper.bokeh_tuple_for_list_of_laps(laps)


@linear()
def update_fuel_map(step):
    global g_stored_fuel_map

    if len(app.gt7comm.laps) == 0:
        div_fuel_map.text = ""
        return

    last_lap = app.gt7comm.laps[0]

    if last_lap == g_stored_fuel_map:
        return
    else:
        g_stored_fuel_map = last_lap

    # TODO Add real live data during a lap
    div_fuel_map.text = gt7diagrams.get_fuel_map_html_table(last_lap)


def update_race_lines(laps: List[Lap], reference_lap: Lap):
    """
    This function updates the race lines on the second tab with the amount of laps
    that the race line tab can hold
    """
    global race_lines, race_lines_data


    reference_lap_data = gt7helper.get_data_dict_from_lap(reference_lap, distance_mode=True)

    for i, lap in enumerate(laps[:len(race_lines)]):
        print("Updating Race Line for Lap %d - %s" % (len(laps) - i, lap.title))

        race_lines[i].title.text = "Lap %d - %s (%s), Reference Lap: %s (%s)" % (len(laps) - i, lap.title, lap.car_name(), reference_lap.title, reference_lap.car_name())

        lap_data = gt7helper.get_data_dict_from_lap(lap, distance_mode=True)
        race_lines_data[i][0].data_source.data = lap_data
        race_lines_data[i][1].data_source.data = lap_data
        race_lines_data[i][2].data_source.data = lap_data

        race_lines_data[i][3].data_source.data = reference_lap_data
        race_lines_data[i][4].data_source.data = reference_lap_data
        race_lines_data[i][5].data_source.data = reference_lap_data

        race_lines[i].axis.visible = False

        gt7diagrams.add_annotations_to_race_line(race_lines[i], lap, reference_lap)

        # Fixme not working
        race_lines[i].x_range = race_lines[0].x_range


def update_header_line(div: Div, last_lap: Lap, reference_lap: Lap):
    div.text = f"<p><b>Last Lap: {last_lap.title} ({reference_lap.car_name()})<b></p>" \
               f"<p><b>Reference Lap: {reference_lap.title} ({reference_lap.car_name()})<b></p>"

@linear()
def update_lap_change(step):
    """
    Is called whenever a lap changes.
    It detects if the telemetry date retrieved is the same as the data displayed.
    If true, it updates all the visual elements.
    """
    global g_laps_stored
    global g_session_stored
    global g_connection_status_stored
    global g_telemetry_update_needed
    global g_reference_lap_selected

    update_start_time = time.time()

    laps = app.gt7comm.get_laps()

    if app.gt7comm.session != g_session_stored:
        update_tuning_info()
        g_session_stored = copy.copy(app.gt7comm.session)

    if app.gt7comm.is_connected() != g_connection_status_stored:
        update_connection_info()
        g_connection_status_stored = copy.copy(app.gt7comm.is_connected())

    # This saves on cpu time, 99.9% of the time this is true
    if laps == g_laps_stored and not g_telemetry_update_needed:
        return

    logging.debug("Rerendering laps")

    reference_lap = Lap()

    if len(laps) > 0:

        last_lap = laps[0]
        update_speed_peak_and_valley_diagram(div_last_lap, last_lap, "Last Lap")

        if len(laps) > 1:
            reference_lap = gt7helper.get_last_reference_median_lap(
                laps, reference_lap_selected=g_reference_lap_selected
            )[1]
            if reference_lap:
                update_speed_peak_and_valley_diagram(
                    div_reference_lap, reference_lap, "Reference Lap"
                )

        update_header_line(div_header_line, last_lap, reference_lap)

    logging.debug("Start of updates have %d laps" % len(laps))

    start_time = time.time()
    logging.debug("Updating time table")
    update_time_table(laps)
    logging.debug("Took %dms" % ((time.time() - start_time) * 1000))

    start_time = time.time()
    logging.debug("Updating reference lap select")
    update_reference_lap_select(laps)
    logging.debug("Took %dms" % ((time.time() - start_time) * 1000))

    start_time = time.time()
    logging.debug("Updating speed velocity graph")
    update_speed_velocity_graph(laps)
    logging.debug("Took %dms" % ((time.time() - start_time) * 1000))

    start_time = time.time()
    logging.debug("Updating race lines")
    update_race_lines(laps, reference_lap)
    logging.debug("Took %dms" % ((time.time() - start_time) * 1000))

    logging.debug("Whole Update took %dms" % ((time.time() - update_start_time) * 1000))


    g_laps_stored = laps.copy()
    g_telemetry_update_needed = False


def update_speed_velocity_graph(laps: List[Lap]):
    last_lap, reference_lap, median_lap = gt7helper.get_last_reference_median_lap(
        laps, reference_lap_selected=g_reference_lap_selected
    )

    last_lap_data = gt7helper.get_data_dict_from_lap(last_lap, distance_mode=True)
    reference_lap_data = gt7helper.get_data_dict_from_lap(reference_lap, distance_mode=True)

    if reference_lap and len(reference_lap.data_speed) > 0:
        race_diagram.source_time_diff.data = calculate_time_diff_by_distance(reference_lap, last_lap)

    race_diagram.source_last_lap.data = last_lap_data
    race_diagram.source_reference_lap.data = reference_lap_data
    race_diagram.source_median_lap.data = gt7helper.get_data_dict_from_lap(median_lap, distance_mode=True)

    last_lap_race_line.data_source.data = last_lap_data
    reference_lap_race_line.data_source.data = reference_lap_data

    s_race_line.legend.visible = False
    s_race_line.axis.visible = False

    # Update breakpoints
    # Adding Brake Points is slow when rendering, this is on Bokehs side about 3s
    brake_points_enabled = os.environ.get("GT7_ADD_BRAKEPOINTS") == "true"

    if brake_points_enabled and len(last_lap.data_braking) > 0:
        update_break_points(last_lap, s_race_line, "blue")

    if brake_points_enabled and len(reference_lap.data_braking) > 0:
        update_break_points(reference_lap, s_race_line, "magenta")


def update_break_points(lap: Lap, race_line: figure, color: str):
    brake_points_x, brake_points_y = gt7helper.get_brake_points(lap)

    for i, _ in enumerate(brake_points_x):
        race_line.scatter(
            brake_points_x[i],
            brake_points_y[i],
            marker="circle",
            size=10,
            fill_color=color,
        )


def update_time_table(laps: List[Lap]):
    global t_lap_times
    global lap_times_source
    print("Adding %d laps to table" % len(laps))
    new_df = gt7helper.pd_data_frame_from_lap(laps, best_lap_time=app.gt7comm.session.best_lap)
    lap_times_source.data = ColumnDataSource.from_df(new_df)
    # FIXME time table is not updating
    # t_lap_times.trigger("source", t_lap_times.source, t_lap_times.source)


def reset_button_handler(event):
    print("reset button clicked")
    div_reference_lap.text = ""
    div_last_lap.text = ""

    init_lap_times_source()

    app.gt7comm.reset()
def always_record_checkbox_handler(event, old, new):
    if len(new) == 2:
        print("Set always record data to True")
        app.gt7comm.always_record_data = True
    else:
        print("Set always record data to False")
        app.gt7comm.always_record_data = False


def log_lap_button_handler(event):
    app.gt7comm.finish_lap(manual=True)
    print("Added a lap manually to the list of laps: %s" % app.gt7comm.laps[0])


def save_button_handler(event):
    path = save_laps_to_pickle(app.gt7comm.laps)
    print("Saved %d laps as %s" % (len(app.gt7comm.laps), path))


def load_laps_handler(attr, old, new):
    print("Loading %s" % new)
    app.gt7comm.load_laps(load_laps_from_pickle(new), replace_other_laps=True)


def load_reference_lap_handler(attr, old, new):
    global g_reference_lap_selected
    global reference_lap_select
    global g_telemetry_update_needed

    if int(new) == -1:
        # Set no reference lap
        g_reference_lap_selected = None
    else:
        g_reference_lap_selected = g_laps_stored[int(new)]
        print("Loading %s as reference" % g_laps_stored[int(new)].format())

    g_telemetry_update_needed = True
    update_lap_change()


def update_speed_peak_and_valley_diagram(div, lap: Lap, title):
    table = """<table>"""

    (
        peak_speed_data_x,
        peak_speed_data_y,
        valley_speed_data_x,
        valley_speed_data_y,
    ) = lap.get_speed_peaks_and_valleys()

    table += '<tr><th colspan="3">%s - %s</th></tr>' % (title, lap.title)

    table = table + "<tr><th>#</th><th>Peak</th><th>Position</th></tr>"
    for i, dx in enumerate(peak_speed_data_x):
        table = table + "<tr><td>%d.</td><td>%d kph</td><td>%d</td></tr>" % (
            i + 1,
            peak_speed_data_x[i],
            peak_speed_data_y[i],
        )

    table = table + "<tr><th>#</th><th>Valley</th><th>Position</th></tr>"
    for i, dx in enumerate(valley_speed_data_x):
        table = table + "<tr><td>%d.</td><td>%d kph</td><td>%d</td></tr>" % (
            i + 1,
            valley_speed_data_x[i],
            valley_speed_data_y[i],
        )

    table = table + """</table>"""
    div.text = table


def update_tuning_info():
    div_tuning_info.text = """<h4>Tuning Info</h4>
    <p>Max Speed: <b>%d</b> kph</p>
    <p>Min Body Height: <b>%d</b> mm</p>""" % (
        app.gt7comm.session.max_speed,
        app.gt7comm.session.min_body_height,
    )

def get_race_lines_layout(number_of_race_lines):
    """
    This function returns the race lines layout.
    It returns a grid of 3x3 race lines. Red is braking.
    Green is throttling.
    """
    i = 0
    race_line_diagrams = []
    race_lines_data = []

    sizing_mode = "scale_height"

    while i < number_of_race_lines:
        s_race_line, throttle_line, breaking_line, coasting_line, reference_throttle_line, reference_breaking_line, reference_coasting_line = gt7diagrams.get_throttle_braking_race_line_diagram()
        s_race_line.sizing_mode = sizing_mode
        race_line_diagrams.append(s_race_line)
        race_lines_data.append([throttle_line, breaking_line, coasting_line, reference_throttle_line, reference_breaking_line, reference_coasting_line])
        i+=1

    l = layout(children=race_line_diagrams)
    l.sizing_mode = sizing_mode

    return l, race_line_diagrams, race_lines_data

app = bokeh.application.Application

# Share the gt7comm connection between sessions by storing them as an application attribute
if not hasattr(app, "gt7comm"):
    playstation_ip = os.environ.get("GT7_PLAYSTATION_IP")
    load_laps_path = os.environ.get("GT7_LOAD_LAPS_PATH")

    if not playstation_ip:
        raise Exception("No IP set in env var GT7_PLAYSTATION_IP")

    app.gt7comm = gt7communication.GT7Communication(playstation_ip)

    if load_laps_path:
        app.gt7comm.load_laps(
            load_laps_from_pickle(load_laps_path), replace_other_laps=True
        )

    app.gt7comm.start()
else:
    # Reuse existing thread
    if not app.gt7comm.is_connected():
        print("Restarting gt7communcation")
        app.gt7comm.restart()
    else:
        # Existing thread has connection, proceed
        pass

lap_times_source = ColumnDataSource(
    gt7helper.pd_data_frame_from_lap([], best_lap_time=app.gt7comm.session.best_lap)
)

def init_lap_times_source():
    global lap_times_source
    lap_times_source.data = gt7helper.pd_data_frame_from_lap([], best_lap_time=app.gt7comm.session.best_lap)

init_lap_times_source()

g_laps_stored = []
g_session_stored = None
g_connection_status_stored = None
g_reference_lap_selected = None
g_stored_fuel_map = None
g_telemetry_update_needed = False

stored_lap_files = gt7helper.bokeh_tuple_for_list_of_lapfiles(
    list_lap_files_from_path(os.path.join(os.getcwd(), "data"))
)

columns = [
    TableColumn(field="number", title="#"),
    TableColumn(field="time", title="Time"),
    TableColumn(field="diff", title="Diff"),
    TableColumn(field="fuelconsumed", title="Fuel Cons."),
    TableColumn(field="fullthrottle", title="Full Throt."),
    TableColumn(field="fullbreak", title="Full Break"),
    TableColumn(field="nothrottle", title="Coast"),
    TableColumn(field="tyrespinning", title="Tire Spin"),
    TableColumn(field="car_name", title="Car"),
]

race_diagram = gt7diagrams.get_throttle_velocity_diagram_for_reference_lap_and_last_lap(width=1000)

t_lap_times = DataTable(
    source=lap_times_source, columns=columns, index_position=None, css_classes=["lap_times_table"]
)
t_lap_times.autosize_mode = "fit_columns"
# t_lap_times.width = 1000
t_lap_times.min_height = 20
t_lap_times.min_width = 950

def table_row_selection_callback(attrname, old, new):
    global g_laps_stored
    global lap_times_source
    global race_diagram

    selectionIndex=lap_times_source.selected.indices
    print("you have selected the row nr "+str(selectionIndex))

    colors = ["green", "red", "black"]
    colors = itertools.cycle(palette)
    # max_additional_laps = len(palette)

    for index in selectionIndex:
            lap_to_add = g_laps_stored[index]
            new_lap_data_source = race_diagram.add_lap_to_race_diagram(next(colors), legend=g_laps_stored[index].title, visible=True)
            new_lap_data_source.data = gt7helper.get_data_dict_from_lap(lap_to_add, distance_mode=True)


lap_times_source.selected.on_change('indices', table_row_selection_callback)

# Race line

race_line_tooltips = [("index", "$index"), ("Breakpoint", "")]
race_line_width = 250
speed_diagram_width = 1200
total_width = race_line_width + speed_diagram_width
s_race_line = figure(
    title="Race Line",
    x_axis_label="x",
    y_axis_label="z",
    match_aspect=True,
    width=race_line_width,
    height=race_line_width,
    active_drag="box_zoom",
    tooltips=race_line_tooltips,
)

# We set this to true, since maps appear flipped in the game
# compared to their actual coordinates
s_race_line.y_range.flipped = True

s_race_line.toolbar.autohide = True

last_lap_race_line = s_race_line.line(
    x="raceline_x",
    y="raceline_z",
    legend_label="Last Lap",
    line_width=1,
    color="blue",
    source=ColumnDataSource(data={"raceline_x": [], "raceline_z": []})
)
reference_lap_race_line = s_race_line.line(
    x="raceline_x",
    y="raceline_z",
    legend_label="Reference Lap",
    line_width=1,
    color="magenta",
    source=ColumnDataSource(data={"raceline_x": [], "raceline_z": []})
)

select_title = Paragraph(text="Load Laps:", align="center")
select = Select(value="laps", options=stored_lap_files)
select.on_change("value", load_laps_handler)

reference_lap_select = Select(value="laps")
reference_lap_select.on_change("value", load_reference_lap_handler)

manual_log_button = Button(label="Log Lap Now")
manual_log_button.on_click(log_lap_button_handler)

save_button = Button(label="Save Laps")
save_button.on_click(save_button_handler)

reset_button = Button(label="Reset Laps")
reset_button.on_click(reset_button_handler)

div_tuning_info = Div(width=200, height=100)

div_last_lap = Div(width=200, height=125)
div_gt7_dashboard = Div(width=120, height=30)
div_header_line = Div(width=400, height=30)
div_reference_lap = Div(width=200, height=125)
div_connection_info = Div(width=30, height=30)

div_fuel_map = Div(width=200, height=125, css_classes=["fuel_map"])

div_gt7_dashboard.text = f"<a href='https://github.com/snipem/gt7dashboard' target='_blank'>GT7 Dashboard</a>"

LABELS = ["Always Record"]

checkbox_group = CheckboxGroup(labels=LABELS, active=[1])
checkbox_group.on_change("active", always_record_checkbox_handler)

l1 = layout(
    children=[
        [div_connection_info, div_gt7_dashboard, div_header_line, reset_button, save_button, select_title, select],
        [race_diagram.f_time_diff, layout(children=[manual_log_button, checkbox_group, reference_lap_select])],
        [race_diagram.f_speed, s_race_line],
        [race_diagram.f_throttle, [[div_last_lap, div_reference_lap]]],
        [race_diagram.f_braking],
        [race_diagram.f_coasting],
        [race_diagram.f_tires],
        [t_lap_times, div_fuel_map, div_tuning_info],
    ]
)




l2, race_lines, race_lines_data = get_race_lines_layout(number_of_race_lines=1)

l3 = layout(
    [[reset_button, save_button],
     # [t_lap_times],
     [div_fuel_map]],
    sizing_mode="stretch_width",
)

#  Setup the tabs
tab1 = TabPanel(child=l1, title="Get Faster")
tab2 = TabPanel(child=l2, title="Race Lines")
tab3 = TabPanel(child=l3, title="Race")
tabs = Tabs(tabs=[tab1, tab2, tab3])

curdoc().add_root(tabs)
curdoc().title = "GT7 Dashboard"

# This will only trigger once per lap, but we check every second if anything happened
curdoc().add_periodic_callback(update_lap_change, 1000)
curdoc().add_periodic_callback(update_fuel_map, 5000)
