import os
import pickle
from datetime import timedelta, datetime, timezone
from statistics import StatisticsError
from typing import Tuple, List

from pathlib import Path

import pandas as pd
from pandas import DataFrame
from scipy.signal import find_peaks
from tabulate import tabulate

from gt7lap import Lap


def save_laps(laps: List[Lap]):
    with open('data/all_laps.pickle', 'wb') as f:
        pickle.dump(laps, f)

def calculate_remaining_fuel(fuel_start_lap: int, fuel_end_lap: int, lap_time: int) -> Tuple[
    int, float, float]:

    # no fuel consumed
    if fuel_start_lap == fuel_end_lap:
        return 0, -1, -1

    # fuel consumed, calculate
    fuel_consumed_per_lap = fuel_start_lap - fuel_end_lap
    laps_remaining = fuel_end_lap / fuel_consumed_per_lap
    time_remaining = laps_remaining * lap_time

    return fuel_consumed_per_lap, laps_remaining, time_remaining

def get_x_axis_for_distance(lap: Lap) -> List:
    x_axis = []
    tick_time = 16.668 # https://www.gtplanet.net/forum/threads/gt7-is-compatible-with-motion-rig.410728/post-13806131
    for i, s in enumerate(lap.DataSpeed):
        # distance traveled + (Speed in km/h / 3.6 / 1000 = mm / ms) * tick_time
        if i == 0:
            x_axis.append(0)
            continue

        x_axis.append(x_axis[i-1] + (lap.DataSpeed[i] / 3.6 / 1000) * tick_time)

    return x_axis


def get_x_axis_depending_on_mode(lap: Lap, distance_mode: bool):
    if distance_mode:
        # Calculate distance for x axis
        return get_x_axis_for_distance(lap)
    else:
        # Use ticks as length, which is the length of any given data list
        return list(range(len(lap.DataSpeed)))
    pass


def get_time_delta_dataframe_for_lap(lap: Lap, name: str):

    lap_distance = get_x_axis_for_distance(lap)
    lap_time = lap.DataTime

    # Multiply to match datatype which is nanoseconds?
    lap_time_ms = [convert_seconds_to_milliseconds(item) for item in lap_time]

    # FIXME: What does Timedelta want for input?
    series = pd.Series(lap_distance, index=pd.TimedeltaIndex(data = lap_time_ms, unit="ms"))

    upsample = series.resample('10ms').asfreq()
    interpolated_upsample = upsample.interpolate()

    # Make distance to index and time to value, because we want to join on distance
    inverted = pd.Series(interpolated_upsample.index.values, index=interpolated_upsample)

    # Flip around, we have to convert timedelta back to integer to do this
    s1 = pd.Series(inverted.values.astype('int64'), name=name, index=inverted.index)

    df1=DataFrame(data=s1)
    # returns a dataframe where index is distance travelled and first data field is time passed
    return df1


def calculate_time_diff_by_distance(reference_lap: Lap, comparison_lap: Lap) -> DataFrame:

    df1 = get_time_delta_dataframe_for_lap(reference_lap, "reference")
    df2 = get_time_delta_dataframe_for_lap(comparison_lap, "comparison")

    df = df1.join(df2, how='outer').sort_index().interpolate()

    # After interpolation, we can make the index a normal field and rename it
    df.reset_index(inplace=True)
    df = df.rename(columns={'index': 'distance'})

    # Convert integer timestamps back to timestamp format
    s_reference_timestamped=pd.to_timedelta(getattr(df, "reference"))
    s_comparison_timestamped=pd.to_timedelta(getattr(df, "comparison"))

    df["reference"] = s_reference_timestamped
    df["comparison"] = s_comparison_timestamped

    df['timedelta'] = df["comparison"] - df["reference"]
    return df


def mark_if_matches_highest_or_lowest(value: float, highest: List[int], lowest: List[int], order: int, high_is_best=True) -> str:
    green = 32
    red = 31
    reset = 0

    high = green
    low = red

    if not high_is_best:
        low = green
        high = red

    if value == highest[order]:
        return "\x1b[1;%dm%0.f\x1b[1;%dm" % (high, value, reset)

    if value == lowest[order]:
        return "\x1b[1;%dm%0.f\x1b[1;%dm" % (low, value, reset)

    return value


def format_laps_to_table(laps: List[Lap], bestlap: int) -> str:

    highest = [0,0,0,0,0]
    lowest = [999999,999999,999999,999999,999999]

    # Display lap times
    table = []
    for idx, lap in enumerate(laps):
        lap_color = 39 # normal color
        time_diff = ""

        if bestlap == lap.LapTime:
            lap_color = 35 # magenta
        elif lap.LapTime < bestlap: # LapTime cannot be smaller than bestlap, bestlap is always the smallest. This can only mean that lap.LapTime is from an earlier race on a different track
            time_diff = "-"
        elif bestlap > 0:
            time_diff = secondsToLaptime(-1 * (bestlap / 1000 - lap.LapTime / 1000))


        ftTicks = lap.FullThrottleTicks/lap.LapTicks*1000
        tbTicks = lap.ThrottleAndBrakesTicks/lap.LapTicks*1000
        fbTicks = lap.FullBrakeTicks/lap.LapTicks*1000
        ntTicks = lap.NoThrottleNoBrakeTicks/lap.LapTicks*1000
        tiTicks =lap.TiresSpinningTicks/lap.LapTicks*1000

        listOfTicks = [ftTicks, tbTicks, fbTicks, ntTicks, tiTicks]


        for i, value in enumerate(listOfTicks):
            if listOfTicks[i] > highest[i]:
                highest[i] = listOfTicks[i]

            if listOfTicks[i] <= lowest[i]:
                lowest[i] = listOfTicks[i]


        table.append([
            # Number
            "\x1b[1;%dm%d" % (lap_color , lap.Number),
            # Timing
            secondsToLaptime(lap.LapTime / 1000),
            time_diff,
            lap.RemainingFuel,
            lap.FuelConsumed,
            # Ticks
            ftTicks,
            tbTicks,
            fbTicks,
            ntTicks,
            tiTicks
        ])

    for i, entry in enumerate(table):
        for k, val in enumerate(table[i]):
            if k == 5:
                table[i][k] = mark_if_matches_highest_or_lowest(table[i][k], highest, lowest, 0, high_is_best=True)
            elif k == 6:
                table[i][k] = mark_if_matches_highest_or_lowest(table[i][k], highest, lowest, 1, high_is_best=False)
            elif k == 7:
                table[i][k] = mark_if_matches_highest_or_lowest(table[i][k], highest, lowest, 2, high_is_best=True)
            elif k == 8:
                table[i][k] = mark_if_matches_highest_or_lowest(table[i][k], highest, lowest, 3, high_is_best=False)
            elif k == 9:
                table[i][k] = mark_if_matches_highest_or_lowest(table[i][k], highest, lowest, 4, high_is_best=False)


    return (tabulate(
        table,
        headers=["#", "Time", "Diff", "Fuel", "FuCo", "fT", "T+B", "fB", "0T", "Spin"],
        floatfmt=".0f"
    ))

def convert_seconds_to_milliseconds(seconds: int):
    minutes = seconds // 60
    remaining = seconds % 60

    return minutes * 60000 + remaining * 1000

def secondsToLaptime(seconds):
    remaining = seconds
    minutes = seconds // 60
    remaining = seconds % 60
    return '{:01.0f}:{:06.3f}'.format(minutes, remaining)

def milliseconds_to_difftime(milliseconds: int):

    if milliseconds > 0:
        prefix = "+"
    else:
        prefix = "-"
        milliseconds = milliseconds * -1


    delta = str(timedelta(milliseconds=int(milliseconds)))

    if milliseconds == 0:
        return ""

    return prefix + delta


def find_speed_peaks_and_valleys(lap: Lap, width: int = 100) -> tuple[list[int], list[int]]:
    inv_data_speed = [i*-1 for i in lap.DataSpeed]
    peaks, whatisthis = find_peaks(lap.DataSpeed, width=width)
    valleys, whatisthis = find_peaks(inv_data_speed, width=width)
    return list(peaks), list(valleys)


def get_speed_peaks_and_valleys(lap: Lap):
    peaks, valleys = find_speed_peaks_and_valleys(lap, width=100)

    peak_speed_data_x = []
    peak_speed_data_y = []

    valley_speed_data_x = []
    valley_speed_data_y = []

    for p in peaks:
        peak_speed_data_x.append(lap.DataSpeed[p])
        peak_speed_data_y.append(p)

    for v in valleys:
        valley_speed_data_x.append(lap.DataSpeed[v])
        valley_speed_data_y.append(v)

    return peak_speed_data_x, peak_speed_data_y, valley_speed_data_x, valley_speed_data_y

def none_ignoring_median(data):
    """Return the median (middle value) of numeric data but ignore None values.

    When the number of data points is odd, return the middle data point.
    When the number of data points is even, the median is interpolated by
    taking the average of the two middle values:

    >>> median([1, 3, None, 5])
    3
    >>> median([1, 3, 5, None, 7])
    4.0

    """
    # FIXME improve me
    filtered_data = []
    for d in data:
        if d is not None:
            filtered_data.append(d)
    filtered_data = sorted(filtered_data)
    n = len(filtered_data)
    if n == 0:
        raise StatisticsError("no median for empty data")
    if n % 2 == 1:
        return filtered_data[n // 2]
    else:
        i = n // 2
        return (filtered_data[i - 1] + filtered_data[i]) / 2

class LapFile:
    def __init__(self):
        self.name = None
        self.path = None
        self.size = None

    def __str__(self):
        return "%s - %s" % (self.name, human_readable_size(self.size, decimal_places=0))

def list_lap_files_from_path(root: str):
    lap_files = []
    for path, subdirs, files in os.walk(root):
        for name in files:
            lf = LapFile()
            lf.name = name
            lf.path = os.path.join(path, name)
            lf.size = os.path.getsize(lf.path)
            lap_files.append(lf)

    return lap_files

def load_laps_from_pickle(path: str) -> List[Lap]:
    with open(path, 'rb') as f:
        return pickle.load(f)

def save_laps_to_pickle(laps: List[Lap]) -> str:

    storage_folder = "data"
    LOCAL_TIMEZONE = datetime.now(timezone.utc).astimezone().tzinfo
    dt = datetime.now(tz=LOCAL_TIMEZONE)
    str_date_time = dt.strftime("%d-%m-%Y_%H:%M:%S")
    print("Current timestamp", str_date_time)
    storage_filename = "laps_%s.pickle" % str_date_time
    Path(storage_folder).mkdir(parents=True, exist_ok=True)

    path = storage_folder+"/"+storage_filename

    with open(path, 'wb') as f:
        pickle.dump(laps, f)

    return path

def human_readable_size(size, decimal_places=3):
    for unit in ['B','KB','MB','GB','TB']:
        if size < 1024.0:
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f} {unit}"
