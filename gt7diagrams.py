from typing import Tuple, List

import bokeh
from bokeh.layouts import row
from bokeh.models import ColumnDataSource, Label, Legend, LegendItem
from bokeh.plotting import figure

import gt7helper
from gt7lap import Lap


def get_throttle_braking_race_line_diagram():
    # TODO Make this work, tooltips just show breakpoint
    race_line_tooltips = [("index", "$index")]
    s_race_line = figure(
        title="Race Line",
        match_aspect=True,
        active_scroll="wheel_zoom",
        tooltips=race_line_tooltips,
    )
    s_race_line.toolbar.autohide = True

    s_race_line.axis.visible = False
    s_race_line.xgrid.visible = False
    s_race_line.ygrid.visible = False

    throttle_line = s_race_line.line(
        x="raceline_z_throttle",
        y="raceline_x_throttle",
        legend_label="Throttle Last Lap",
        line_width=5,
        color="green",
        source=ColumnDataSource(
            data={"raceline_z_throttle": [], "raceline_x_throttle": []}
        ),
    )
    breaking_line = s_race_line.line(
        x="raceline_z_braking",
        y="raceline_x_braking",
        legend_label="Braking Last Lap",
        line_width=5,
        color="red",
        source=ColumnDataSource(
            data={"raceline_z_braking": [], "raceline_x_braking": []}
        ),
    )

    coasting_line = s_race_line.line(
        x="raceline_z_coasting",
        y="raceline_x_coasting",
        legend_label="Coasting Last Lap",
        line_width=5,
        color="blue",
        source=ColumnDataSource(
            data={"raceline_z_coasting": [], "raceline_x_coasting": []}
        ),
    )

    # Reference Lap

    reference_throttle_line = s_race_line.line(
        x="raceline_z_throttle",
        y="raceline_x_throttle",
        legend_label="Throttle Reference",
        line_width=15,
        alpha=0.3,
        color="green",
        source=ColumnDataSource(
            data={"raceline_z_throttle": [], "raceline_x_throttle": []}
        ),
    )
    reference_breaking_line = s_race_line.line(
        x="raceline_z_braking",
        y="raceline_x_braking",
        legend_label="Braking Reference",
        line_width=15,
        alpha=0.3,
        color="red",
        source=ColumnDataSource(
            data={"raceline_z_braking": [], "raceline_x_braking": []}
        ),
    )

    reference_coasting_line = s_race_line.line(
        x="raceline_z_coasting",
        y="raceline_x_coasting",
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


def get_throttle_velocity_diagram_for_reference_lap_and_last_lap(
    width: int,
) -> tuple[figure, figure, figure, figure, figure, figure, list[ColumnDataSource]]:
    """
    Returns figures for time-diff, speed, throttling, braking and coasting.
    All with lines for last lap, best lap and median lap.
    The last return value is the sources object, that has to be altered
    to display data.
    """
    tooltips = [
        ("index", "$index"),
        ("value", "$y"),
        ("Speed", "@speed{0} kph"),
        ("Throttle", "@throttle%"),
        ("Brake", "@brake%"),
        ("Coast", "@coast%"),
        ("Distance", "@distance{0} m"),
    ]

    tooltips_timedelta = [
        ("index", "$index"),
        ("timedelta", "@timedelta{0} ms"),
        ("reference", "@reference{0} ms"),
        ("comparison", "@comparison{0} ms"),
    ]
    colors = ["blue", "magenta", "green"]
    legends = ["Last Lap", "Reference Lap", "Median Lap"]

    f_speed = figure(
        title="Last, Reference, Median",
        y_axis_label="Speed",
        width=width,
        height=250,
        tooltips=tooltips,
        active_drag="box_zoom",
    )

    f_time_diff = figure(
        title="Time Diff - Last, Reference",
        x_range=f_speed.x_range,
        y_axis_label="Time / Diff",
        width=width,
        height=int(f_speed.height / 2),
        tooltips=tooltips_timedelta,
        active_drag="box_zoom",
    )

    f_throttle = figure(
        x_range=f_speed.x_range,
        y_axis_label="Throttle",
        width=width,
        height=int(f_speed.height / 2),
        tooltips=tooltips,
        active_drag="box_zoom",
    )
    f_braking = figure(
        x_range=f_speed.x_range,
        y_axis_label="Braking",
        width=width,
        height=int(f_speed.height / 2),
        tooltips=tooltips,
        active_drag="box_zoom",
    )

    f_coasting = figure(
        x_range=f_speed.x_range,
        y_axis_label="Coasting",
        width=width,
        height=int(f_speed.height / 2),
        tooltips=tooltips,
        active_drag="box_zoom",
    )

    f_tires = figure(
        x_range=f_speed.x_range,
        y_axis_label="Tire Spd / Car Spd",
        width=width,
        height=int(f_speed.height / 2),
        tooltips=tooltips,
        active_drag="box_zoom",
    )

    f_speed.toolbar.autohide = True

    span_zero_time_diff = bokeh.models.Span(
        location=0,
        dimension="width",
        line_color="black",
        line_dash="dashed",
        line_width=1,
    )
    f_time_diff.add_layout(span_zero_time_diff)

    f_time_diff.toolbar.autohide = True

    f_throttle.xaxis.visible = False
    f_throttle.toolbar.autohide = True

    f_braking.xaxis.visible = False
    f_braking.toolbar.autohide = True

    f_coasting.xaxis.visible = False
    f_coasting.toolbar.autohide = True

    f_tires.xaxis.visible = False
    f_tires.toolbar.autohide = True

    sources = []

    time_diff_source = ColumnDataSource(data={"distance": [], "timedelta": []})
    f_time_diff.line(
        x="distance",
        y="timedelta",
        source=time_diff_source,
        line_width=1,
        color="blue",
        line_alpha=1,
    )
    sources.append(time_diff_source)

    # Set empty data for avoiding warnings about missing columns
    dummy_data = gt7helper.get_data_dict_from_lap(Lap(), distance_mode=True)

    for color, legend in zip(colors, legends):
        source = ColumnDataSource(data=dummy_data)
        sources.append(source)

        if legend == "Median Lap":
            visible = False
        else:
            visible = True

        f_speed.line(
            x="distance",
            y="speed",
            source=source,
            legend_label=legend,
            line_width=1,
            color=color,
            line_alpha=1,
            visible=visible
        )
        f_throttle.line(
            x="distance",
            y="throttle",
            source=source,
            legend_label=legend,
            line_width=1,
            color=color,
            line_alpha=1,
            visible=visible
        )
        f_braking.line(
            x="distance",
            y="brake",
            source=source,
            legend_label=legend,
            line_width=1,
            color=color,
            line_alpha=1,
            visible=visible
        )
        f_coasting.line(
            x="distance",
            y="coast",
            source=source,
            legend_label=legend,
            line_width=1,
            color=color,
            line_alpha=1,
            visible=visible
        )
        f_tires.line(
            x="distance",
            y="tires",
            source=source,
            legend_label=legend,
            line_width=1,
            color=color,
            line_alpha=1,
            visible=visible
        )


    f_speed.legend.click_policy = "hide"
    f_throttle.legend.click_policy = f_speed.legend.click_policy
    f_braking.legend.click_policy = f_speed.legend.click_policy
    f_coasting.legend.click_policy = f_speed.legend.click_policy
    f_tires.legend.click_policy = f_speed.legend.click_policy

    return f_time_diff, f_speed, f_throttle, f_braking, f_coasting, f_tires, sources


def add_peaks_and_valleys_to_diagram(
    race_line: figure, last_lap: Lap, reference_lap: Lap
):
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
        position_x = lap.data_position_z[peak_speed_data_y[i]]
        position_y = lap.data_position_x[peak_speed_data_y[i]]

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
        position_x = lap.data_position_z[valley_speed_data_y[i]]
        position_y = lap.data_position_x[valley_speed_data_y[i]]

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

def get_fuel_map_html_table(last_lap):
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
        no_fuel_consumption = fuel_map.fuel_consumed_per_lap == 0
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
                    fuel_map.fuel_consumed_per_lap,
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
