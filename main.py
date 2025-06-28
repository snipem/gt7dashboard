import copy
import itertools
import logging
import os
from random import randint
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
from bokeh.palettes import Plasma11 as palette
from bokeh.plotting import curdoc
from bokeh.plotting import figure

from gt7dashboard import gt7communication, gt7diagrams, gt7help, gt7helper, gt7lap
from gt7dashboard.gt7diagrams import get_speed_peak_and_valley_diagram

from gt7dashboard.gt7help import get_help_div
from gt7dashboard.gt7helper import (
    equalizer_lap,
    load_laps_from_pickle,
    save_laps_to_pickle,
    list_lap_files_from_path,
    calculate_time_diff_by_distance, save_laps_to_json, load_laps_from_json,
)
from gt7dashboard.gt7lap import Lap


# set logging level to debug
logger = logging.getLogger('main.py')
logger.setLevel(logging.DEBUG)


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


    reference_lap_data = reference_lap.get_data_dict()

    for i, lap in enumerate(laps[:len(race_lines)]):
        logger.info(f"Updating Race Line for Lap {len(laps) -i} - {lap.title} and reference lap {reference_lap.title}")

        race_lines[i].title.text = "Lap %d - %s (%s), Reference Lap: %s (%s)" % (len(laps) - i, lap.title, lap.car_name(), reference_lap.title, reference_lap.car_name())

        lap_data = lap.get_data_dict()
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
    div.text = f"<p><b>Last Lap: {last_lap.title} ({last_lap.car_name()})<b></p>" \
               f"<p><b>Reference Lap: {reference_lap.title} ({reference_lap.car_name()})<b></p>"

def update_lap_change():
    """
    Is called whenever a lap changes.
    It detects if the telemetry data retrieved is the same as the data displayed.
    If true, it updates all the visual elements.
    """
    global g_laps_stored
    global g_session_stored
    global g_connection_status_stored
    global g_telemetry_update_needed
    global g_reference_lap_selected

    update_start_time = time.time()  # Record the start time of the update process

    laps = app.gt7comm.get_laps()  # Retrieve the latest laps from the telemetry
    
    # logger.debug(laps)
    # Check if the session has changed and update tuning info if needed
    if app.gt7comm.session != g_session_stored:
        update_tuning_info()
        g_session_stored = copy.copy(app.gt7comm.session)

    # Check if the connection status has changed and update connection info if needed
    if app.gt7comm.is_connected() != g_connection_status_stored:
        update_connection_info()
        g_connection_status_stored = copy.copy(app.gt7comm.is_connected())

    # Save on CPU time, as 99.9% of the time the laps are the same and no update is needed
    if laps == g_laps_stored and not g_telemetry_update_needed:
        return

    logger.debug("Rerendering laps")

    reference_lap = Lap()  # Initialize a reference lap object

    if len(laps) > 0:
        last_lap = laps[0]  # Get the most recent lap

        if len(laps) > 1:

            # Get the reference lap using a helper function
            reference_lap = gt7helper.get_last_reference_median_lap(
                laps, reference_lap_selected=g_reference_lap_selected
            )[1]

            last_lap = equalizer_lap(reference_lap, last_lap)

            # Update the speed peak and valley diagram with the last lap and reference lap
            div_speed_peak_valley_diagram.text = get_speed_peak_and_valley_diagram(last_lap, reference_lap)

        # Update the header line with the last lap and reference lap
        update_header_line(div_header_line, last_lap, reference_lap)

    logger.debug("Updating of %d laps" % len(laps))

    # Update the time table and log the time taken
    start_time = time.time()
    update_time_table(laps)
    logger.debug("Updating time table took %dms" % ((time.time() - start_time) * 1000))

    # Update the reference lap select and log the time taken
    start_time = time.time()
    update_reference_lap_select(laps)
    logger.debug("Updating reference lap select took %dms" % ((time.time() - start_time) * 1000))

    # Update the speed velocity graph and log the time taken
    start_time = time.time()
    update_speed_velocity_graph(laps)
    logger.debug("Updating speed velocity graph took %dms" % ((time.time() - start_time) * 1000))

    # Update the race lines and log the time taken
    start_time = time.time()
    update_race_lines(laps, reference_lap)
    logger.debug("Updating race lines took %dms" % ((time.time() - start_time) * 1000))

    # Log the total time taken for the entire update process
    logger.debug("End of updating laps, whole Update took %dms" % ((time.time() - update_start_time) * 1000))

    g_laps_stored = laps.copy()  # Store the latest laps
    g_telemetry_update_needed = False  # Reset the telemetry update flag



def update_speed_velocity_graph(laps: List[Lap]):
    last_lap, reference_lap, median_lap = gt7helper.get_last_reference_median_lap(
        laps, reference_lap_selected=g_reference_lap_selected
    )

    if last_lap:
        last_lap_data = last_lap.get_data_dict()
        race_diagram.source_last_lap.data = last_lap_data
        last_lap_race_line.data_source.data = last_lap_data

        if reference_lap and len(reference_lap.data_speed) > 0:
            reference_lap_data = reference_lap.get_data_dict()
            race_diagram.source_time_diff.data = calculate_time_diff_by_distance(reference_lap, last_lap)
            race_diagram.source_reference_lap.data = reference_lap_data
            reference_lap_race_line.data_source.data = reference_lap_data

    if median_lap:
        race_diagram.source_median_lap.data = median_lap.get_data_dict()


    s_race_line.legend.visible = False
    s_race_line.axis.visible = False

    fastest_laps = race_diagram.update_fastest_laps_variance(laps)
    logger.info("Updating Speed Deviance with %d fastest laps" % len(fastest_laps))
    div_deviance_laps_on_display.text = ""
    for fastest_lap in fastest_laps:
        div_deviance_laps_on_display.text += f"<b>Lap {fastest_lap.number}:</b> {fastest_lap.title}<br>"

    # Update breakpoints
    # Adding Brake Points is slow when rendering, this is on Bokehs side about 3s
    brake_points_enabled = os.environ.get("GT7_ADD_BRAKEPOINTS") == "true"
    brake_points_enabled = True
    try:
        if brake_points_enabled and len(last_lap.data_braking) > 0:
            update_break_points(last_lap, s_race_line, "blue")

        if brake_points_enabled and len(reference_lap.data_braking) > 0:
            update_break_points(reference_lap, s_race_line, "magenta")
    except Exception as e:
        logger.error(f"Error adding brake points: {e}")

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
    global race_time_table
    global lap_times_source
    # FIXME time table is not updating
    logger.info("Adding %d laps to table" % len(laps))
    race_time_table.show_laps(laps)

    # t_lap_times.trigger("source", t_lap_times.source, t_lap_times.source)


def reset_button_handler(event):
    global g_telemetry_update_needed
    logger.info("reset button clicked")
    race_diagram.delete_all_additional_laps()

    app.gt7comm.load_laps([], replace_other_laps=True)
    app.gt7comm.reset()
    g_telemetry_update_needed = True


def always_record_checkbox_handler(event, old, new):
    if len(new) == 2:
        logger.info("Set always record data to True")
        app.gt7comm.always_record_data = True
    else:
        logger.info("Set always record data to False")
        app.gt7comm.always_record_data = False


def log_lap_button_handler(event):
    app.gt7comm.finish_lap(manual=True)
    logger.info("Added a lap manually to the list of laps: %s" % app.gt7comm.laps[0])


def save_button_handler(event):
    if len(app.gt7comm.laps) > 0:
        path = save_laps_to_json(app.gt7comm.laps)
        logger.info("Saved %d laps as %s" % (len(app.gt7comm.laps), path))


def load_laps_handler(attr, old, new):
    logger.info("Loading %s" % new)
    race_diagram.delete_all_additional_laps()
    app.gt7comm.load_laps(load_laps_from_json(new), replace_other_laps=True)


def load_reference_lap_handler(attr, old, new):
    global g_reference_lap_selected
    global reference_lap_select
    global g_telemetry_update_needed

    if int(new) == -1:
        # Set no reference lap
        g_reference_lap_selected = None
    else:
        g_reference_lap_selected = g_laps_stored[int(new)]
        logger.info("Loading %s as reference" % g_laps_stored[int(new)].format())

    g_telemetry_update_needed = True
    update_lap_change()



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
    # Retrieve the PlayStation IP address and the path to load laps from environment variables
    playstation_ip = os.environ.get("GT7_PLAYSTATION_IP")
    load_laps_path = os.environ.get("GT7_LOAD_LAPS_PATH")

    # If no IP address is set in the environment variable, use the broadcast address
    if not playstation_ip:
        playstation_ip = "255.255.255.255"
        logger.info(f"No IP set in env var GT7_PLAYSTATION_IP using broadcast at {playstation_ip}")

    # Initialize the GT7Communication object with the PlayStation IP address
    app.gt7comm = gt7communication.GT7Communication(playstation_ip)

    # Load laps from a pickle file if the path is set
    if load_laps_path:
        app.gt7comm.load_laps(
            load_laps_from_pickle(load_laps_path), replace_other_laps=True
        )

    # Start the GT7 communication thread
    app.gt7comm.start()
else:
    # Reuse the existing GT7 communication thread
    if not app.gt7comm.is_connected():
        logger.info("Restarting gt7communcation because of no connection")
        # Restart the GT7 communication thread if there is no connection
        app.gt7comm.restart()
    else:
        # If the existing thread has a connection, proceed without any action
        pass



# def init_lap_times_source():
#     global lap_times_source
#     lap_times_source.data = gt7helper.pd_data_frame_from_lap([], best_lap_time=app.gt7comm.session.last_lap)
#
# init_lap_times_source()

g_laps_stored = []
g_session_stored = None
g_connection_status_stored = None
g_reference_lap_selected = None
g_stored_fuel_map = None
g_telemetry_update_needed = False

stored_lap_files = gt7helper.bokeh_tuple_for_list_of_lapfiles(
    list_lap_files_from_path(os.path.join(os.getcwd(), "data"))
)

race_diagram = gt7diagrams.RaceDiagram(width=1000)
race_time_table = gt7diagrams.RaceTimeTable()
colors = itertools.cycle(palette)


def table_row_selection_callback(attrname, old, new):
    global g_laps_stored
    global race_diagram
    global race_time_table
    global colors

    selectionIndex=race_time_table.lap_times_source.selected.indices
    logger.info("you have selected the row nr "+str(selectionIndex))

    colors = ["blue", "magenta", "green", "orange", "black", "purple"]
    # max_additional_laps = len(palette)
    colors_index = len(race_diagram.sources_additional_laps) + race_diagram.number_of_default_laps # which are the default colors

    for index in selectionIndex:
        if index >= len(colors):
            colors_index = 0

        # get element at index of iterator
        color = colors[colors_index]
        colors_index+=1
        lap_to_add = g_laps_stored[index]
        new_lap_data_source = race_diagram.add_lap_to_race_diagram(color, legend=g_laps_stored[index].title, visible=True)
        new_lap_data_source.data = lap_to_add.get_data_dict()


race_time_table.lap_times_source.selected.on_change('indices', table_row_selection_callback)

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
    active_drag="auto",
    active_scroll="wheel_zoom",
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

# div_last_lap = Div(width=200, height=125)
# div_reference_lap = Div(width=200, height=125)
div_speed_peak_valley_diagram = Div(width=200, height=125)
div_gt7_dashboard = Div(width=120, height=30)
div_header_line = Div(width=400, height=30)
div_connection_info = Div(width=30, height=30)
div_deviance_laps_on_display = Div(width=200, height=race_diagram.f_speed_variance.height)

div_fuel_map = Div(width=200, height=125, css_classes=["fuel_map"])

div_gt7_dashboard.text = f"<a href='https://github.com/snipem/gt7dashboard' target='_blank'>GT7 Dashboard</a>"

LABELS = ["Record Replays"]

checkbox_group = CheckboxGroup(labels=LABELS, active=[1])
checkbox_group.on_change("active", always_record_checkbox_handler)

race_time_table.t_lap_times.width=900

l1 = layout(
    children=[
        [get_help_div(gt7help.HEADER), div_connection_info, div_gt7_dashboard, div_header_line, reset_button, save_button, select_title, select, get_help_div(gt7help.LAP_CONTROLS)],
        [get_help_div(gt7help.TIME_DIFF), race_diagram.f_time_diff, layout(children=[manual_log_button, checkbox_group, reference_lap_select]), get_help_div(gt7help.MANUAL_CONTROLS)],
        [get_help_div(gt7help.SPEED_DIAGRAM), race_diagram.f_speed, s_race_line, get_help_div(gt7help.RACE_LINE_MINI)],
        [get_help_div(gt7help.SPEED_VARIANCE), race_diagram.f_speed_variance, div_deviance_laps_on_display, get_help_div(gt7help.SPEED_VARIANCE)],
        [get_help_div(gt7help.THROTTLE_DIAGRAM), race_diagram.f_throttle, div_speed_peak_valley_diagram, get_help_div(gt7help.SPEED_PEAKS_AND_VALLEYS)],
        [get_help_div(gt7help.YAW_RATE_DIAGRAM), race_diagram.f_yaw_rate],
        [get_help_div(gt7help.BRAKING_DIAGRAM), race_diagram.f_braking],
        [get_help_div(gt7help.COASTING_DIAGRAM), race_diagram.f_coasting],
        [get_help_div(gt7help.GEAR_DIAGRAM), race_diagram.f_gear],
        [get_help_div(gt7help.RPM_DIAGRAM), race_diagram.f_rpm],
        [get_help_div(gt7help.BOOST_DIAGRAM), race_diagram.f_boost],
        [get_help_div(gt7help.TIRE_DIAGRAM), race_diagram.f_tires],
        [get_help_div(gt7help.TIME_TABLE), race_time_table.t_lap_times, get_help_div(gt7help.FUEL_MAP), div_fuel_map, get_help_div(gt7help.TUNING_INFO), div_tuning_info],
    ]
)

l2, race_lines, race_lines_data = get_race_lines_layout(number_of_race_lines=1)

l3 = layout(
    [
        [reset_button, save_button],
        [div_speed_peak_valley_diagram, div_fuel_map], # TODO Race table does not render twice, one rendering will be empty
     ],
    sizing_mode="stretch_width",
)

data_dict = {
    "metric": [],
    "values": []
}

source = ColumnDataSource(data=data_dict)


columns = [
    TableColumn(field="metric", title="Metric"),
    TableColumn(field="values", title="Value")
]

data_table = DataTable(source=source, columns=columns, width=400, height=3000)

def update_telemetry_table():
    current_data = app.gt7comm.get_last_data_once()
    
    if current_data is None:
        return

    telemetry = current_data
    
    new_data_table = [
        ("Package ID", telemetry.package_id),
        ("Best Lap", telemetry.best_lap),
        ("Last Lap", telemetry.last_lap),
        ("Laps", f"{telemetry.current_lap}/{telemetry.total_laps}"),
        ("Current Gear", telemetry.current_gear),
        ("Suggested Gear", telemetry.suggested_gear),
        ("Fuel Capacity", telemetry.fuel_capacity),
        ("Current Fuel", telemetry.current_fuel),
        ("Boost", telemetry.boost),
        ("Type Speed FL", telemetry.type_speed_FL),
        ("Type Speed FR", telemetry.type_speed_FR),
        ("Type Speed RL", telemetry.type_speed_RL),
        ("Tyre Speed RR", telemetry.tyre_speed_RR),
        ("Car Speed", telemetry.car_speed),
        ("Tyre Slip Ratio FL", telemetry.tyre_slip_ratio_FL),
        ("Tyre Slip Ratio FR", telemetry.tyre_slip_ratio_FR),
        ("Tyre Slip Ratio RL", telemetry.tyre_slip_ratio_RL),
        ("Tyre Slip Ratio RR", telemetry.tyre_slip_ratio_RR),
        ("Current Position", telemetry.current_position),
        ("Total Positions", telemetry.total_positions),
        ("Is Paused", telemetry.is_paused),
        ("In Race", telemetry.in_race),
        ("Car ID", telemetry.car_id),
        ("Throttle", telemetry.throttle),
        ("RPM", telemetry.rpm),
        ("RPM Rev Warning", telemetry.rpm_rev_warning),
        ("Brake", telemetry.brake),
        ("RPM Rev Limiter", telemetry.rpm_rev_limiter),
        ("Estimated Top Speed", telemetry.estimated_top_speed),
        ("Clutch", telemetry.clutch),
        ("Clutch Engaged", telemetry.clutch_engaged),
        ("RPM After Clutch", telemetry.rpm_after_clutch),
        ("Ride Height", telemetry.ride_height),
        ("Tyre Temp FL", telemetry.tyre_temp_FL),
        ("Tyre Temp FR", telemetry.tyre_temp_FR),
        ("Suspension FL", telemetry.suspension_fl),
        ("Suspension FR", telemetry.suspension_fr),
        ("Tyre Temp RL", telemetry.tyre_temp_rl),
        ("Tyre Temp RR", telemetry.tyre_temp_rr),
        ("Suspension RL", telemetry.suspension_rl),
        ("Suspension RR", telemetry.suspension_rr),
        ("Position X", telemetry.position_x),
        ("Position Y", telemetry.position_y),
        ("Position Z", telemetry.position_z),
        ("Velocity X", telemetry.velocity_x),
        ("Velocity Y", telemetry.velocity_y),
        ("Velocity Z", telemetry.velocity_z),
        ("Rotation Pitch", telemetry.rotation_pitch),
        ("Rotation Yaw", telemetry.rotation_yaw),
        ("Rotation Roll", telemetry.rotation_roll),
        ("Angular Velocity X", telemetry.angular_velocity_x),
        ("Angular Velocity Y", telemetry.angular_velocity_y),
        ("Angular Velocity Z", telemetry.angular_velocity_z),
        ("Oil Temp", telemetry.oil_temp),
        ("Water Temp", telemetry.water_temp),
        ("Oil Pressure", telemetry.oil_pressure),
        # ("Time on Track", telemetry.time_on_track),
        # ("Gear 1", telemetry.gear_1),
        # ("Gear 2", telemetry.gear_2),
        # ("Gear 3", telemetry.gear_3),
        # ("Gear 4", telemetry.gear_4),
        # ("Gear 5", telemetry.gear_5),
        # ("Gear 6", telemetry.gear_6),
        # ("Gear 7", telemetry.gear_7),
        # ("Gear 8", telemetry.gear_8),
        # ("Tyre Diameter FL", telemetry.tyre_diameter_FL),
        # ("Tyre Diameter FR", telemetry.tyre_diameter_FR),
        # ("Tyre Diameter RL", telemetry.tyre_diameter_RL),
        # ("Tyre Diameter RR", telemetry.tyre_diameter_RR),
    ]
    
    source.data = {
    "metric": [item[0] for item in new_data_table],
    "values": [item[1] for item in new_data_table]
}


# Create a layout
l4 = layout([
    [data_table]
])

#  Setup the tabs
tab1 = TabPanel(child=l1, title="Get Faster")
tab2 = TabPanel(child=l2, title="Race Lines")
tab3 = TabPanel(child=l3, title="Race")
tab4 = TabPanel(child=l4, title="Dashboard")
tabs = Tabs(tabs=[tab1, tab2, tab3, tab4])

curdoc().add_root(tabs)
curdoc().title = "GT7 Dashboard"

# This will only trigger once per lap, but we check every second if anything happened
curdoc().add_periodic_callback(update_lap_change, 1000)
curdoc().add_periodic_callback(update_fuel_map, 5000)

curdoc().add_periodic_callback(update_telemetry_table, 200)

# def update_packate_id():
#     print(app.gt7comm.get_package_id())

# curdoc().add_periodic_callback(update_packate_id, 500)

# curdoc().add_periodic_callback