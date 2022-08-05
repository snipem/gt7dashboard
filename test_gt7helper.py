import unittest

from gt7helper import calculate_remaining_fuel


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
