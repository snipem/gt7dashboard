from datetime import timedelta
from typing import Tuple, List

from tabulate import tabulate

from gt7lap import Lap


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

def format_laps_to_table(laps: List[Lap], bestlap: int) -> str:
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

        table.append([
            # Number
            "\x1b[1;%dm%d" % (lap_color , lap.Number),
            # Timing
            secondsToLaptime(lap.LapTime / 1000),
            time_diff,
            lap.RemainingFuel,
            # Ticks
            lap.FullThrottleTicks/lap.LapTicks*1000,
            lap.ThrottleAndBrakesTicks/lap.LapTicks*1000,
            lap.FullBrakeTicks/lap.LapTicks*1000,
            lap.NoThrottleNoBrakeTicks/lap.LapTicks*1000,
            lap.TiresSpinningTicks/lap.LapTicks*1000
        ])

    return (tabulate(
        table,
        headers=["#", "Time", "Diff", "Fuel", "fT", "T+B", "fB", "0T", "Spin"],
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
