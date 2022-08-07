import unittest

from gt7lap import Lap
from gt7plot import get_brake_points, get_median_lap


class TestBrakePoints(unittest.TestCase):
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

        self.Laps[0].DataBraking = [2, 4, 0, -75, 10]
        self.Laps[1].DataBraking = [4, 8, 0, -25, 10]
        self.Laps[2].DataBraking = [8, 16 ,0, -10]
        self.Laps[3].DataBraking = [100, 100,0, -20]

    def test_list_eq(self):
        """Will fail"""
        brake_points_x, brake_points_y = get_brake_points(self.Lap)
        # A break point will be the point after a zero for breaking
        self.assertListEqual(brake_points_x, [1, 8])
        self.assertListEqual(brake_points_y, [2, 18])

    def test_get_median_lap(self):
        median_lap = get_median_lap(self.Laps)
        self.assertEqual(len(median_lap.DataThrottle), len(self.Laps[0].DataThrottle))
        self.assertEqual(1225, median_lap.LapTime)
        self.assertListEqual([0, 37.5, 75, 99, 100, 50, 27.5, 0], median_lap.DataThrottle)
        # also checking if incomplete sets are ignored, 0 is not appearing, since it does not appear in elements 2 and 3
        self.assertListEqual([6, 12, 0, -22.5], median_lap.DataBraking)

        median_lap = get_median_lap([])
        self.assertIsNotNone(median_lap)


if __name__ == "__main__":
    unittest.main()
