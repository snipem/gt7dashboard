from bokeh.models import Div

from gt7dashboard import gt7helper

SPEED_VARIANCE_HELP = f"""Displays the speed deviation of the fastest laps within a {gt7helper.DEFAULT_FASTEST_LAPS_PERCENT_THRESHOLD * 100}% time difference threshold of the fastest lap.
Replay laps are ignored. The speed deviation is calculated as the standard deviation between these fastest laps.

With a perfect driver in an ideal world, this line would be flat. In a real world situation, you will get an almost flat line, 
with bumps at the corners and long straights. This is where even your best laps deviate.

You may get some insights for improvement on your consistency if you look at the points of the track where this line is bumpy."""

SPEED_PEAKS_AND_VALLEYS_HELP = ""


def get_help_div(help_text_resource):
    return Div(text=get_help_text_resource(help_text_resource), width=5, height=5)


def get_help_text_resource(help_text_resource):
    return f"""
    <div title="{help_text_resource}">?⃝</div>
    """
