import copy
import logging
import os
import time
from typing import List

import bokeh.application
from bokeh.driving import linear
from bokeh.layouts import column, layout, row
from bokeh.models import (
    Select,
    Paragraph,
    ColumnDataSource,
    TableColumn,
    DataTable,
    Button,
    Div, CheckboxGroup, TabPanel, Tabs,
)
from bokeh.plotting import curdoc
from bokeh.plotting import figure

from gt7dashboard import gt7communication, gt7diagrams, gt7help, gt7helper, gt7lap, gt7theme
from gt7dashboard.gt7diagrams import get_speed_peak_and_valley_diagram

from gt7dashboard.gt7help import get_help_div
from gt7dashboard.gt7helper import (
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

    logger.debug("Rerendering laps")

    reference_lap = Lap()

    if len(laps) > 0:

        last_lap = laps[0]

        if len(laps) > 1:
            reference_lap = gt7helper.get_last_reference_median_lap(
                laps, reference_lap_selected=g_reference_lap_selected
            )[1]

            div_speed_peak_valley_diagram.text = get_speed_peak_and_valley_diagram(last_lap, reference_lap)

        update_header_line(div_header_line, last_lap, reference_lap)

    logger.debug("Updating of %d laps" % len(laps))

    start_time = time.time()
    update_time_table(laps)
    logger.debug("Updating time table took %dms" % ((time.time() - start_time) * 1000))

    start_time = time.time()
    update_reference_lap_select(laps)
    logger.debug("Updating reference lap select took %dms" % ((time.time() - start_time) * 1000))

    start_time = time.time()
    update_speed_velocity_graph(laps)
    logger.debug("Updating speed velocity graph took %dms" % ((time.time() - start_time) * 1000))

    start_time = time.time()
    update_race_lines(laps, reference_lap)
    logger.debug("Updating race lines took %dms" % ((time.time() - start_time) * 1000))

    logger.debug("End of updating laps, whole Update took %dms" % ((time.time() - update_start_time) * 1000))

    g_laps_stored = laps.copy()
    g_telemetry_update_needed = False


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

    if brake_points_enabled and len(last_lap.data_braking) > 0:
        update_break_points(last_lap, s_race_line, gt7theme.LAST_LAP)

    if brake_points_enabled and len(reference_lap.data_braking) > 0:
        update_break_points(reference_lap, s_race_line, gt7theme.REFERENCE_LAP)


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
    div_tuning_info.text = """<p>Max Speed: <b>%d</b> kph</p>
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
        playstation_ip = "255.255.255.255"
        logger.info(f"No IP set in env var GT7_PLAYSTATION_IP using broadcast at {playstation_ip}")

    app.gt7comm = gt7communication.GT7Communication(playstation_ip)

    if load_laps_path:
        app.gt7comm.load_laps(
            load_laps_from_pickle(load_laps_path), replace_other_laps=True
        )

    app.gt7comm.start()
else:
    # Reuse existing thread
    if not app.gt7comm.is_connected():
        logger.info("Restarting gt7communcation because of no connection")
        app.gt7comm.restart()
    else:
        # Existing thread has connection, proceed
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

# Theme must be installed before any figure is constructed. Bokeh applies it
# when those models are attached to this document.
gt7theme.apply(curdoc())

race_diagram = gt7diagrams.RaceDiagram(width=1000)
race_time_table = gt7diagrams.RaceTimeTable()


def table_row_selection_callback(attrname, old, new):
    global g_laps_stored
    global race_diagram
    global race_time_table

    selectionIndex=race_time_table.lap_times_source.selected.indices
    logger.info("you have selected the row nr "+str(selectionIndex))

    lap_colors = gt7theme.ADDITIONAL_LAP_COLORS
    colors_index = len(race_diagram.sources_additional_laps) % len(lap_colors)

    for index in selectionIndex:
        if index >= len(lap_colors):
            colors_index = 0

        color = lap_colors[colors_index % len(lap_colors)]
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
    line_width=gt7theme.TRACE_WIDTH,
    color=gt7theme.LAST_LAP,
    source=ColumnDataSource(data={"raceline_x": [], "raceline_z": []})
)
reference_lap_race_line = s_race_line.line(
    x="raceline_x",
    y="raceline_z",
    legend_label="Reference Lap",
    line_width=gt7theme.TRACE_WIDTH,
    color=gt7theme.REFERENCE_LAP,
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
div_gt7_dashboard.stylesheets = [f"a {{ color: {gt7theme.INK}; text-decoration: none; }}"]

LABELS = ["Record Replays"]

checkbox_group = CheckboxGroup(labels=LABELS, active=[1])
checkbox_group.on_change("active", always_record_checkbox_handler)

race_time_table.t_lap_times.sizing_mode = "stretch_width"
race_time_table.t_lap_times.width = None
race_time_table.t_lap_times.min_width = 720
race_time_table.t_lap_times.height = 480

select.width = 280
reference_lap_select.width = 220
div_deviance_laps_on_display.width = 240

div_header_line.sizing_mode = "stretch_width"
div_header_line.width = None
div_header_line.min_width = 240
div_header_line.height = 52

div_fuel_map.sizing_mode = "stretch_width"
div_fuel_map.width = None
div_fuel_map.min_width = 360
div_fuel_map.height = 420

div_tuning_info.sizing_mode = "stretch_width"
div_tuning_info.width = None
div_tuning_info.min_width = 220
div_tuning_info.height = 140

div_speed_peak_valley_diagram.sizing_mode = "stretch_width"
div_speed_peak_valley_diagram.width = None
div_speed_peak_valley_diagram.min_width = 480
div_speed_peak_valley_diagram.height = 260

# Distance charts share f_speed.x_range. Stretch the width and keep an
# explicit height so a hidden tab does not scale itself to the viewport.
for chart, height in (
    (race_diagram.f_time_diff, 180),
    (race_diagram.f_speed, 280),
    (race_diagram.f_speed_variance, 110),
    (race_diagram.f_gear, 150),
    (race_diagram.f_rpm, 150),
    (race_diagram.f_boost, 150),
    (race_diagram.f_throttle, 150),
    (race_diagram.f_braking, 150),
    (race_diagram.f_coasting, 150),
    (race_diagram.f_yaw_rate, 150),
    (race_diagram.f_tires, 150),
):
    chart.sizing_mode = "stretch_width"
    chart.height = height
    chart.width = None

div_deviance_laps_on_display.height = race_diagram.f_speed_variance.height

s_race_line.sizing_mode = "fixed"
s_race_line.width = 320
s_race_line.height = 320

# Returned layout is not added to the document. Putting it in the document
# would give the race-line figure a second parent beside the Racing Lines tab.
# RaceDiagram.layout is likewise left out of the document.
_race_line_layout, race_lines, race_lines_data = get_race_lines_layout(number_of_race_lines=1)
race_lines[0].sizing_mode = "stretch_width"
race_lines[0].height = 560
race_lines[0].width = None


def _caption(text, help_text):
    """Title line with the info icon beside the label, not in a side gutter."""
    label = Paragraph(
        text=text,
        margin=0,
        styles={
            "color": gt7theme.INK,
            "font_size": "15px",
            "font_family": "Helvetica, Arial, sans-serif",
            "line_height": "18px",
            "white_space": "nowrap",
        },
    )
    bar = row([label, get_help_div(help_text)], spacing=6)
    bar.styles = {"align_items": "center", "height": "auto"}
    return bar


def _titled_block(title, help_text, body, stretch=True):
    block = column(_caption(title, help_text), body, spacing=2)
    if stretch:
        block.sizing_mode = "stretch_width"
    return block


def _chart_block(fig, help_text, *beside, stretch=True):
    title = fig.title.text
    # The caption row shows this title. An empty in-figure title takes no band.
    fig.title.text = ""
    if beside:
        body = row([fig, *beside], sizing_mode="stretch_width", spacing=8)
    else:
        body = fig
    return _titled_block(title, help_text, body, stretch=stretch)


def _wrapping_toolbar_row(children):
    # Bokeh rows do not wrap. Inline height lets a wrapped line grow past the
    # one-line size the layout solver would otherwise lock in.
    group = row(children, sizing_mode="stretch_width", spacing=8)
    group.styles = {
        "flex_wrap": "wrap",
        "row_gap": "8px",
        "align_items": "center",
        "height": "auto",
        "max_height": "none",
    }
    return group


control_bar = layout(
    children=[
        [
            div_connection_info,
            get_help_div(gt7help.HEADER),
            div_header_line,
            div_gt7_dashboard,
        ],
        _wrapping_toolbar_row(
            [
                reset_button,
                save_button,
                get_help_div(gt7help.LAP_CONTROLS),
                manual_log_button,
                checkbox_group,
            ]
        ),
        _wrapping_toolbar_row(
            [
                select_title,
                select,
                get_help_div(gt7help.MANUAL_CONTROLS),
                reference_lap_select,
            ]
        ),
    ],
    sizing_mode="stretch_width",
)

overview = layout(
    children=[
        _titled_block("Lap times", gt7help.TIME_TABLE, race_time_table.t_lap_times),
    ],
    sizing_mode="stretch_width",
)

speed_and_gears = layout(
    children=[
        _chart_block(race_diagram.f_time_diff, gt7help.TIME_DIFF),
        _chart_block(race_diagram.f_speed, gt7help.SPEED_DIAGRAM),
        _chart_block(
            race_diagram.f_speed_variance,
            gt7help.SPEED_VARIANCE,
            div_deviance_laps_on_display,
        ),
        _chart_block(race_diagram.f_gear, gt7help.GEAR_DIAGRAM),
        _chart_block(race_diagram.f_rpm, gt7help.RPM_DIAGRAM),
        _chart_block(race_diagram.f_boost, gt7help.BOOST_DIAGRAM),
    ],
    sizing_mode="stretch_width",
)

driver_inputs = layout(
    children=[
        _chart_block(race_diagram.f_throttle, gt7help.THROTTLE_DIAGRAM),
        _chart_block(race_diagram.f_braking, gt7help.BRAKING_DIAGRAM),
        _chart_block(race_diagram.f_coasting, gt7help.COASTING_DIAGRAM),
        _chart_block(race_diagram.f_yaw_rate, gt7help.YAW_RATE_DIAGRAM),
        _chart_block(race_diagram.f_tires, gt7help.TIRE_DIAGRAM),
    ],
    sizing_mode="stretch_width",
)

mini_race_line = _chart_block(s_race_line, gt7help.RACE_LINE_MINI, stretch=False)
mini_race_line.width = s_race_line.width
racing_lines = layout(
    children=[
        row(
            [
                mini_race_line,
                _chart_block(race_lines[0], gt7help.RACE_LINE_BIG),
            ],
            sizing_mode="stretch_width",
            spacing=12,
        ),
        _titled_block(
            "Speed peaks",
            gt7help.SPEED_PEAKS_AND_VALLEYS,
            div_speed_peak_valley_diagram,
        ),
    ],
    sizing_mode="stretch_width",
)

fuel_and_strategy = layout(
    children=[
        row(
            [
                _titled_block("Fuel map", gt7help.FUEL_MAP, div_fuel_map),
                _titled_block("Tuning Info", gt7help.TUNING_INFO, div_tuning_info),
            ],
            sizing_mode="stretch_width",
            spacing=12,
        ),
    ],
    sizing_mode="stretch_width",
)

tabs = Tabs(
    tabs=[
        TabPanel(child=overview, title="Overview"),
        TabPanel(child=speed_and_gears, title="Speed & Gears"),
        TabPanel(child=driver_inputs, title="Driver Inputs"),
        TabPanel(child=racing_lines, title="Racing Lines"),
        TabPanel(child=fuel_and_strategy, title="Fuel & Strategy"),
    ],
    sizing_mode="stretch_width",
)
page = layout(children=[control_bar, tabs], sizing_mode="stretch_width")

# layout() copies stretch_width onto children that have no sizing mode.
# Put controls back to their own width so they do not split the row with the charts.
for control in (
    select,
    reference_lap_select,
    select_title,
    reset_button,
    save_button,
    manual_log_button,
    checkbox_group,
    div_connection_info,
    div_gt7_dashboard,
    div_deviance_laps_on_display,
):
    control.sizing_mode = None

gt7theme.install_chrome(
    page,
    tabs,
    buttons=[reset_button, save_button, manual_log_button],
    selects=[select, reference_lap_select],
    checkboxes=[checkbox_group],
    tables=[race_time_table.t_lap_times],
)

curdoc().add_root(page)
curdoc().title = "GT7 Dashboard"

# This will only trigger once per lap, but we check every second if anything happened
curdoc().add_periodic_callback(update_lap_change, 1000)
curdoc().add_periodic_callback(update_fuel_map, 5000)
