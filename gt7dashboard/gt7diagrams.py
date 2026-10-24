from typing import List

import bokeh
from bokeh.layouts import layout
from bokeh.models import ColumnDataSource, Label, Scatter, Column, Line, TableColumn, DataTable, Range1d
from bokeh.plotting import figure

from gt7dashboard import gt7helper
from gt7dashboard.gt7lap import Lap

# Distinct from the built-in last (blue), reference (magenta), and median (green) traces.
COMPARISON_LAP_COLORS = (
    "orange",
    "purple",
    "brown",
    "teal",
    "goldenrod",
    "gray",
    "crimson",
    "darkcyan",
    "olive",
    "coral",
)


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
            TableColumn(field="timestamp", title="Timestamp"),
            TableColumn(field="info", title="Info"),
            TableColumn(field="fuelconsumed", title="Fuel Cons."),
            TableColumn(field="fullthrottle", title="Full Throt."),
            TableColumn(field="fullbreak", title="Full Brake"),
            TableColumn(field="nothrottle", title="Coast"),
            TableColumn(field="tyrespinning", title="Tire Spin"),
            TableColumn(field="car_name", title="Car"),
        ]

        self.lap_times_source = ColumnDataSource(
            gt7helper.pd_data_frame_from_lap([], best_lap_time=0)
        )
        self.t_lap_times: DataTable

        # CheckboxEditor opens an editor and waits for a second click before it
        # commits. The checkbox selection column toggles one row on the first
        # click and does not follow ordinary row highlighting.
        self.t_lap_times = DataTable(
            source=self.lap_times_source,
            columns=self.columns,
            index_position=None,
            selectable="checkbox",
            frozen_columns=1,
            css_classes=["lap_times_table"],
        )
        # This will lead to not being rendered
        # self.t_lap_times.autosize_mode = "fit_columns"
        # Maybe this is related: https://github.com/bokeh/bokeh/issues/10512 ?
        self.laps: List[Lap] = []
        self._syncing = False

    @property
    def syncing(self) -> bool:
        return self._syncing

    def show_laps(self, laps: List[Lap], plotted_laps: List[Lap] = None):
        """Replace the rows and check the boxes for laps that are already plotted."""
        self.laps = list(laps)
        if plotted_laps is None:
            plotted_laps = []

        indices = []
        for lap in plotted_laps:
            for index, candidate in enumerate(self.laps):
                if candidate is lap and index not in indices:
                    indices.append(index)
                    break

        self._syncing = True
        try:
            if self.laps:
                best_lap = gt7helper.get_best_lap(self.laps)
                new_df = gt7helper.pd_data_frame_from_lap(self.laps, best_lap_time=best_lap.lap_finish_time)
                self.lap_times_source.data = ColumnDataSource.from_df(new_df)
            else:
                self.lap_times_source.data = {
                    column.field: [] for column in self.columns
                }
            self.lap_times_source.selected.indices = indices
        finally:
            self._syncing = False

    def selected_laps(self) -> List[Lap]:
        chosen = []
        seen = set()
        for index in self.lap_times_source.selected.indices:
            if not isinstance(index, int) or index < 0 or index >= len(self.laps):
                continue
            lap = self.laps[index]
            if lap in seen:
                continue
            seen.add(lap)
            chosen.append(lap)
        return chosen

    def apply_plot_selection(self, diagram: "RaceDiagram"):
        diagram.sync_comparison_laps(self.selected_laps())

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
        # Lap object -> (ColumnDataSource, color). Identity, not table row, is the plotted state.
        self._comparison_by_lap = {}
        # Kept after a lap is unchecked so the same lap gets the same color again.
        self._comparison_color_by_lap = {}
        self._renderers_by_source = {}

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

    def _telemetry_series(self):
        return (
            (self.speed_lines, self.f_speed, "speed"),
            (self.throttle_lines, self.f_throttle, "throttle"),
            (self.braking_lines, self.f_braking, "brake"),
            (self.coasting_lines, self.f_coasting, "coast"),
            (self.tires_lines, self.f_tires, "tires"),
            (self.gears_lines, self.f_gear, "gear"),
            (self.rpm_lines, self.f_rpm, "rpm"),
            (self.boost_lines, self.f_boost, "boost"),
            (self.yaw_rate_lines, self.f_yaw_rate, "yaw_rate"),
        )

    def _comparison_color(self, lap: Lap) -> str:
        remembered = self._comparison_color_by_lap.get(lap)
        if remembered is not None:
            return remembered
        used = set(self._comparison_color_by_lap.values())
        for color in COMPARISON_LAP_COLORS:
            if color not in used:
                chosen = color
                break
        else:
            chosen = COMPARISON_LAP_COLORS[len(self._comparison_color_by_lap) % len(COMPARISON_LAP_COLORS)]
        self._comparison_color_by_lap[lap] = chosen
        return chosen

    def comparison_laps(self) -> List[Lap]:
        return list(self._comparison_by_lap.keys())

    def sync_comparison_laps(self, laps: List[Lap]):
        """Plot exactly these laps. Built-in traces are left in place."""
        desired = []
        seen = set()
        for lap in laps:
            if lap in seen:
                continue
            seen.add(lap)
            desired.append(lap)
        desired_set = set(desired)

        for lap in list(self._comparison_by_lap):
            if lap not in desired_set:
                self._remove_comparison(lap)
        for lap in desired:
            if lap not in self._comparison_by_lap:
                self._add_comparison(lap)

    def retain_comparison_laps(self, laps: List[Lap]):
        """Drop comparison traces whose lap is no longer in the session."""
        keep = set(laps)
        for lap in list(self._comparison_color_by_lap):
            if lap not in keep:
                del self._comparison_color_by_lap[lap]
        self.sync_comparison_laps([lap for lap in self.comparison_laps() if lap in keep])

    def _add_comparison(self, lap: Lap):
        if lap in self._comparison_by_lap:
            return self._comparison_by_lap[lap][0]
        color = self._comparison_color(lap)
        legend = lap.title or lap.format()
        source = self.add_lap_to_race_diagram(color, legend, True)
        source.data = lap.get_data_dict()
        self.sources_additional_laps.append(source)
        self._comparison_by_lap[lap] = (source, color)
        return source

    def _remove_comparison(self, lap: Lap):
        entry = self._comparison_by_lap.pop(lap, None)
        if entry is None:
            return
        self._detach_source(entry[0])

    def _detach_source(self, source):
        renderers = set(self._renderers_by_source.pop(source, []))
        for lines, fig, _field in self._telemetry_series():
            if renderers:
                lines[:] = [renderer for renderer in lines if renderer not in renderers]
                fig.renderers = [renderer for renderer in fig.renderers if renderer not in renderers]
                fig.legend.items = [
                    item for item in fig.legend.items
                    if not any(renderer in renderers for renderer in item.renderers)
                ]
        if source in self.sources_additional_laps:
            self.sources_additional_laps.remove(source)

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
        renderers = []

        for lines, fig, field in self._telemetry_series():
            renderer = fig.line(
                x="distance",
                y=field,
                source=source,
                legend_label=legend,
                line_width=1,
                color=color,
                line_alpha=1,
                visible=visible
            )
            lines.append(renderer)
            renderers.append(renderer)

        self._renderers_by_source[source] = renderers
        return source

    def get_layout(self) -> Column:
        return self.layout

    def delete_all_additional_laps(self):
        self._comparison_by_lap.clear()
        self._comparison_color_by_lap.clear()
        for source in list(self.sources_additional_laps):
            self._detach_source(source)
        self.sources_additional_laps.clear()






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
