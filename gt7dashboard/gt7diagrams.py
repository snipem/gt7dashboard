from typing import List

import bokeh
from bokeh.layouts import layout
from bokeh.models import ColumnDataSource, Label, Scatter, Column, Line, TableColumn, DataTable, Range1d
from bokeh.plotting import figure

from gt7dashboard import gt7helper
from gt7dashboard.gt7lap import Lap


def get_throttle_braking_race_line_diagram():
    # TODO Make this work, tooltips just show breakpoint
    race_line_tooltips = [("index", "$index")]
    s_race_line = figure(
        title="Race Line",
        match_aspect=True,
        active_scroll="wheel_zoom",
        tooltips=race_line_tooltips,
    )

    # We set this to true, since maps appear flipped in the game
    # compared to their actual coordinates
    s_race_line.y_range.flipped = True

    s_race_line.toolbar.autohide = True

    s_race_line.axis.visible = False
    s_race_line.xgrid.visible = False
    s_race_line.ygrid.visible = False

    throttle_line = s_race_line.line(
        x="raceline_x_throttle",
        y="raceline_z_throttle",
        legend_label="Throttle Last Lap",
        line_width=5,
        color="green",
        source=ColumnDataSource(
            data={"raceline_z_throttle": [], "raceline_x_throttle": []}
        ),
    )
    breaking_line = s_race_line.line(
        x="raceline_x_braking",
        y="raceline_z_braking",
        legend_label="Braking Last Lap",
        line_width=5,
        color="red",
        source=ColumnDataSource(
            data={"raceline_z_braking": [], "raceline_x_braking": []}
        ),
    )

    coasting_line = s_race_line.line(
        x="raceline_x_coasting",
        y="raceline_z_coasting",
        legend_label="Coasting Last Lap",
        line_width=5,
        color="blue",
        source=ColumnDataSource(
            data={"raceline_z_coasting": [], "raceline_x_coasting": []}
        ),
    )

    # Reference Lap

    reference_throttle_line = s_race_line.line(
        x="raceline_x_throttle",
        y="raceline_z_throttle",
        legend_label="Throttle Reference",
        line_width=15,
        alpha=0.3,
        color="green",
        source=ColumnDataSource(
            data={"raceline_z_throttle": [], "raceline_x_throttle": []}
        ),
    )
    reference_breaking_line = s_race_line.line(
        x="raceline_x_braking",
        y="raceline_z_braking",
        legend_label="Braking Reference",
        line_width=15,
        alpha=0.3,
        color="red",
        source=ColumnDataSource(
            data={"raceline_z_braking": [], "raceline_x_braking": []}
        ),
    )

    reference_coasting_line = s_race_line.line(
        x="raceline_x_coasting",
        y="raceline_z_coasting",
        legend_label="Coasting Reference",
        line_width=15,
        alpha=0.3,
        color="blue",
        source=ColumnDataSource(
            data={"raceline_z_coasting": [], "raceline_x_coasting": []}
        ),
    )

    s_race_line.legend.visible = True

    s_race_line.add_layout(s_race_line.legend[0], "right")

    s_race_line.legend.click_policy = "hide"

    return (
        s_race_line,
        throttle_line,
        breaking_line,
        coasting_line,
        reference_throttle_line,
        reference_breaking_line,
        reference_coasting_line,
    )

class RaceTimeTable(object):

    def __init__(self):

        self.columns = [
            TableColumn(field="number", title="#"),
            TableColumn(field="time", title="Time"),
            TableColumn(field="diff", title="Diff"),
            TableColumn(field="info", title="Info"),
            TableColumn(field="fuelconsumed", title="Fuel Cons."),
            TableColumn(field="fullthrottle", title="Full Throt."),
            TableColumn(field="fullbreak", title="Full Break"),
            TableColumn(field="nothrottle", title="Coast"),
            TableColumn(field="tyrespinning", title="Tire Spin"),
            TableColumn(field="car_name", title="Car"),
        ]

        self.lap_times_source = ColumnDataSource(
            gt7helper.pd_data_frame_from_lap([], best_lap_time=0)
        )
        self.t_lap_times: DataTable

        self.t_lap_times = DataTable(
            source=self.lap_times_source, columns=self.columns, index_position=None, css_classes=["lap_times_table"]
        )
        # This will lead to not being rendered
        # self.t_lap_times.autosize_mode = "fit_columns"
        # Maybe this is related: https://github.com/bokeh/bokeh/issues/10512 ?


    def show_laps(self, laps: List[Lap]):
        best_lap = gt7helper.get_best_lap(laps)
        if best_lap == None:
            return

        new_df = gt7helper.pd_data_frame_from_lap(laps, best_lap_time=best_lap.lap_finish_time)
        self.lap_times_source.data = ColumnDataSource.from_df(new_df)

class RaceDiagram(object):
    def __init__(self, width=400):
        """
        Returns figures for time-diff, speed, throttling, braking and coasting.
        All with lines for last lap, best lap and median lap.
        The last return value is the sources object, that has to be altered
        to display data.
        """

        self.speed_lines = []
        self.braking_lines = []
        self.coasting_lines = []
        self.throttle_lines = []
        self.tires_lines = []
        self.rpm_lines = []
        self.gears_lines = []
        self.boost_lines = []
        self.yaw_rate_lines = []

        # Data Sources
        self.source_time_diff = None
        self.source_speed_variance = None
        self.source_last_lap = None
        self.source_reference_lap = None
        self.source_median_lap = None
        self.sources_additional_laps = []

        self.additional_laps = List[Lap]

        # This is the number of default laps,
        # last lap, best lap and median lap
        self.number_of_default_laps = 3


        tooltips = [
            ("index", "$index"),
            ("value", "$y"),
            ("Speed", "@speed{0}"),
            ("Yaw Rate", "@yaw_rate{0.00}"),
            ("Throttle", "@throttle%"),
            ("Brake", "@brake%"),
            ("Coast", "@coast%"),
            ("Gear", "@gear"),
            ("Rev", "@rpm{0} RPM"),
            ("Distance", "@distance{0} m"),
            ("Boost", "@boost{0.00} x 100 kPa"),
        ]

        tooltips_timedelta = [
            ("index", "$index"),
            ("timedelta", "@timedelta{0} ms"),
            ("reference", "@reference{0} ms"),
            ("comparison", "@comparison{0} ms"),
        ]

        self.tooltips_speed_variance = [
            ("index", "$index"),
            ("Distance", "@distance{0} m"),
            ("Spd. Deviation", "@speed_variance{0}"),
        ]

        self.f_speed = figure(
            title="Last, Reference, Median",
            y_axis_label="Speed",
            width=width,
            height=250,
            tooltips=tooltips,
            active_drag="box_zoom",
        )

        self.f_speed_variance = figure(
            y_axis_label="Spd.Dev.",
            x_range=self.f_speed.x_range,
            y_range=Range1d(0, 50),
            width=width,
            height=int(self.f_speed.height / 4),
            tooltips=self.tooltips_speed_variance,
            active_drag="box_zoom",
        )

        self.f_time_diff = figure(
            title="Time Diff - Last, Reference",
            x_range=self.f_speed.x_range,
            y_axis_label="Time / Diff",
            width=width,
            height=int(self.f_speed.height / 2),
            tooltips=tooltips_timedelta,
            active_drag="box_zoom",
        )

        self.f_throttle = figure(
            x_range=self.f_speed.x_range,
            y_axis_label="Throttle",
            width=width,
            height=int(self.f_speed.height / 2),
            tooltips=tooltips,
            active_drag="box_zoom",
        )
        self.f_braking = figure(
            x_range=self.f_speed.x_range,
            y_axis_label="Braking",
            width=width,
            height=int(self.f_speed.height / 2),
            tooltips=tooltips,
            active_drag="box_zoom",
        )

        self.f_coasting = figure(
            x_range=self.f_speed.x_range,
            y_axis_label="Coasting",
            width=width,
            height=int(self.f_speed.height / 2),
            tooltips=tooltips,
            active_drag="box_zoom",
        )

        self.f_tires = figure(
            x_range=self.f_speed.x_range,
            y_axis_label="Tire Spd / Car Spd",
            width=width,
            height=int(self.f_speed.height / 2),
            tooltips=tooltips,
            active_drag="box_zoom",
        )

        self.f_rpm = figure(
            x_range=self.f_speed.x_range,
            y_axis_label="RPM",
            width=width,
            height=int(self.f_speed.height / 2),
            tooltips=tooltips,
            active_drag="box_zoom",
        )

        self.f_gear = figure(
            x_range=self.f_speed.x_range,
            y_axis_label="Gear",
            width=width,
            height=int(self.f_speed.height / 2),
            tooltips=tooltips,
            active_drag="box_zoom",
        )

        self.f_boost = figure(
            x_range=self.f_speed.x_range,
            y_axis_label="Boost",
            width=width,
            height=int(self.f_speed.height / 2),
            tooltips=tooltips,
            active_drag="box_zoom",
        )

        self.f_yaw_rate = figure(
            x_range=self.f_speed.x_range,
            y_axis_label="Yaw Rate / Second",
            width=width,
            height=int(self.f_speed.height / 2),
            tooltips=tooltips,
            active_drag="box_zoom",
        )

        self.f_speed.toolbar.autohide = True

        span_zero_time_diff = bokeh.models.Span(
            location=0,
            dimension="width",
            line_color="black",
            line_dash="dashed",
            line_width=1,
        )
        self.f_time_diff.add_layout(span_zero_time_diff)

        self.f_time_diff.toolbar.autohide = True

        self.f_speed_variance.xaxis.visible = False
        self.f_speed_variance.toolbar.autohide = True

        self.f_throttle.xaxis.visible = False
        self.f_throttle.toolbar.autohide = True

        self.f_braking.xaxis.visible = False
        self.f_braking.toolbar.autohide = True

        self.f_coasting.xaxis.visible = False
        self.f_coasting.toolbar.autohide = True

        self.f_tires.xaxis.visible = False
        self.f_tires.toolbar.autohide = True

        self.f_gear.xaxis.visible = False
        self.f_gear.toolbar.autohide = True

        self.f_rpm.xaxis.visible = False
        self.f_rpm.toolbar.autohide = True

        self.f_boost.xaxis.visible = False
        self.f_boost.toolbar.autohide = True

        self.f_yaw_rate.xaxis.visible = False
        self.f_yaw_rate.toolbar.autohide = True

        self.source_time_diff = ColumnDataSource(data={"distance": [], "timedelta": []})
        self.f_time_diff.line(
            x="distance",
            y="timedelta",
            source=self.source_time_diff,
            line_width=1,
            color="blue",
            line_alpha=1,
        )

        self.source_last_lap = self.add_lap_to_race_diagram("blue", "Last Lap", True)

        self.source_reference_lap = self.add_lap_to_race_diagram("magenta", "Reference Lap", True)

        self.source_median_lap = self.add_lap_to_race_diagram("green", "Median Lap", False)

        self.f_speed.legend.click_policy = "hide"
        self.f_throttle.legend.click_policy = self.f_speed.legend.click_policy
        self.f_braking.legend.click_policy = self.f_speed.legend.click_policy
        self.f_coasting.legend.click_policy = self.f_speed.legend.click_policy
        self.f_tires.legend.click_policy = self.f_speed.legend.click_policy
        self.f_gear.legend.click_policy = self.f_speed.legend.click_policy
        self.f_rpm.legend.click_policy = self.f_speed.legend.click_policy
        self.f_boost.legend.click_policy = self.f_speed.legend.click_policy
        self.f_yaw_rate.legend.click_policy = self.f_speed.legend.click_policy

        # Leave padding on the left because rpm is 4 digits and diagrams will not start at the same position otherwise
        min_border_left = 60
        self.f_time_diff.min_border_left = min_border_left
        self.f_speed.min_border_left = min_border_left
        self.f_throttle.min_border_left = min_border_left
        self.f_braking.min_border_left = min_border_left
        self.f_coasting.min_border_left = min_border_left
        self.f_tires.min_border_left = min_border_left
        self.f_gear.min_border_left = min_border_left
        self.f_rpm.min_border_left = min_border_left
        self.f_speed_variance.min_border_left = min_border_left
        self.f_boost.min_border_left = min_border_left
        self.f_yaw_rate.min_border_left = min_border_left

        self.layout = layout(self.f_time_diff, self.f_speed, self.f_speed_variance, self.f_throttle, self.f_yaw_rate, self.f_braking, self.f_coasting, self.f_tires, self.f_gear, self.f_rpm, self.f_boost)

        self.source_speed_variance = ColumnDataSource(data={"distance": [], "speed_variance": []})

        self.f_speed_variance.line(
            x="distance",
            y="speed_variance",
            source=self.source_speed_variance,
            line_width=1,
            color="gray",
            line_alpha=1,
            visible=True
        )

    def add_additional_lap_to_race_diagram(self, color: str, lap: Lap, visible: bool = True):
        source = self.add_lap_to_race_diagram(color, lap.title, visible)
        source.data = lap.get_data_dict()
        self.sources_additional_laps.append(source)

    def update_fastest_laps_variance(self, laps):
        # FIXME, many many data points, mayabe reduce by the amount of laps?
        variance, fastest_laps = gt7helper.get_variance_for_fastest_laps(laps)
        self.source_speed_variance.data = variance
        return fastest_laps

    def add_lap_to_race_diagram(self, color: str, legend: str, visible: bool = True):

        # Set empty data for avoiding warnings about missing columns
        dummy_data = Lap().get_data_dict()

        source = ColumnDataSource(data=dummy_data)

        self.speed_lines.append(self.f_speed.line(
            x="distance",
            y="speed",
            source=source,
            legend_label=legend,
            line_width=1,
            color=color,
            line_alpha=1,
            visible=visible
        ))

        self.throttle_lines.append(self.f_throttle.line(
            x="distance",
            y="throttle",
            source=source,
            legend_label=legend,
            line_width=1,
            color=color,
            line_alpha=1,
            visible=visible
        ))

        self.braking_lines.append(self.f_braking.line(
            x="distance",
            y="brake",
            source=source,
            legend_label=legend,
            line_width=1,
            color=color,
            line_alpha=1,
            visible=visible
        ))

        self.coasting_lines.append(self.f_coasting.line(
            x="distance",
            y="coast",
            source=source,
            legend_label=legend,
            line_width=1,
            color=color,
            line_alpha=1,
            visible=visible
        ))

        self.tires_lines.append(self.f_tires.line(
            x="distance",
            y="tires",
            source=source,
            legend_label=legend,
            line_width=1,
            color=color,
            line_alpha=1,
            visible=visible
        ))

        self.gears_lines.append(self.f_gear.line(
            x="distance",
            y="gear",
            source=source,
            legend_label=legend,
            line_width=1,
            color=color,
            line_alpha=1,
            visible=visible
        ))

        self.rpm_lines.append(self.f_rpm.line(
            x="distance",
            y="rpm",
            source=source,
            legend_label=legend,
            line_width=1,
            color=color,
            line_alpha=1,
            visible=visible
        ))

        self.boost_lines.append(self.f_boost.line(
            x="distance",
            y="boost",
            source=source,
            legend_label=legend,
            line_width=1,
            color=color,
            line_alpha=1,
            visible=visible
        ))

        self.yaw_rate_lines.append(self.f_yaw_rate.line(
            x="distance",
            y="yaw_rate",
            source=source,
            legend_label=legend,
            line_width=1,
            color=color,
            line_alpha=1,
            visible=visible
        ))

        return source

    def get_layout(self) -> Column:
        return self.layout

    def delete_all_additional_laps(self):
        # Delete all but first three in list
        self.sources_additional_laps = []

        for i, _ in enumerate(self.f_speed.renderers):
            if i >= self.number_of_default_laps:
                self.f_speed.renderers.remove(self.f_speed.renderers[i])  # remove the line renderer
                self.f_throttle.renderers.remove(self.f_throttle.renderers[i])  # remove the line renderer
                self.f_braking.renderers.remove(self.f_braking.renderers[i])  # remove the line renderer
                self.f_coasting.renderers.remove(self.f_coasting.renderers[i])  # remove the line renderer
                self.f_tires.renderers.remove(self.f_tires.renderers[i])  # remove the line renderer
                self.f_boost.renderers.remove(self.f_boost.renderers[i])  # remove the line renderer
                self.f_yaw_rate.renderers.remove(self.f_yaw_rate.renderers[i])  # remove the line renderer
                # self.f_time_diff.renderers.remove(self.f_time_diff.renderers[i])  # remove the line renderer

                self.f_speed.legend.items.pop(i)
                self.f_throttle.legend.items.pop(i)
                self.f_braking.legend.items.pop(i)
                self.f_coasting.legend.items.pop(i)
                self.f_tires.legend.items.pop(i)
                self.f_yaw_rate.legend.items.pop(i)
                self.f_boost.legend.items.pop(i)
                # self.f_time_diff.legend.items.pop(i)






def add_annotations_to_race_line(
    race_line: figure, last_lap: Lap, reference_lap: Lap
):
    """ Adds annotations such as speed peaks and valleys and the starting line to the racing line"""

    remove_all_annotation_text_from_figure(race_line)

    decorations = []
    decorations.extend(
        _add_peaks_and_valley_decorations_for_lap(
            last_lap, race_line, color="blue", offset=0
        )
    )
    decorations.extend(
        _add_peaks_and_valley_decorations_for_lap(
            reference_lap, race_line, color="magenta", offset=0
        )
    )
    add_starting_line_to_diagram(race_line, last_lap)

    # This is multiple times faster by adding all texts at once rather than adding them above
    # With around 20 positions, this took 27s before.
    # Maybe this has something to do with every text being transmitted over network
    race_line.center.extend(decorations)

    # Add peaks and valleys of last lap


def _add_peaks_and_valley_decorations_for_lap(
    lap: Lap, race_line: figure, color, offset
):
    (
        peak_speed_data_x,
        peak_speed_data_y,
        valley_speed_data_x,
        valley_speed_data_y,
    ) = lap.get_speed_peaks_and_valleys()

    decorations = []

    for i in range(len(peak_speed_data_x)):
        # shift 10 px to the left
        position_x = lap.data_position_x[peak_speed_data_y[i]]
        position_y = lap.data_position_z[peak_speed_data_y[i]]

        mytext = Label(
            x=position_x,
            y=position_y,
            text_color=color,
            text_font_size="10pt",
            text_font_style="bold",
            x_offset=offset,
            background_fill_color="white",
            background_fill_alpha=0.75,
        )
        mytext.text = "▴%.0f" % peak_speed_data_x[i]

        decorations.append(mytext)

    for i in range(len(valley_speed_data_x)):
        position_x = lap.data_position_x[valley_speed_data_y[i]]
        position_y = lap.data_position_z[valley_speed_data_y[i]]

        mytext = Label(
            x=position_x,
            y=position_y,
            text_color=color,
            text_font_size="10pt",
            x_offset=offset,
            text_font_style="bold",
            background_fill_color="white",
            background_fill_alpha=0.75,
            text_align="right",
        )
        mytext.text = "%.0f▾" % valley_speed_data_x[i]

        decorations.append(mytext)

    return decorations


def remove_all_annotation_text_from_figure(f: figure):
    f.center = [r for r in f.center if not isinstance(r, Label)]


def get_fuel_map_html_table(last_lap: Lap) -> str:
    """
    Returns a html table of relative fuel map.
    :param last_lap:
    :return: html table
    """

    fuel_maps = gt7helper.get_fuel_on_consumption_by_relative_fuel_levels(last_lap)
    table = (
        "<table><tr>"
        "<th title='The fuel level relative to the current one'>Fuel Lvl.</th>"
        "<th title='Fuel consumed'>Fuel Cons.</th>"
        "<th title='Laps remaining with this setting'>Laps Rem.</th>"
        "<th title='Time remaining with this setting' >Time Rem.</th>"
        "<th title='Time Diff to last lap with this setting'>Time Diff</th></tr>"
    )
    for fuel_map in fuel_maps:
        no_fuel_consumption = fuel_map.fuel_consumed_per_lap <= 0
        line_style = ""
        if fuel_map.mixture_setting == 0 and not no_fuel_consumption:
            line_style = "background-color:rgba(0,255,0,0.5)"
        table += (
                "<tr id='fuel_map_row_%d' style='%s'>"
                "<td style='text-align:center'>%d</td>"
                "<td style='text-align:center'>%d</td>"
                "<td style='text-align:center'>%.1f</td>"
                "<td style='text-align:center'>%s</td>"
                "<td style='text-align:center'>%s</td>"
                "</tr>"
                % (
                    fuel_map.mixture_setting,
                    line_style,
                    fuel_map.mixture_setting,
                    0 if no_fuel_consumption else fuel_map.fuel_consumed_per_lap,
                    0 if no_fuel_consumption else fuel_map.laps_remaining_on_current_fuel,
                    "No Fuel" if no_fuel_consumption else (gt7helper.seconds_to_lap_time(
                        fuel_map.time_remaining_on_current_fuel / 1000
                    )),
                    "Consumption" if no_fuel_consumption else (gt7helper.seconds_to_lap_time(fuel_map.lap_time_diff / 1000)),
                )
        )
    table += "</table>"
    table += "<p>Fuel Remaining: <b>%d</b></p>" % last_lap.fuel_at_end
    return table


def add_starting_line_to_diagram(race_line: figure, last_lap: Lap):

    if len(last_lap.data_position_z) == 0:
        return

    x = last_lap.data_position_x[0]
    y = last_lap.data_position_z[0]

    # We use a text because scatters are too memory consuming
    # and cannot be easily removed from the diagram
    mytext = Label(
        x=x,
        y=y,
        text_font_size="10pt",
        text_font_style="bold",
        background_fill_color="white",
        background_fill_alpha=0.25,
        text_align="center",
    )
    mytext.text = "===="
    race_line.center.append(mytext)

def get_speed_peak_and_valley_diagram(last_lap: Lap, reference_lap: Lap) -> str:
    """
    Returns a html div with the speed peaks and valleys of the last lap and the reference lap
    as a formatted html table
    :param last_lap: Lap
    :param reference_lap: Lap
    :return: html table with peaks and valleys
    """
    table = """<table style='border-spacing: 10px; text-align:center'>"""

    table += """<colgroup>
    <col/>
    <col style='border-left: 1px solid #cdd0d4;'/>
    <col/>
    <col/>
    <col style="background-color: lightblue;"/>
    <col/>
    <col/>
    <col/>
    <col style="background-color: thistle;"/>
    <col/>
  </colgroup>"""

    ll_tuple_list = gt7helper.get_peaks_and_valleys_sorted_tuple_list(last_lap)
    rl_tuple_list = gt7helper.get_peaks_and_valleys_sorted_tuple_list(reference_lap)

    max_data = max(len(ll_tuple_list), len(rl_tuple_list))

    table += '<tr>'

    table += '<th></th>'
    table += '<th colspan="4">%s - %s</th>' % ("Last", last_lap.title)
    table += '<th colspan="4">%s - %s</th>' % ("Ref.", reference_lap.title)
    table += '<th colspan="2">Diff</th>'

    table += '</tr>'

    table += """<tr>
    <td></td><td>#</td><td></td><td>Pos.</td><td>Speed</td>
    <td>#</td><td></td><td>Pos.</td><td>Speed</td>
    <td>Pos.</td><td>Speed</td>
    </tr>"""

    rl_and_ll_are_same_size = len(ll_tuple_list) == len(rl_tuple_list)

    i = 0
    while i < max_data:
        diff_pos = 0
        diff_speed = 0

        if rl_and_ll_are_same_size:
            diff_pos = ll_tuple_list[i][1] - rl_tuple_list[i][1]
            diff_speed = ll_tuple_list[i][0] - rl_tuple_list[i][0]

            if diff_speed > 0:
                diff_style = f"color: rgba(0, 0, 255, .3)" # Blue
            elif diff_speed >= -3:
                diff_style = f"color: rgba(0, 255, 0, .3)" # Green
            elif diff_speed >= -10:
                diff_style = f"color: rgba(251, 192, 147, .3)" # Orange
            else:
                diff_style = f"color: rgba(255, 0, 0, .3)" # Red

        else:
            diff_style = f"text-color: rgba(255, 0, 0, .3)" # Red

        table += '<tr>'
        table += f'<td style="width:15px; text-opacity:0.5; {diff_style}">█</td>'

        if len(ll_tuple_list) > i:
            table += f"""<td>{i+1}</td>
                <td>{"S" if ll_tuple_list[i][2] == gt7helper.PEAK else "T"}</td>
                <td>{ll_tuple_list[i][1]:d}</td>
                <td>{ll_tuple_list[i][0]:.0f}</td>
            """

        if len(rl_tuple_list) > i:
            table += f"""<td>{i+1}</td>
                <td>{"S" if rl_tuple_list[i][2] == gt7helper.PEAK else "T"}</td>
                <td>{rl_tuple_list[i][1]:d}</td>
                <td>{rl_tuple_list[i][0]:.0f}</td>
            """

        if rl_and_ll_are_same_size:
            table += f"""
                <td>{diff_pos:d}</td>
                <td>{diff_speed:.0f}</td>
            """
        else:
            table += f"""
                <td>-</td>
                <td>-</td>
            """



        table += '</tr>'
        i+=1



    table += '</td>'
    table += '<td>'

    table += '</td>'

    table = table + """</table>"""
    return table


def get_speed_peak_and_valley_diagram_row(peak_speed_data_x, peak_speed_data_y, table, valley_speed_data_x,
                                          valley_speed_data_y):
    row = ""

    row += "<tr><th>#</th><th>Peak</th><th>Position</th></tr>"
    for i, dx in enumerate(peak_speed_data_x):
        row += "<tr><td>%d.</td><td>%d kph</td><td>%d</td></tr>" % (
            i + 1,
            peak_speed_data_x[i],
            peak_speed_data_y[i],
        )
    row += "<tr><th>#</th><th>Valley</th><th>Position</th></tr>"
    for i, dx in enumerate(valley_speed_data_x):
        row += "<tr><td>%d.</td><td>%d kph</td><td>%d</td></tr>" % (
            i + 1,
            valley_speed_data_x[i],
            valley_speed_data_y[i],
        )
    return row
