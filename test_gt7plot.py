import pickle
import unittest

import gt7plot
from gt7lap import Lap
from gt7plot import get_brake_points, get_median_lap, filter_max_min_laps, find_speed_peaks_and_valleys


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

        self.Laps[0].DataBraking = [2, 4, 0, -75, 10]  # has one more than the others
        self.Laps[1].DataBraking = [4, 8, 0, -25, 10]  # has one more than the others
        self.Laps[2].DataBraking = [8, 16, 0, -10]
        self.Laps[3].DataBraking = [100, 100, 0, -20]

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
        filtered_laps = filter_max_min_laps(laps, max_lap_time=1270, min_lap_time=600)
        self.assertEqual(3, len(filtered_laps))

    def test_find_speed_peaks_and_valleys(self):
        valleyLap = Lap()
        valleyLap.DataSpeed = [0, 2, 3, 5, 5, 4.5, 3, 6, 7, 8, 7, 8, 3, 2]
        peaks, valleys = find_speed_peaks_and_valleys(valleyLap, width=1)
        self.assertEqual([3, 9, 11], peaks)


    @unittest.skip("Works only with test data")
    def test_find_speed_peaks_and_valleys_real_data(self):

        with open("data/peaks_and_valleys.pickle", 'rb') as f:
            l = pickle.load(f)

        peaks, valleys = find_speed_peaks_and_valleys(l[1], width=100)

        gt7plot.plot_session_analysis([l[1]], open_in_browser=True)

        self.assertEqual([310, 1400, 2481, 3248, 3757, 4841], peaks)
        self.assertEqual([449, 1647, 2675, 3361, 4105, 5030, 5322], valleys)


if __name__ == "__main__":
    unittest.main()
