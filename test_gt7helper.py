import unittest
from statistics import StatisticsError

import pandas as pd

import gt7helper
from gt7helper import calculate_remaining_fuel, format_laps_to_table, milliseconds_to_difftime, \
    calculate_time_diff_by_distance
from gt7lap import Lap


class GTHelper(unittest.TestCase):
    def test_calculate_remaining_fuel(self):
        fuel_consumed_per_lap, laps_remaining, time_remaining = calculate_remaining_fuel(100, 80, 10000)
        self.assertEqual(fuel_consumed_per_lap, 20)
        self.assertEqual(laps_remaining, 4)
        self.assertEqual(time_remaining, 40000)

        fuel_consumed_per_lap, laps_remaining, time_remaining = calculate_remaining_fuel(20, 5, 100)
        self.assertEqual(fuel_consumed_per_lap, 15)
        self.assertLess(laps_remaining, 1)
        self.assertLess(time_remaining, 34)

        fuel_consumed_per_lap, laps_remaining, time_remaining = calculate_remaining_fuel(100, 100, 10000)
        self.assertEqual(fuel_consumed_per_lap, 0)
        self.assertEqual(laps_remaining, -1)
        self.assertEqual(time_remaining, -1)

    def test_format_laps_to_table(self):
        lap1 = Lap()
        lap1.Number = 1
        lap1.LapTime = 11311000 / 1000
        lap1.RemainingFuel = 90
        lap1.FullThrottleTicks = 10000
        lap1.ThrottleAndBrakesTicks = 500
        lap1.FullBrakeTicks = 10000
        lap1.NoThrottleNoBrakeTicks = 50
        lap1.LapTicks = 33333
        lap1.TiresSpinningTicks = 260

        lap2 = Lap()
        lap2.Number = 2
        lap2.LapTime = 11110000 / 1000
        lap2.RemainingFuel = 44
        lap2.FullThrottleTicks = 100
        lap2.ThrottleAndBrakesTicks = 750
        lap2.FullBrakeTicks = 1000
        lap2.NoThrottleNoBrakeTicks = 40
        lap2.LapTicks = 33333
        lap2.TiresSpinningTicks = 240

        lap3 = Lap()
        lap3.Number = 3
        lap3.LapTime = 12114000 / 1000
        lap3.RemainingFuel = 34
        lap3.FullThrottleTicks = 100
        lap3.ThrottleAndBrakesTicks = 10
        lap3.FullBrakeTicks = 1000
        lap3.NoThrottleNoBrakeTicks = 100
        lap3.LapTicks = 33333
        lap3.TiresSpinningTicks = 120

        laps = [lap3, lap2, lap1]

        result = format_laps_to_table(laps, 11110000 / 1000)
        print("\n")
        print(result)
        self.assertEqual(len(result.split("\n")), len(laps) + 2)  # +2 for header and last line

    def test_seconds_to_difftime(self):
        self.assertEqual('+0:16:40', milliseconds_to_difftime(500))
        self.assertEqual('', milliseconds_to_difftime(0))
        self.assertEqual('-1:40.000', milliseconds_to_difftime(-102))

    def test_calculate_time_diff_by_distance_from_pickle(self):
        laps = gt7helper.load_laps_from_pickle("data/laps_20-08-2022_21:46:22.pickle")

        df = calculate_time_diff_by_distance(laps[1], laps[2])

        print(len(df))

    def test_calculate_time_diff_by_distance(self):
        best_lap = Lap()
        best_lap.DataTime = [0, 2, 6, 12, 22, 45, 60, 70]
        best_lap.DataSpeed = [0, 50, 55, 100, 120, 30, 20, 50]

        second_best_lap = Lap()
        second_best_lap.DataTime = [0, 1, 4, 5, 20, 30, 70, 75]
        second_best_lap.DataSpeed = [0, 40, 35, 90, 85, 50, 20, 5]

        df = calculate_time_diff_by_distance(best_lap, second_best_lap)

        print(len(df))


    def test_convert_seconds_to_milliseconds(self):
        seconds = 10000
        ms = gt7helper.convert_seconds_to_milliseconds(seconds)
        s_s = gt7helper.secondsToLaptime(seconds / 1000)
        print(ms, s_s)

    def test_get_last_reference_median_lap(self):
        gt7helper.get_last_reference_median_lap(laps, None)
