import os
import pickle
import unittest

import gt7helper
from gt7diagrams import get_throttle_braking_race_line_diagram
from bokeh.plotting import figure, show, output_file, save


class TestHelper(unittest.TestCase):
    def test_get_throttle_braking_race_line_diagram(self):
        path = os.path.join(os.getcwd(), 'test_data', 'tsukuba_2laps_rain_first_is_best.pickle')
        with open(path, 'rb') as f:
            l = pickle.load(f)

        lap_data = gt7helper.get_data_from_lap(l[1], distance_mode=True)

        race_line, throttle_line_data, breaking_line_data, coasting_line_data = get_throttle_braking_race_line_diagram(race_line_width=600)

        throttle_line_data.data_source.data = lap_data
        breaking_line_data.data_source.data = lap_data
        coasting_line_data.data_source.data = lap_data

        out_file = 'test_out/test_get_throttle_braking_race_line_diagram.html'
        save(race_line, out_file)

        # get file size, should be about 2.5MB
        file_size = os.path.getsize(out_file)
        self.assertAlmostEqual(file_size, 3500000, delta=1000000)
