import pickle
import unittest
import os

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
        fuel_lap.fuel_at_start = 100
        fuel_lap.fuel_at_end = 50
        fuel_lap.lap_finish_time = 1000
        fuel_maps = gt7helper.get_fuel_on_consumption_by_relative_fuel_levels(fuel_lap)
        self.assertEqual(11, len(fuel_maps))
        print("\nFuelLvl	 Power%		    Fuel% Consum. LapsRem 	Time Rem Exp. Lap Time\n")
        for fuel_map in fuel_maps:
            print(fuel_map)

    def test_format_laps_to_table(self):
        lap1 = Lap()
        lap1.number = 1
        lap1.lap_finish_time = 11311000 / 1000
        lap1.fuel_at_end = 90
        lap1.full_throttle_ticks = 10000
        lap1.throttle_and_brake_ticks = 500
        lap1.full_brake_ticks = 10000
        lap1.no_throttle_and_no_brake_ticks = 50
        lap1.lap_ticks = 33333
        lap1.tires_spinning_ticks = 260

        lap2 = Lap()
        lap2.number = 2
        lap2.lap_finish_time = 11110000 / 1000
        lap2.fuel_at_end = 44
        lap2.full_throttle_ticks = 100
        lap2.throttle_and_brake_ticks = 750
        lap2.full_brake_ticks = 1000
        lap2.no_throttle_and_no_brake_ticks = 40
        lap2.lap_ticks = 33333
        lap2.tires_spinning_ticks = 240

        lap3 = Lap()
        lap3.number = 3
        lap3.lap_finish_time = 12114000 / 1000
        lap3.fuel_at_end = 34
        lap3.full_throttle_ticks = 100
        lap3.throttle_and_brake_ticks = 10
        lap3.full_brake_ticks = 1000
        lap3.no_throttle_and_no_brake_ticks = 100
        lap3.lap_ticks = 33333
        lap3.tires_spinning_ticks = 120

        laps = [lap3, lap2, lap1]

        result = format_laps_to_table(laps, 11110000 / 1000)
        print("\n")
        print(result)
        self.assertEqual(len(result.split("\n")), len(laps) + 2)  # +2 for header and last line

    def test_calculate_time_diff_by_distance_from_pickle(self):
        path = os.path.join(os.getcwd(), 'test_data', 'tsukuba_2laps_rain_first_is_best.pickle')
        laps = gt7helper.load_laps_from_pickle(path)

        df = calculate_time_diff_by_distance(laps[0], laps[1])

        # Check for common length but also for columns to exist
        self.assertEqual(len(df.distance), len(df.comparison))
        self.assertEqual(len(df.distance), len(df.reference))

    def test_calculate_time_diff_by_distance(self):
        best_lap = Lap()
        best_lap.data_time = [0, 2, 6, 12, 22, 45, 60, 70]
        best_lap.data_speed = [0, 50, 55, 100, 120, 30, 20, 50]

        second_best_lap = Lap()
        second_best_lap.data_time = [0, 1, 4, 5, 20, 30, 70, 75]
        second_best_lap.data_speed = [0, 40, 35, 90, 85, 50, 20, 5]

        df = calculate_time_diff_by_distance(best_lap, second_best_lap)

        print(len(df))

    def test_convert_seconds_to_milliseconds(self):
        seconds = 10000
        ms = gt7helper.convert_seconds_to_milliseconds(seconds)
        s_s = gt7helper.seconds_to_lap_time(seconds / 1000)
        print(ms, s_s)


class TestLastReferenceMedian(unittest.TestCase):

    def setUp(self):
        self.l_fast = Lap()
        self.l_fast.lap_finish_time = 100
        self.l_fast.data_speed = [200]

        self.l_middle = Lap()
        self.l_middle.lap_finish_time = 200
        self.l_middle.data_speed = [150]

        self.l_slow = Lap()
        self.l_slow.lap_finish_time = 300
        self.l_slow.data_speed = [100]

        self.l_reference = Lap()
        self.l_reference.lap_finish_time = 90
        self.l_reference.data_speed = [300]

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
        self.Lap.data_position_z = [0, 1, 3, 4, 7, 8, 9]  # Brake points are stored for x,y in z,x
        self.Lap.data_position_x = [0, 2, 5, 8, 9, 18, 19]

        self.Lap.data_braking = [0, 50, 40, 50, 0, 10, 0]

        # Set of Laps
        self.Laps = [Lap(), Lap(), Lap(), Lap()]
        self.Laps[0].lap_finish_time = 1000
        self.Laps[1].lap_finish_time = 1200
        self.Laps[2].lap_finish_time = 1250
        self.Laps[3].lap_finish_time = 1250

        self.Laps[0].data_throttle = [0, 50, 75, 100, 100, 100, 55, 0]
        self.Laps[1].data_throttle = [0, 25, 75, 98, 100, 0, 0, 0]

        self.Laps[0].data_braking = [2, 4, 0, -75, 10]  # has one more than the others
        self.Laps[1].data_braking = [4, 8, 0, -25, 10]  # has one more than the others
        self.Laps[2].data_braking = [8, 16, 0, -10]
        self.Laps[3].data_braking = [100, 100, 0, -20]

    def test_list_eq(self):
        """Will fail"""
        brake_points_x, brake_points_y = gt7helper.get_brake_points(self.Lap)
        # A break point will be the point after a zero for breaking
        self.assertListEqual(brake_points_x, [2, 18])
        self.assertListEqual(brake_points_y, [1, 8])

    def test_get_median_lap(self):
        median_lap = gt7helper.get_median_lap(self.Laps)
        self.assertEqual(len(median_lap.data_throttle), len(self.Laps[0].data_throttle))
        self.assertEqual(1225, median_lap.lap_finish_time)
        self.assertListEqual([0, 37.5, 75, 99, 100, 50, 27.5, 0], median_lap.data_throttle)
        # should contain the last 10, even though the other laps do not contain it
        self.assertListEqual([6, 12, 0, -22.5, 10], median_lap.data_braking)

        # with self.assertRaises(Exception) as context:
        #     get_median_lap([])
        #
        # self.assertTrue('This is broken' in context.exception)

    def test_filter_max_min_laps(self):
        laps = [Lap(), Lap(), Lap(), Lap()]
        laps[0].lap_finish_time = 1000  # best lap, should be in
        laps[1].lap_finish_time = 1200  # should be in
        laps[2].lap_finish_time = 1250  # should be in
        laps[3].lap_finish_time = 1275  # should be out
        laps[3].lap_finish_time = 400  # odd lap, should be out
        filtered_laps = gt7helper.filter_max_min_laps(laps, max_lap_time=1270, min_lap_time=600)
        self.assertEqual(3, len(filtered_laps))

    def test_find_speed_peaks_and_valleys(self):
        valleyLap = Lap()
        valleyLap.data_speed = [0, 2, 3, 5, 5, 4.5, 3, 6, 7, 8, 7, 8, 3, 2]
        peaks, valleys = gt7helper.find_speed_peaks_and_valleys(valleyLap, width=1)
        self.assertEqual([3, 9, 11], peaks)

    def test_find_speed_peaks_and_valleys_real_data(self):
        path = os.path.join(os.getcwd(), 'test_data', 'tsukuba_2laps_rain_first_is_best.pickle')
        with open(path, 'rb') as f:
            l = pickle.load(f)

        peaks, valleys = gt7helper.find_speed_peaks_and_valleys(l[1], width=100)

        self.assertEqual([253, 1236, 2138, 3006, 4293], peaks)
        self.assertEqual([565, 1746, 2387, 3380, 4808], valleys)

    def test_get_data_from_lap(self):
        path = os.path.join(os.getcwd(), 'test_data', 'tsukuba_2laps_rain_first_is_best.pickle')
        with open(path, 'rb') as f:
            l = pickle.load(f)

        lap = gt7helper.get_data_dict_from_lap(l[0], distance_mode=True)
        print(lap)

    def test_get_car_name_for_car_id(self):
        car_name = gt7helper.get_car_name_for_car_id(1448)
        self.assertEqual("SILVIA spec-R Aero (S15) '02", car_name)

        non_existing_car_name = gt7helper.get_car_name_for_car_id(89239843984983)
        self.assertEqual(non_existing_car_name, "")

    def test_get_car_name_for_car_id_when_csv_file_does_not_exist(self):
        gt7helper.CARS_CSV_FILENAME = "not_existing_file"
        car_name = gt7helper.get_car_name_for_car_id(1448)
        self.assertEqual(car_name, "")


    def test_get_safe_filename(self):
        self.assertEqual("Cio_123_98", gt7helper.get_safe_filename("Cio 123 '98"))
