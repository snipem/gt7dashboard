import unittest

from gt7lap import Lap
from gt7plot import get_brake_points


class TestBrakePoints(unittest.TestCase):
    def setUp(self):
        self.expected = ['foo', 'bar', 'baz']
        self.result = ['baz', 'foo', 'bar']
        self.Lap = Lap()          #P1            #P2
        self.Lap.PositionsZ =  [0, 1,  3,  4,  7, 8,  9] # Brake points are stored for x,y in z,x
        self.Lap.PositionsX =  [0, 2,  5,  8,  9, 18, 19]

        self.Lap.DataBraking = [0, 50, 40, 50, 0, 10, 0]

    def test_list_eq(self):
        """Will fail"""
        brake_points_x, brake_points_y = get_brake_points(self.Lap)
        # A break point will be the point after a zero for breaking
        self.assertListEqual(brake_points_x, [1, 8])
        self.assertListEqual(brake_points_y, [2, 18])

if __name__ == "__main__":
    unittest.main()
