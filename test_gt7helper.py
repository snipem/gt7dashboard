import pickle
import unittest

import gt7helper
from gt7helper import calculate_remaining_fuel, format_laps_to_table, calculate_time_diff_by_distance
from gt7lap import Lap


class TestHelper(unittest.TestCase):
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

    def test_get_fuel_on_consumption_by_relative_fuel_levels(self):
        fuel_lap = Lap()
        fuel_lap.FuelAtStart = 100
        fuel_lap.FuelAtEnd = 50
        fuel_lap.LapTime = 1000
        fuel_maps = gt7helper.get_fuel_on_consumption_by_relative_fuel_levels(fuel_lap)
        self.assertEqual(11, len(fuel_maps))
        print("\nFuelLvl	 Power%		    Fuel% Consum. LapsRem 	Time Rem Exp. Lap Time\n")
        for fuel_map in fuel_maps:
            print(fuel_map)

    def test_format_laps_to_table(self):
        lap1 = Lap()
        lap1.Number = 1
        lap1.LapTime = 11311000 / 1000
        lap1.FuelAtEnd = 90
        lap1.FullThrottleTicks = 10000
        lap1.ThrottleAndBrakesTicks = 500
        lap1.FullBrakeTicks = 10000
        lap1.NoThrottleNoBrakeTicks = 50
        lap1.LapTicks = 33333
        lap1.TiresSpinningTicks = 260

        lap2 = Lap()
        lap2.Number = 2
        lap2.LapTime = 11110000 / 1000
        lap2.FuelAtEnd = 44
        lap2.FullThrottleTicks = 100
        lap2.ThrottleAndBrakesTicks = 750
        lap2.FullBrakeTicks = 1000
        lap2.NoThrottleNoBrakeTicks = 40
        lap2.LapTicks = 33333
        lap2.TiresSpinningTicks = 240

        lap3 = Lap()
        lap3.Number = 3
        lap3.LapTime = 12114000 / 1000
        lap3.FuelAtEnd = 34
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

    def test_calculate_time_diff_by_distance_from_pickle(self):
        laps = gt7helper.load_laps_from_pickle("test_data/time_diff.pickle")

        df = calculate_time_diff_by_distance(laps[1], laps[2])

        # Check for common length but also for columns to exist
        self.assertEqual(len(df.distance), len(df.comparison))
        self.assertEqual(len(df.distance), len(df.reference))

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
        s_s = gt7helper.seconds_to_laptime(seconds / 1000)
        print(ms, s_s)


class TestLastReferenceMedian(unittest.TestCase):

    def setUp(self):
        self.l_fast = Lap()
        self.l_fast.LapTime = 100
        self.l_fast.DataSpeed = [200]

        self.l_middle = Lap()
        self.l_middle.LapTime = 200
        self.l_middle.DataSpeed = [150]

        self.l_slow = Lap()
        self.l_slow.LapTime = 300
        self.l_slow.DataSpeed = [100]

        self.l_reference = Lap()
        self.l_reference.LapTime = 90
        self.l_reference.DataSpeed = [300]

    def test_one_lap(self):
        last, reference, median = gt7helper.get_last_reference_median_lap([self.l_slow], None)
        self.assertEqual(self.l_slow, last)
        self.assertIsNone(reference)
        self.assertIsNone(median)

    def test_one_lap_with_reference(self):
        last, reference, median = gt7helper.get_last_reference_median_lap([self.l_fast], self.l_reference)
        self.assertEqual(self.l_fast, last)
        self.assertEqual(self.l_reference, reference)
        self.assertIsNone(median)

    def test_two_laps(self):
        last, reference, median = gt7helper.get_last_reference_median_lap([self.l_slow, self.l_fast], None)
        self.assertEqual(self.l_slow, last)
        self.assertEqual(self.l_fast, reference)
        self.assertIsNone(median, Lap)

    def test_two_laps_with_reference(self):
        last, reference, median = gt7helper.get_last_reference_median_lap([self.l_slow, self.l_fast], self.l_reference)
        self.assertEqual(self.l_slow, last)
        self.assertEqual(self.l_reference, reference)
        self.assertIsNone(median, Lap)

    def test_three_laps(self):
        last, reference, median = gt7helper.get_last_reference_median_lap([self.l_slow, self.l_fast, self.l_middle],
                                                                          None)
        self.assertEqual(self.l_slow, last)
        self.assertEqual(self.l_fast, reference)
        self.assertIsInstance(median, Lap)

    def test_two_three_with_reference(self):
        last, reference, median = gt7helper.get_last_reference_median_lap([self.l_slow, self.l_fast, self.l_middle],
                                                                          self.l_reference)
        self.assertEqual(self.l_slow, last)
        self.assertEqual(self.l_reference, reference)
        self.assertIsInstance(median, Lap)

    def test_fastest_is_latest(self):
        last, reference, median = gt7helper.get_last_reference_median_lap([self.l_fast, self.l_slow, self.l_middle],
                                                                          None)
        self.assertEqual(self.l_fast, last)
        self.assertEqual(self.l_fast, reference)
        self.assertIsInstance(median, Lap)

    def test_reference_slower_than_latest(self):
        last, reference, median = gt7helper.get_last_reference_median_lap(
            [self.l_reference, self.l_slow, self.l_middle], self.l_fast)
        self.assertEqual(self.l_reference, last)
        self.assertEqual(self.l_fast, reference)
        self.assertIsInstance(median, Lap)


class TestLaps(unittest.TestCase):
    def setUp(self):
        # Single Lap
        self.Lap = Lap()  # P1            #P2
        self.Lap.PositionsZ = [0, 1, 3, 4, 7, 8, 9]  # Brake points are stored for x,y in z,x
        self.Lap.PositionsX = [0, 2, 5, 8, 9, 18, 19]

        self.Lap.DataBraking = [0, 50, 40, 50, 0, 10, 0]

        # Set of Laps
        self.Laps = [Lap(), Lap(), Lap(), Lap()]
        self.Laps[0].LapTime = 1000
        self.Laps[1].LapTime = 1200
        self.Laps[2].LapTime = 1250
        self.Laps[3].LapTime = 1250

        self.Laps[0].DataThrottle = [0, 50, 75, 100, 100, 100, 55, 0]
        self.Laps[1].DataThrottle = [0, 25, 75, 98, 100, 0, 0, 0]

        self.Laps[0].DataBraking = [2, 4, 0, -75, 10]  # has one more than the others
        self.Laps[1].DataBraking = [4, 8, 0, -25, 10]  # has one more than the others
        self.Laps[2].DataBraking = [8, 16, 0, -10]
        self.Laps[3].DataBraking = [100, 100, 0, -20]

    def test_list_eq(self):
        """Will fail"""
        brake_points_x, brake_points_y = gt7helper.get_brake_points(self.Lap)
        # A break point will be the point after a zero for breaking
        self.assertListEqual(brake_points_x, [1, 8])
        self.assertListEqual(brake_points_y, [2, 18])

    def test_get_median_lap(self):
        median_lap = gt7helper.get_median_lap(self.Laps)
        self.assertEqual(len(median_lap.DataThrottle), len(self.Laps[0].DataThrottle))
        self.assertEqual(1225, median_lap.LapTime)
        self.assertListEqual([0, 37.5, 75, 99, 100, 50, 27.5, 0], median_lap.DataThrottle)
        # should contain the last 10, even though the other laps do not contain it
        self.assertListEqual([6, 12, 0, -22.5, 10], median_lap.DataBraking)

        # with self.assertRaises(Exception) as context:
        #     get_median_lap([])
        #
        # self.assertTrue('This is broken' in context.exception)

    def test_filter_max_min_laps(self):
        laps = [Lap(), Lap(), Lap(), Lap()]
        laps[0].LapTime = 1000  # best lap, should be in
        laps[1].LapTime = 1200  # should be in
        laps[2].LapTime = 1250  # should be in
        laps[3].LapTime = 1275  # should be out
        laps[3].LapTime = 400  # odd lap, should be out
        filtered_laps = gt7helper.filter_max_min_laps(laps, max_lap_time=1270, min_lap_time=600)
        self.assertEqual(3, len(filtered_laps))

    def test_find_speed_peaks_and_valleys(self):
        valleyLap = Lap()
        valleyLap.DataSpeed = [0, 2, 3, 5, 5, 4.5, 3, 6, 7, 8, 7, 8, 3, 2]
        peaks, valleys = gt7helper.find_speed_peaks_and_valleys(valleyLap, width=1)
        self.assertEqual([3, 9, 11], peaks)

    def test_find_speed_peaks_and_valleys_real_data(self):
        with open("test_data/peaks_and_valleys.pickle", 'rb') as f:
            l = pickle.load(f)

        peaks, valleys = gt7helper.find_speed_peaks_and_valleys(l[1], width=100)

        self.assertEqual([310, 1400, 2481, 3248, 3757, 4841], peaks)
        self.assertEqual([449, 1647, 2675, 3361, 4105, 5030, 5322], valleys)
