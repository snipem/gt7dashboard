import os
import pickle
import unittest

from bokeh.layouts import layout
from bokeh.plotting import save

import gt7helper
from gt7diagrams import (
    get_throttle_braking_race_line_diagram,
    get_throttle_velocity_diagram_for_reference_lap_and_last_lap,
)


class TestHelper(unittest.TestCase):
    def setUp(self) -> None:
        self.path = os.path.join(
            os.getcwd(), "test_data", "tsukuba_2laps_rain_first_is_best.pickle"
        )
        with open(self.path, "rb") as f:
            self.test_laps = pickle.load(f)

    def test_get_throttle_braking_race_line_diagram(self):
        (
            race_line,
            throttle_line_data,
            breaking_line_data,
            coasting_line_data,
            reference_throttle_line_data,
            reference_breaking_line_data,
            reference_coasting_line_data,
        ) = get_throttle_braking_race_line_diagram()

        lap_data = gt7helper.get_data_dict_from_lap(
            self.test_laps[1], distance_mode=True
        )
        reference_lap_data = gt7helper.get_data_dict_from_lap(
            self.test_laps[0], distance_mode=True
        )

        throttle_line_data.data_source.data = lap_data
        breaking_line_data.data_source.data = lap_data
        coasting_line_data.data_source.data = lap_data

        reference_throttle_line_data.data_source.data = reference_lap_data
        reference_breaking_line_data.data_source.data = reference_lap_data
        reference_coasting_line_data.data_source.data = reference_lap_data

        out_file = "test_out/test_get_throttle_braking_race_line_diagram.html"
        save(race_line, out_file)
        print("View file for reference at %s" % out_file)

        # get file size, should be about 3.5MB
        file_size = os.path.getsize(out_file)
        self.assertAlmostEqual(file_size, 7500000, delta=1000000)

    def test_get_throttle_velocity_diagram_for_reference_lap_and_last_lap(self):
        (
            f_time_diff,
            f_speed,
            f_throttle,
            f_braking,
            f_coasting,
            sources,
        ) = get_throttle_velocity_diagram_for_reference_lap_and_last_lap(600)

        lap_data_1 = gt7helper.get_data_dict_from_lap(
            self.test_laps[0], distance_mode=True
        )
        lap_data_2 = gt7helper.get_data_dict_from_lap(
            self.test_laps[1], distance_mode=True
        )

        out_file = "test_out/test_get_throttle_velocity_diagram_for_reference_lap_and_last_lap.html"
        print("View file for reference at %s" % out_file)

        sources[0].data = gt7helper.calculate_time_diff_by_distance(
            self.test_laps[0], self.test_laps[1]
        )
        sources[1].data = lap_data_2
        sources[2].data = lap_data_1
        sources[3].data = lap_data_2

        save(
            layout(
                [f_time_diff],
                [f_speed],
                [f_throttle],
                [f_braking],
                [f_coasting],
            ),
            filename=out_file,
        )

        # get file size, should be about 5MB
        file_size = os.path.getsize(out_file)
        self.assertAlmostEqual(file_size, 5000000, delta=1000000)
