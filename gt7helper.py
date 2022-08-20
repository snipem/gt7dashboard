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

def calculate_time_diff_by_distance(best_lap_distance: List[int], best_lap_time: List[int], second_best_lap_distance: List[int], second_best_lap_time: List[int]) -> DataFrame:
    second_best_lap_time_ns = [item * 1000000 for item in second_best_lap_time]
    best_lap_time_ns = [item * 1000000 for item in best_lap_time]

    best_series = pd.Series(best_lap_distance, index=pd.TimedeltaIndex(data = best_lap_time_ns))
    second_best_series = pd.Series(second_best_lap_distance, index=pd.TimedeltaIndex(data = second_best_lap_time_ns))

    # interpolated_x, interpolated_y = interpolate_missing_values(best_lap_time, best_lap_distance, interpolation_step=1)
    best_upsample = best_series.resample('1ms').asfreq()
    best_interpolated_upsample = best_upsample.interpolate()

    second_best_upsample = second_best_series.resample('1ms').asfreq()
    second_best_interpolated_upsample = second_best_upsample.interpolate()

    inverted_best = pd.Series(best_interpolated_upsample.index.values, index=best_interpolated_upsample )
    inverted_second_best = pd.Series(second_best_interpolated_upsample.index.values, index=second_best_interpolated_upsample )

    df=pd.concat([
        pd.Series(inverted_best.values.astype('int64'), index=inverted_best.index), # convert to integer to interpolete timestamps
        pd.Series(inverted_second_best.values.astype('int64'), index=inverted_second_best.index) # convert to integer to interpolete timestamps
    ],axis=1).sort_index().interpolate()

    df['timedelta'] = df[0] - df[1]
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
