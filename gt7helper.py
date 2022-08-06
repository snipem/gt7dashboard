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
    lowest = [0,0,0,0,0]

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
                highest[i] = value

            if listOfTicks[i] < lowest[i]:
                lowest[i] = value


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
