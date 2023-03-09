from bokeh.models import ColumnDataSource
from bokeh.plotting import figure


def get_throttle_braking_race_line_diagram(race_line_width=250):

    # TODO Make this work
    race_line_tooltips = [("index", "$index"), ("Breakpoint", "")]
    s_race_line = figure(
        title="Race Line",
        x_axis_label="z",
        y_axis_label="x",
        match_aspect=True,
        width=race_line_width,
        height=race_line_width,
        active_drag="box_zoom",
        tooltips=race_line_tooltips,
    )
    s_race_line.toolbar.autohide = True
    # FIXME: Does not work
    s_race_line.legend.visible = False

    throttle_line = s_race_line.line(
        x="raceline_z_throttle",
        y="raceline_x_throttle",
        legend_label="Throttle",
        line_width=5,
        color="green",
        source=ColumnDataSource(data={"raceline_z_throttle": [], "raceline_x_throttle": []})
    )
    breaking_line = s_race_line.line(
        x="raceline_z_braking",
        y="raceline_x_braking",
        legend_label="Braking",
        line_width=5,
        color="red",
        source=ColumnDataSource(data={"raceline_z_braking": [], "raceline_x_braking": []})
    )

    coasting_line = s_race_line.line(
        x="raceline_z_coasting",
        y="raceline_x_coasting",
        legend_label="Coasting",
        line_width=5,
        color="blue",
        source=ColumnDataSource(data={"raceline_z_coasting": [], "raceline_x_coasting": []})
    )

    return s_race_line, throttle_line, breaking_line, coasting_line
