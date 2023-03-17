import bokeh
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure, Figure

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
        legend_label="Throttle",
        line_width=5,
        color="green",
        source=ColumnDataSource(
            data={"raceline_z_throttle": [], "raceline_x_throttle": []}
        ),
    )
    breaking_line = s_race_line.line(
        x="raceline_z_braking",
        y="raceline_x_braking",
        legend_label="Braking",
        line_width=5,
        color="red",
        source=ColumnDataSource(
            data={"raceline_z_braking": [], "raceline_x_braking": []}
        ),
    )

    coasting_line = s_race_line.line(
        x="raceline_z_coasting",
        y="raceline_x_coasting",
        legend_label="Coasting",
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
        legend_label="Throttle",
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
        legend_label="Braking",
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
        legend_label="Coasting",
        line_width=15,
        alpha=0.3,
        color="blue",
        source=ColumnDataSource(
            data={"raceline_z_coasting": [], "raceline_x_coasting": []}
        ),
    )

    # FIXME: Does not work
    s_race_line.legend.visible = False

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
) -> tuple[Figure, Figure, Figure, Figure, Figure, list[ColumnDataSource]]:
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

        f_speed.line(
            x="distance",
            y="speed",
            source=source,
            legend_label=legend,
            line_width=1,
            color=color,
            line_alpha=1,
        )
        f_throttle.line(
            x="distance",
            y="throttle",
            source=source,
            legend_label=legend,
            line_width=1,
            color=color,
            line_alpha=1,
        )
        f_braking.line(
            x="distance",
            y="brake",
            source=source,
            legend_label=legend,
            line_width=1,
            color=color,
            line_alpha=1,
        )
        f_coasting.line(
            x="distance",
            y="coast",
            source=source,
            legend_label=legend,
            line_width=1,
            color=color,
            line_alpha=1,
        )

    f_speed.legend.click_policy = "hide"
    f_throttle.legend.click_policy = f_speed.legend.click_policy
    f_braking.legend.click_policy = f_speed.legend.click_policy
    f_coasting.legend.click_policy = f_speed.legend.click_policy

    return f_time_diff, f_speed, f_throttle, f_braking, f_coasting, sources
