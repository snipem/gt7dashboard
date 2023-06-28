import copy
import itertools
import logging
import os
import sys
import time
from typing import List

from bokeh.application import Application
from bokeh.application.handlers import FunctionHandler
from bokeh.driving import linear
from bokeh.layouts import layout
from bokeh.models import (
    Select,
    Paragraph,
    ColumnDataSource,
    Button,
    Div, CheckboxGroup, TabPanel, Tabs,
)
from bokeh.palettes import Plasma11 as palette
from bokeh.plotting import figure
from bokeh.server.server import Server
from tornado.ioloop import IOLoop

from gt7dashboard import gt7communication, gt7diagrams, gt7help, gt7helper
from gt7dashboard.gt7diagrams import get_speed_peak_and_valley_diagram
from gt7dashboard.gt7help import get_help_div
from gt7dashboard.gt7helper import (
    load_laps_from_pickle,
    save_laps_to_pickle,
    list_lap_files_from_path,
    calculate_time_diff_by_distance,
)
from gt7dashboard.gt7lap import Lap

# set logging level to debug
logger = logging.getLogger('gt7dashboard.py')
logger.setLevel(logging.DEBUG)

app = Application()


class GT7Dashboard:
    """GT7Dashboard holds the state of the GT7Dashboard"""

    def __init__(self):
        self.number_of_default_laps = 3
        self.sources_additional_laps = []
        self.race_lines_data = None
        self.race_lines = []
        self.race_diagram = None
        self.reference_lap_selected = None
        self.telemetry_update_needed = False
        self.connection_status_stored = None
        self.session_stored = None
        self.laps_stored = None
        self.reference_lap_select = None
        self.race_time_table = None
        self.s_race_line = None
        self.reference_lap_race_line = None
        self.last_lap_race_line = None
        self.div_header_line = Div()
        self.div_speed_peak_valley_diagram = Div()
        self.div_deviance_laps_on_display = Div()
        self.div_tuning_info = Div()
        self.div_connection_info = Div()
        self.div_fuel_map = Div()
        self.stored_fuel_map = None


dashboard = GT7Dashboard()


def update_connection_info():
    dashboard.div_connection_info.text = ""
    if app.gt7comm.is_connected():
        dashboard.div_connection_info.text += "<p title='Connected'>🟢</p>"
    else:
        dashboard.div_connection_info.text += "<p title='Disconnected'>🔴</p>"


def update_reference_lap_select(laps):
    dashboard.reference_lap_select.options = [
                                                 tuple(("-1", "Best Lap"))
                                             ] + gt7helper.bokeh_tuple_for_list_of_laps(laps)


@linear()
def update_fuel_map(step):
    if len(app.gt7comm.laps) == 0:
        dashboard.div_fuel_map.text = ""
        return

    last_lap = app.gt7comm.laps[0]

    if last_lap == dashboard.stored_fuel_map:
        return
    else:
        dashboard.stored_fuel_map = last_lap

    # TODO Add real live data during a lap
    dashboard.div_fuel_map.text = gt7diagrams.get_fuel_map_html_table(last_lap)


def update_race_lines(laps: List[Lap], reference_lap: Lap):
    """
    This function updates the race lines on the second tab with the amount of laps
    that the race line tab can hold
    """
    global dashboard

    reference_lap_data = reference_lap.get_data_dict()

    for i, lap in enumerate(laps[:len(dashboard.race_lines)]):
        logger.info(f"Updating Race Line for Lap {len(laps) - i} - {lap.title} and reference lap {reference_lap.title}")

        dashboard.race_lines[i].title.text = "Lap %d - %s (%s), Reference Lap: %s (%s)" % (
        len(laps) - i, lap.title, lap.car_name(), reference_lap.title, reference_lap.car_name())

        lap_data = lap.get_data_dict()
        dashboard.race_lines_data[i][0].data_source.data = lap_data
        dashboard.race_lines_data[i][1].data_source.data = lap_data
        dashboard.race_lines_data[i][2].data_source.data = lap_data

        dashboard.race_lines_data[i][3].data_source.data = reference_lap_data
        dashboard.race_lines_data[i][4].data_source.data = reference_lap_data
        dashboard.race_lines_data[i][5].data_source.data = reference_lap_data

        dashboard.race_lines[i].axis.visible = False

        gt7diagrams.add_annotations_to_race_line(dashboard.race_lines[i], lap, reference_lap)

        # Fixme not working
        dashboard.race_lines[i].x_range = dashboard.race_lines[0].x_range


def update_header_line(div: Div, last_lap: Lap, reference_lap: Lap):
    div.text = f"<p><b>Last Lap: {last_lap.title} ({last_lap.car_name()})<b></p>" \
               f"<p><b>Reference Lap: {reference_lap.title} ({reference_lap.car_name()})<b></p>"


def update_lap_change():
    """
    Is called whenever a lap changes.
    It detects if the telemetry date retrieved is the same as the data displayed.
    If true, it updates all the visual elements.
    """
    global dashboard

    update_start_time = time.time()

    laps = app.gt7comm.get_laps()

    if app.gt7comm.session != dashboard.session_stored:
        update_tuning_info()
        dashboard.session_stored = copy.copy(app.gt7comm.session)

    if app.gt7comm.is_connected() != dashboard.connection_status_stored:
        update_connection_info()
        dashboard.connection_status_stored = copy.copy(app.gt7comm.is_connected())

    # This saves on cpu time, 99.9% of the time this is true
    if laps == dashboard.laps_stored and not dashboard.telemetry_update_needed:
        return

    logger.debug("Rerendering laps")

    reference_lap = Lap()

    if len(laps) > 0:

        last_lap = laps[0]

        if len(laps) > 1:
            reference_lap = gt7helper.get_last_reference_median_lap(
                laps, reference_lap_selected=dashboard.reference_lap_selected
            )[1]

            dashboard.div_speed_peak_valley_diagram.text = get_speed_peak_and_valley_diagram(last_lap, reference_lap)

        update_header_line(dashboard.div_header_line, last_lap, reference_lap)

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

    dashboard.laps_stored = laps.copy()
    dashboard.telemetry_update_needed = False


def update_speed_velocity_graph(laps: List[Lap]):
    last_lap, reference_lap, median_lap = gt7helper.get_last_reference_median_lap(
        laps, reference_lap_selected=dashboard.reference_lap_selected
    )

    if last_lap:
        last_lap_data = last_lap.get_data_dict()
        dashboard.race_diagram.source_last_lap.data = last_lap_data
        dashboard.last_lap_race_line.data_source.data = last_lap_data

    if reference_lap and len(reference_lap.data_speed) > 0:
        reference_lap_data = reference_lap.get_data_dict()
        dashboard.race_diagram.source_time_diff.data = calculate_time_diff_by_distance(reference_lap, last_lap)
        dashboard.race_diagram.source_reference_lap.data = reference_lap_data
        dashboard.reference_lap_race_line.data_source.data = reference_lap_data

    if median_lap:
        dashboard.race_diagram.source_median_lap.data = median_lap.get_data_dict()

    dashboard.s_race_line.legend.visible = False
    dashboard.s_race_line.axis.visible = False

    fastest_laps = dashboard.race_diagram.update_fastest_laps_variance(laps)
    print("Updating Speed Deviance with %d fastest laps" % len(fastest_laps))
    dashboard.div_deviance_laps_on_display.text = ""
    for fastest_lap in fastest_laps:
        dashboard.div_deviance_laps_on_display.text += f"<b>Lap {fastest_lap.number}:</b> {fastest_lap.title}<br>"

    # Update breakpoints
    # Adding Brake Points is slow when rendering, this is on Bokehs side about 3s
    brake_points_enabled = os.environ.get("GT7_ADD_BRAKEPOINTS") == "true"

    if brake_points_enabled and len(last_lap.data_braking) > 0:
        update_break_points(last_lap, dashboard.s_race_line, "blue")

    if brake_points_enabled and len(reference_lap.data_braking) > 0:
        update_break_points(reference_lap, dashboard.s_race_line, "magenta")


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
    global dashboard
    # FIXME time table is not updating
    print("Adding %d laps to table" % len(laps))
    dashboard.race_time_table.show_laps(laps)

    # t_lap_times.trigger("source", t_lap_times.source, t_lap_times.source)


def reset_button_handler(event):
    print("reset button clicked")
    # div_reference_lap.text = ""
    # div_last_lap.text = ""
    dashboard.race_diagram.delete_all_additional_laps()

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
    dashboard.race_diagram.delete_all_additional_laps()
    app.gt7comm.load_laps(load_laps_from_pickle(new), replace_other_laps=True)


def load_reference_lap_handler(attr, old, new):
    global dashboard

    if int(new) == -1:
        # Set no reference lap
        dashboard.reference_lap_selected = None
    else:
        dashboard.reference_lap_selected = dashboard.laps_stored[int(new)]
        print("Loading %s as reference" % dashboard.laps_stored[int(new)].format())

    dashboard.telemetry_update_needed = True
    update_lap_change()


def update_tuning_info():
    dashboard.div_tuning_info.text = """<h4>Tuning Info</h4>
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
        race_lines_data.append(
            [throttle_line, breaking_line, coasting_line, reference_throttle_line, reference_breaking_line,
             reference_coasting_line])
        i += 1

    l = layout(children=race_line_diagrams)
    l.sizing_mode = sizing_mode

    return l, race_line_diagrams, race_lines_data


def table_row_selection_callback(attrname, old, new):
    global dashboard

    selectionIndex = dashboard.race_time_table.lap_times_source.selected.indices
    print("you have selected the row nr " + str(selectionIndex))

    colors = ["blue", "magenta", "green", "orange", "black", "purple"]
    # max_additional_laps = len(palette)
    colors_index = len(
        dashboard.sources_additional_laps) + dashboard.number_of_default_laps  # which are the default colors

    for index in selectionIndex:
        if index >= len(colors):
            colors_index = 0

        # get element at index of iterator
        color = colors[colors_index]
        colors_index += 1
        lap_to_add = dashboard.laps_stored[index]
        new_lap_data_source = dashboard.race_diagram.add_lap_to_race_diagram(color,
                                                                             legend=dashboard.laps_stored[index].title,
                                                                             visible=True)
        new_lap_data_source.data = lap_to_add.get_data_dict()


def modify_doc(doc):
    # def init_lap_times_source():
    #     global lap_times_source
    #     lap_times_source.data = gt7helper.pd_data_frame_from_lap([], best_lap_time=app.gt7comm.session.last_lap)
    #
    # init_lap_times_source()

    global app

    # Share the gt7comm connection between sessions by storing them as an application attribute
    if not hasattr(app, "gt7comm"):
        if len(sys.argv) > 1:
            playstation_ip = sys.argv[1]
        else:
            playstation_ip = os.environ.get("GT7_PLAYSTATION_IP")

        load_laps_path = os.environ.get("GT7_LOAD_LAPS_PATH")

        if not playstation_ip:
            raise Exception("No IP set in env var GT7_PLAYSTATION_IP or first parameter of gt7dashboard.py")

        app.gt7comm = gt7communication.GT7Communication(playstation_ip)

        if load_laps_path:
            print(f"Loading preloaded laps from {load_laps_path}")
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

    dashboard.stored_lap_files = gt7helper.bokeh_tuple_for_list_of_lapfiles(
        list_lap_files_from_path(os.path.join(os.getcwd(), "data"))
    )

    dashboard.race_diagram = gt7diagrams.RaceDiagram(width=1000)
    dashboard.race_time_table = gt7diagrams.RaceTimeTable()
    colors = itertools.cycle(palette)

    dashboard.race_time_table.lap_times_source.selected.on_change('indices', table_row_selection_callback)

    # Race line

    race_line_tooltips = [("index", "$index"), ("Breakpoint", "")]
    race_line_width = 250
    speed_diagram_width = 1200
    total_width = race_line_width + speed_diagram_width
    dashboard.s_race_line = figure(
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
    dashboard.s_race_line.y_range.flipped = True

    dashboard.s_race_line.toolbar.autohide = True

    dashboard.last_lap_race_line = dashboard.s_race_line.line(
        x="raceline_x",
        y="raceline_z",
        legend_label="Last Lap",
        line_width=1,
        color="blue",
        source=ColumnDataSource(data={"raceline_x": [], "raceline_z": []})
    )
    dashboard.reference_lap_race_line = dashboard.s_race_line.line(
        x="raceline_x",
        y="raceline_z",
        legend_label="Reference Lap",
        line_width=1,
        color="magenta",
        source=ColumnDataSource(data={"raceline_x": [], "raceline_z": []})
    )

    select_title = Paragraph(text="Load Laps:", align="center")
    dashboard.select = Select(value="laps", options=dashboard.stored_lap_files)
    dashboard.select.on_change("value", load_laps_handler)

    dashboard.reference_lap_select = Select(value="laps")
    dashboard.reference_lap_select.on_change("value", load_reference_lap_handler)

    dashboard.manual_log_button = Button(label="Log Lap Now")
    dashboard.manual_log_button.on_click(log_lap_button_handler)

    dashboard.save_button = Button(label="Save Laps")
    dashboard.save_button.on_click(save_button_handler)

    dashboard.reset_button = Button(label="Reset Laps")
    dashboard.reset_button.on_click(reset_button_handler)

    dashboard.div_tuning_info = Div(width=200, height=100)

    # div_last_lap = Div(width=200, height=125)
    # div_reference_lap = Div(width=200, height=125)
    dashboard.div_speed_peak_valley_diagram = Div(width=200, height=125)
    dashboard.div_gt7_dashboard = Div(width=120, height=30)
    dashboard.div_header_line = Div(width=400, height=30)
    dashboard.div_connection_info = Div(width=30, height=30)
    dashboard.div_deviance_laps_on_display = Div(width=200, height=dashboard.race_diagram.f_speed_variance.height)

    dashboard.div_fuel_map = Div(width=200, height=125, css_classes=["fuel_map"])

    dashboard.div_gt7_dashboard.text = f"<a href='https://github.com/snipem/gt7dashboard' target='_blank'>GT7 Dashboard</a>"

    LABELS = ["Record Replays"]

    dashboard.checkbox_group = CheckboxGroup(labels=LABELS, active=[1])
    dashboard.checkbox_group.on_change("active", always_record_checkbox_handler)

    dashboard.race_time_table.t_lap_times.width = 900

    l1 = layout(
        children=[
            [get_help_div(gt7help.HEADER), dashboard.div_connection_info, dashboard.div_gt7_dashboard, dashboard.div_header_line, dashboard.reset_button, dashboard.save_button, select_title, dashboard.select, get_help_div(gt7help.LAP_CONTROLS)],
            [get_help_div(gt7help.TIME_DIFF), dashboard.race_diagram.f_time_diff, layout(children=[dashboard.manual_log_button, dashboard.checkbox_group, dashboard.reference_lap_select]), get_help_div(gt7help.MANUAL_CONTROLS)],
            [get_help_div(gt7help.SPEED_DIAGRAM), dashboard.race_diagram.f_speed, dashboard.s_race_line, get_help_div(gt7help.RACE_LINE_MINI)],
            [get_help_div(gt7help.SPEED_VARIANCE), dashboard.race_diagram.f_speed_variance, dashboard.div_deviance_laps_on_display, get_help_div(gt7help.SPEED_VARIANCE)],
            [get_help_div(gt7help.THROTTLE_DIAGRAM), dashboard.race_diagram.f_throttle, dashboard.div_speed_peak_valley_diagram, get_help_div(gt7help.SPEED_PEAKS_AND_VALLEYS)],
            [get_help_div(gt7help.YAW_RATE_DIAGRAM), dashboard.race_diagram.f_yaw_rate],
            [get_help_div(gt7help.BRAKING_DIAGRAM), dashboard.race_diagram.f_braking],
            [get_help_div(gt7help.COASTING_DIAGRAM), dashboard.race_diagram.f_coasting],
            [get_help_div(gt7help.GEAR_DIAGRAM), dashboard.race_diagram.f_gear],
            [get_help_div(gt7help.RPM_DIAGRAM), dashboard.race_diagram.f_rpm],
            [get_help_div(gt7help.BOOST_DIAGRAM), dashboard.race_diagram.f_boost],
            [get_help_div(gt7help.TIRE_DIAGRAM), dashboard.race_diagram.f_tires],
            [get_help_div(gt7help.TIME_TABLE), dashboard.race_time_table.t_lap_times, get_help_div(gt7help.FUEL_MAP), dashboard.div_fuel_map, get_help_div(gt7help.TUNING_INFO), dashboard.div_tuning_info],
        ]
    )

    l2, race_lines, race_lines_data = get_race_lines_layout(number_of_race_lines=1)

    l3 = layout(
        [
            [dashboard.reset_button, dashboard.save_button],
            [dashboard.div_speed_peak_valley_diagram, dashboard.div_fuel_map],
            # TODO Race table does not render twice, one rendering will be empty
        ],
        sizing_mode="stretch_width",
    )

    #  Setup the tabs
    tab1 = TabPanel(child=l1, title="Get Faster")
    tab2 = TabPanel(child=l2, title="Race Lines")
    tab3 = TabPanel(child=l3, title="Race")
    tabs = Tabs(tabs=[tab1, tab2, tab3])

    doc.add_root(tabs)
    doc.title = "GT7 Dashboard"

    # This will only trigger once per lap, but we check every second if anything happened
    doc.add_periodic_callback(update_lap_change, 1000)
    doc.add_periodic_callback(update_fuel_map, 5000)


def main():
    global app

    app = Application(FunctionHandler(modify_doc))

    path = "/gt7dashboard"
    port = 5006
    server = Server({path: app}, port=port, io_loop=IOLoop.current())
    server.start()
    print(f'Opening GT7Dashboard application on http://localhost:{port}{path}')

    # activate for debugging
    # server.io_loop.add_callback(server.show, path)

    server.io_loop.start()


if __name__ == '__main__':
    main()
