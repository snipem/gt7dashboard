import unittest
from statistics import StatisticsError

from gt7helper import calculate_remaining_fuel, format_laps_to_table, milliseconds_to_difftime
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
