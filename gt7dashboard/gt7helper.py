import csv
import itertools
import logging
import os
import pickle
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import StatisticsError
from typing import Tuple, List

import pandas as pd
from pandas import DataFrame
from scipy.signal import find_peaks
from tabulate import tabulate

from gt7dashboard.gt7lap import Lap
from gt7dashboard import gt7helper


def save_laps(laps: List[Lap]):
    path = os.path.join(os.getcwd(), 'data', 'all_laps.pickle')
    with open(path, "wb") as f:
        pickle.dump(laps, f)


def calculate_remaining_fuel(
        fuel_start_lap: int, fuel_end_lap: int, lap_time: int
) -> Tuple[int, float, float]:
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
    tick_time = 16.668  # https://www.gtplanet.net/forum/threads/gt7-is-compatible-with-motion-rig.410728/post-13806131
    for i, s in enumerate(lap.data_speed):
        # distance traveled + (Speed in km/h / 3.6 / 1000 = mm / ms) * tick_time
        if i == 0:
            x_axis.append(0)
            continue

        x_axis.append(x_axis[i - 1] + (lap.data_speed[i] / 3.6 / 1000) * tick_time)

    return x_axis


def get_x_axis_depending_on_mode(lap: Lap, distance_mode: bool):
    if distance_mode:
        # Calculate distance for x axis
        return get_x_axis_for_distance(lap)
    else:
        # Use ticks as length, which is the length of any given data list
        return list(range(len(lap.data_speed)))
    pass


def get_time_delta_dataframe_for_lap(lap: Lap, name: str) -> DataFrame:
    lap_distance = get_x_axis_for_distance(lap)
    lap_time = lap.data_time

    # Multiply to match datatype which is nanoseconds?
    lap_time_ms = [convert_seconds_to_milliseconds(item) for item in lap_time]

    series = pd.Series(
        lap_distance, index=pd.TimedeltaIndex(data=lap_time_ms, unit="ms")
    )

    upsample = series.resample("10ms").asfreq()
    interpolated_upsample = upsample.interpolate()

    # Make distance to index and time to value, because we want to join on distance
    inverted = pd.Series(
        interpolated_upsample.index.values, index=interpolated_upsample
    )

    # Flip around, we have to convert timedelta back to integer to do this
    s1 = pd.Series(inverted.values.astype("int64"), name=name, index=inverted.index)

    df1 = DataFrame(data=s1)
    # returns a dataframe where index is distance travelled and first data field is time passed
    return df1


def calculate_time_diff_by_distance(
        reference_lap: Lap, comparison_lap: Lap
) -> DataFrame:
    df1 = get_time_delta_dataframe_for_lap(reference_lap, "reference")
    df2 = get_time_delta_dataframe_for_lap(comparison_lap, "comparison")

    df = df1.join(df2, how="outer").sort_index().interpolate()

    # After interpolation, we can make the index a normal field and rename it
    df.reset_index(inplace=True)
    df = df.rename(columns={"index": "distance"})

    # Convert integer timestamps back to timestamp format
    s_reference_timestamped = pd.to_timedelta(getattr(df, "reference"))
    s_comparison_timestamped = pd.to_timedelta(getattr(df, "comparison"))

    df["reference"] = s_reference_timestamped
    df["comparison"] = s_comparison_timestamped

    df["timedelta"] = df["comparison"] - df["reference"]
    return df


def mark_if_matches_highest_or_lowest(
        value: float, highest: List[int], lowest: List[int], order: int, high_is_best=True
) -> str:
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

    return "%0.f" % value


def format_laps_to_table(laps: List[Lap], best_lap: float) -> str:
    highest = [0, 0, 0, 0, 0]
    lowest = [999999, 999999, 999999, 999999, 999999]

    # Display lap times
    table = []
    for idx, lap in enumerate(laps):
        lap_color = 39  # normal color
        time_diff = ""

        if best_lap == lap.lap_finish_time:
            lap_color = 35  # magenta
        elif lap.lap_finish_time < best_lap:
            # lap_finish_time cannot be smaller than best_lap, best_lap is always the smallest.
            # This can only mean that lap.lap_finish_time is from an earlier race on a different track
            time_diff = "-"
        elif best_lap > 0:
            time_diff = seconds_to_lap_time(-1 * (best_lap / 1000 - lap.lap_finish_time / 1000))

        ft_ticks = lap.full_throttle_ticks / lap.lap_ticks * 1000
        tb_ticks = lap.throttle_and_brake_ticks / lap.lap_ticks * 1000
        fb_ticks = lap.full_brake_ticks / lap.lap_ticks * 1000
        nt_ticks = lap.no_throttle_and_no_brake_ticks / lap.lap_ticks * 1000
        ti_ticks = lap.tires_spinning_ticks / lap.lap_ticks * 1000

        list_of_ticks = [ft_ticks, tb_ticks, fb_ticks, nt_ticks, ti_ticks]

        for i, value in enumerate(list_of_ticks):
            if list_of_ticks[i] > highest[i]:
                highest[i] = list_of_ticks[i]

            if list_of_ticks[i] <= lowest[i]:
                lowest[i] = list_of_ticks[i]

        table.append(
            [
                # number
                "\x1b[1;%dm%d" % (lap_color, lap.number),
                # Timing
                seconds_to_lap_time(lap.lap_finish_time / 1000),
                time_diff,
                lap.fuel_at_end,
                lap.fuel_consumed,
                # Ticks
                ft_ticks,
                tb_ticks,
                fb_ticks,
                nt_ticks,
                ti_ticks,
            ]
        )

    for i, entry in enumerate(table):
        for k, val in enumerate(table[i]):
            if k == 5:
                table[i][k] = mark_if_matches_highest_or_lowest(
                    table[i][k], highest, lowest, 0, high_is_best=True
                )
            elif k == 6:
                table[i][k] = mark_if_matches_highest_or_lowest(
                    table[i][k], highest, lowest, 1, high_is_best=False
                )
            elif k == 7:
                table[i][k] = mark_if_matches_highest_or_lowest(
                    table[i][k], highest, lowest, 2, high_is_best=True
                )
            elif k == 8:
                table[i][k] = mark_if_matches_highest_or_lowest(
                    table[i][k], highest, lowest, 3, high_is_best=False
                )
            elif k == 9:
                table[i][k] = mark_if_matches_highest_or_lowest(
                    table[i][k], highest, lowest, 4, high_is_best=False
                )

    return tabulate(
        table,
        headers=["#", "Time", "Diff", "Fuel", "FuCo", "fT", "T+B", "fB", "0T", "Spin"],
        floatfmt=".0f",
    )


def convert_seconds_to_milliseconds(seconds: int):
    minutes = seconds // 60
    remaining = seconds % 60

    return minutes * 60000 + remaining * 1000


def seconds_to_lap_time(seconds):
    prefix = ""
    if seconds < 0:
        prefix = "-"
        seconds *= -1

    minutes = seconds // 60
    remaining = seconds % 60
    return prefix + "{:01.0f}:{:06.3f}".format(minutes, remaining)


def find_speed_peaks_and_valleys(
        lap: Lap, width: int = 100
) -> tuple[list[int], list[int]]:
    inv_data_speed = [i * -1 for i in lap.data_speed]
    peaks, whatisthis = find_peaks(lap.data_speed, width=width)
    valleys, whatisthis = find_peaks(inv_data_speed, width=width)
    return list(peaks), list(valleys)


def get_speed_peaks_and_valleys(lap: Lap):
    peaks, valleys = find_speed_peaks_and_valleys(lap, width=100)

    peak_speed_data_x = []
    peak_speed_data_y = []

    valley_speed_data_x = []
    valley_speed_data_y = []

    for p in peaks:
        peak_speed_data_x.append(lap.data_speed[p])
        peak_speed_data_y.append(p)

    for v in valleys:
        valley_speed_data_x.append(lap.data_speed[v])
        valley_speed_data_y.append(v)

    return (
        peak_speed_data_x,
        peak_speed_data_y,
        valley_speed_data_x,
        valley_speed_data_y,
    )


def none_ignoring_median(data):
    """Return the median (middle value) of numeric data but ignore None values.

    When the number of data points is odd, return the middle data point.
    When the number of data points is even, the median is interpolated by
    taking the average of the two middle values:

    >>> none_ignoring_median([1, 3, None, 5])
    3
    >>> none_ignoring_median([1, 3, 5, None, 7])
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
    for path, sub_dirs, files in os.walk(root):
        for name in files:
            if name.endswith(".laps"):
                lf = LapFile()
                lf.name = name
                lf.path = os.path.join(path, name)
                lf.size = os.path.getsize(lf.path)
                lap_files.append(lf)

    lap_files.sort(key=lambda x: x.path, reverse=True)
    return lap_files


def load_laps_from_pickle(path: str) -> List[Lap]:
    with open(path, "rb") as f:
        return pickle.load(f)


def save_laps_to_pickle(laps: List[Lap]) -> str:
    storage_folder = "data"
    local_timezone = datetime.now(timezone.utc).astimezone().tzinfo
    dt = datetime.now(tz=local_timezone)
    str_date_time = dt.strftime("%Y-%m-%d_%H_%M_%S")
    storage_filename = "%s_%s.laps" % (str_date_time, get_safe_filename(laps[0].car_name()))
    Path(storage_folder).mkdir(parents=True, exist_ok=True)

    path = os.path.join(os.getcwd(), storage_folder, storage_filename)

    with open(path, "wb") as f:
        pickle.dump(laps, f)

    return path


def get_safe_filename(unsafe_filename: str) -> str:
    return "".join(x for x in unsafe_filename if x.isalnum() or x in "._- ").replace(" ", "_")


def human_readable_size(size, decimal_places=3):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f} {unit}"


def get_last_reference_median_lap(
        laps: List[Lap], reference_lap_selected: Lap
) -> Tuple[Lap, Lap, Lap]:
    last_lap = None
    reference_lap = None
    median_lap = None

    if len(laps) > 0:  # Only show last lap
        last_lap = laps[0]

    if len(laps) >= 2 and not reference_lap_selected:
        reference_lap = get_best_lap(laps)

    if len(laps) >= 3:
        median_lap = get_median_lap(laps)

    if reference_lap_selected:
        reference_lap = reference_lap_selected

    return last_lap, reference_lap, median_lap


def get_best_lap(laps: List[Lap]):
    if len(laps) == 0:
        return None

    return sorted(laps, key=lambda x: x.lap_finish_time, reverse=False)[0]


def get_median_lap(laps: List[Lap]) -> Lap:
    if len(laps) == 0:
        raise Exception("Lap list does not contain any laps")

    # Filter out too long laps, like box laps etc. use 10 Seconds of the best lap as a threshold
    best_lap = get_best_lap(laps)
    ten_seconds = 10000
    laps = filter_max_min_laps(
        laps, best_lap.lap_finish_time + ten_seconds, best_lap.lap_finish_time - ten_seconds
    )

    median_lap = Lap()
    if len(laps) == 0:
        return median_lap

    for val in vars(laps[0]):
        attributes = []
        for lap in laps:
            if val == "options":
                continue
            attr = getattr(lap, val)
            # FIXME why is it sometimes string AND int?
            if not isinstance(attr, str) and attr != "" and attr != []:
                attributes.append(getattr(lap, val))
        if len(attributes) == 0:
            continue
        if isinstance(getattr(laps[0], val), list):
            median_attribute = [
                none_ignoring_median(k)
                for k in itertools.zip_longest(*attributes, fillvalue=None)
            ]
        else:
            median_attribute = statistics.median(attributes)
        setattr(median_lap, val, median_attribute)

    median_lap.title = "Median (%d Laps): %s" % (
        len(laps),
        seconds_to_lap_time(median_lap.lap_finish_time / 1000),
    )

    return median_lap


def get_brake_points(lap):
    x = []
    y = []
    for i, b in enumerate(lap.data_braking):
        if i > 0:
            if lap.data_braking[i - 1] == 0 and lap.data_braking[i] > 0:
                x.append(lap.data_position_x[i])
                y.append(lap.data_position_z[i])

    return x, y


def filter_max_min_laps(laps: List[Lap], max_lap_time=-1, min_lap_time=-1) -> List[Lap]:
    if max_lap_time > 0:
        laps = list(filter(lambda l: l.lap_finish_time <= max_lap_time, laps))

    if min_lap_time > 0:
        laps = list(filter(lambda l: l.lap_finish_time >= min_lap_time, laps))

    return laps


def pd_data_frame_from_lap(
        laps: List[Lap], best_lap_time: int
) -> pd.DataFrame:
    df = pd.DataFrame()
    for i, lap in enumerate(laps):
        time_diff = ""
        if best_lap_time == lap.lap_finish_time:
            # lap_color = 35 # magenta
            # TODO add some formatting
            pass
        elif lap.lap_finish_time < best_lap_time:
            # lap_finish_time cannot be smaller than best_lap, best_lap is always the smallest.
            # This can only mean that lap.lap_finish_time is from an earlier race on a different track
            time_diff = "-"
        elif best_lap_time > 0:
            time_diff = seconds_to_lap_time(
                -1 * (best_lap_time / 1000 - lap.lap_finish_time / 1000)
            )

        df_add = pd.DataFrame(
            [
                {
                    "number": lap.number,
                    "time": seconds_to_lap_time(lap.lap_finish_time / 1000),
                    "diff": time_diff,
                    "car_name": lap.car_name(),
                    "fuelconsumed": "%d" % lap.fuel_consumed,
                    "fullthrottle": "%d"
                                    % (lap.full_throttle_ticks / lap.lap_ticks * 1000),
                    "throttleandbreak": "%d"
                                        % (lap.throttle_and_brake_ticks / lap.lap_ticks * 1000),
                    "fullbreak": "%d" % (lap.full_brake_ticks / lap.lap_ticks * 1000),
                    "nothrottle": "%d"
                                  % (lap.no_throttle_and_no_brake_ticks / lap.lap_ticks * 1000),
                    "tyrespinning": "%d"
                                    % (lap.tires_spinning_ticks / lap.lap_ticks * 1000),
                }
            ],
            index=[i],
        )
        df = pd.concat([df, df_add])

    return df


RACE_LINE_BRAKING_MODE = "RACE_LINE_BRAKING_MODE"
RACE_LINE_THROTTLE_MODE = "RACE_LINE_THROTTLE_MODE"
RACE_LINE_COASTING_MODE = "RACE_LINE_COASTING_MODE"


def get_race_line_coordinates_when_mode_is_active(lap: Lap, mode: str):
    return_y = []
    return_x = []
    return_z = []

    for i, _ in enumerate(lap.data_braking):

        if mode == RACE_LINE_BRAKING_MODE:

            if lap.data_braking[i] > lap.data_throttle[i]:
                return_y.append(lap.data_position_y[i])
                return_x.append(lap.data_position_x[i])
                return_z.append(lap.data_position_z[i])
            else:
                return_y.append("NaN")
                return_x.append("NaN")
                return_z.append("NaN")

        elif mode == RACE_LINE_THROTTLE_MODE:

            if lap.data_braking[i] < lap.data_throttle[i]:
                return_y.append(lap.data_position_y[i])
                return_x.append(lap.data_position_x[i])
                return_z.append(lap.data_position_z[i])
            else:
                return_y.append("NaN")
                return_x.append("NaN")
                return_z.append("NaN")

        if mode == RACE_LINE_COASTING_MODE:

            if lap.data_braking[i] == 0 and lap.data_throttle[i] == 0:
                return_y.append(lap.data_position_y[i])
                return_x.append(lap.data_position_x[i])
                return_z.append(lap.data_position_z[i])
            else:
                return_y.append("NaN")
                return_x.append("NaN")
                return_z.append("NaN")

    return return_y, return_x, return_z


CARS_CSV_FILENAME = "db/cars.csv"


def get_car_name_for_car_id(car_id: int) -> str:
    # check if variable is int
    if not isinstance(car_id, int):
        raise ValueError("car_id must be an integer")

    # check if file exists
    if not os.path.isfile(CARS_CSV_FILENAME):
        logging.info("Could not find file %s" % CARS_CSV_FILENAME)
        return "CAR-ID-%d" % car_id

    # read csv from file
    with open(CARS_CSV_FILENAME, 'r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            if row[0] == str(car_id):
                return row[1]

    return ""


def bokeh_tuple_for_list_of_lapfiles(lapfiles: List[LapFile]):
    tuples = [""]  # Use empty first option which is default
    for lapfile in lapfiles:
        tuples.append(tuple((lapfile.path, lapfile.__str__())))
    return tuples


def bokeh_tuple_for_list_of_laps(laps: List[Lap]):
    tuples = []
    for i, lap in enumerate(laps):
        tuples.append(tuple((str(i), lap.format())))
    return tuples


class FuelMap:
    """A Fuel Map with calculated attributes of the fuel setting

    Attributes:
            fuel_consumed_per_lap   The amount of fuel consumed per lap with this fuel map
    """

    def __init__(self, mixture_setting, power_percentage, consumption_percentage):
        """
        Create a Fuel Map that is relative to the base setting

        :param mixture_setting: Mixture Setting of the Fuel Map
        :param power_percentage: Percentage of available power to the car relative to the base setting
        :param consumption_percentage: Percentage of fuel consumption relative to the base setting
        """
        self.mixture_setting = mixture_setting
        self.power_percentage = power_percentage
        self.consumption_percentage = consumption_percentage

        self.fuel_consumed_per_lap = 0
        self.laps_remaining_on_current_fuel = 0
        self.time_remaining_on_current_fuel = 0
        self.lap_time_diff = 0
        self.lap_time_expected = 0

    def __str__(self):
        return "%d\t\t %d%%\t\t\t %d%%\t%d\t%.1f\t%s\t%s" % (
            self.mixture_setting,
            self.power_percentage * 100,
            self.consumption_percentage * 100,
            self.fuel_consumed_per_lap,
            self.laps_remaining_on_current_fuel,
            seconds_to_lap_time(self.time_remaining_on_current_fuel / 1000),
            seconds_to_lap_time(self.lap_time_diff / 1000),
        )


def get_fuel_on_consumption_by_relative_fuel_levels(lap: Lap) -> List[FuelMap]:
    # Relative Setting, Laps to Go, Time to Go, Assumed Diff in Lap Times
    fuel_consumed_per_lap, laps_remaining, time_remaining = calculate_remaining_fuel(
        lap.fuel_at_start, lap.fuel_at_end, lap.lap_finish_time
    )
    i = -5

    # Source:
    # https://www.gtplanet.net/forum/threads/test-results-fuel-mixture-settings-and-other-fuel-saving-techniques.369387/
    fuel_consumption_per_level_change = 8
    power_per_level_change = 4

    relative_fuel_maps = []

    while i <= 5:
        relative_fuel_map = FuelMap(
            mixture_setting=i,
            power_percentage=(100 - i * power_per_level_change) / 100,
            consumption_percentage=(100 - i * fuel_consumption_per_level_change) / 100,
        )

        relative_fuel_map.fuel_consumed_per_lap = fuel_consumed_per_lap * relative_fuel_map.consumption_percentage
        relative_fuel_map.laps_remaining_on_current_fuel = laps_remaining + laps_remaining * (
                1 - relative_fuel_map.consumption_percentage
        )

        relative_fuel_map.time_remaining_on_current_fuel = time_remaining + time_remaining * (
                1 - relative_fuel_map.consumption_percentage
        )
        relative_fuel_map.lap_time_diff = lap.lap_finish_time * (1 - relative_fuel_map.power_percentage)
        relative_fuel_map.lap_time_expected = lap.lap_finish_time + relative_fuel_map.lap_time_diff

        relative_fuel_maps.append(relative_fuel_map)
        i += 1

    return relative_fuel_maps


def get_n_fastest_laps_within_percent_threshold_ignoring_replays(laps: List[Lap], number_of_laps: int,
                                                                 percent_threshold: float):
    # FIXME Replace later with this line
    # filtered_laps = [lap for lap in laps if not lap.is_replay]
    filtered_laps = [lap for lap in laps if not (len(lap.data_speed) == 0 or lap.is_replay)]

    if len(filtered_laps) == 0:
        return []

    # sort laps by finish time
    filtered_laps.sort(key=lambda lap: lap.lap_finish_time)
    fastest_lap = filtered_laps[0]
    threshold_laps = [lap for lap in filtered_laps if
                      lap.lap_finish_time <= fastest_lap.lap_finish_time * (1 + percent_threshold)]
    return threshold_laps[:number_of_laps]


DEFAULT_FASTEST_LAPS_PERCENT_THRESHOLD = 0.05
def get_variance_for_fastest_laps(laps: List[Lap], number_of_laps: int = 3, percent_threshold: float = DEFAULT_FASTEST_LAPS_PERCENT_THRESHOLD) -> (DataFrame, list[Lap]):
    fastest_laps: list[Lap] = get_n_fastest_laps_within_percent_threshold_ignoring_replays(laps, number_of_laps, percent_threshold)
    variance: DataFrame = get_variance_for_laps(fastest_laps)
    return variance, fastest_laps


def get_variance_for_laps(laps: List[Lap]) -> DataFrame:

    dataframe_distance_columns = []
    merged_df = pd.DataFrame(columns=['distance'])
    for lap in laps:
        d = {'speed': lap.data_speed, 'distance' : gt7helper.get_x_axis_for_distance(lap)}
        df = pd.DataFrame(data=d)
        dataframe_distance_columns.append(df)
        merged_df = pd.merge(merged_df, df, on='distance', how='outer')

    merged_df = merged_df.sort_values(by='distance')
    merged_df = merged_df.set_index('distance')

    # Interpolate missing values
    merged_df = merged_df.interpolate()
    dbs_df = merged_df.std(axis=1).abs()
    dbs_df = dbs_df.reset_index().rename(columns={'index': 'distance'})
    dbs_df.columns = ["distance", "speed_variance"]

    return dbs_df
