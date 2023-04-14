import os
import pickle
import unittest

from bokeh.io import output_file
from bokeh.layouts import layout
from bokeh.models import Div, Plot, Scatter, Label
from bokeh.plotting import save, figure

import gt7diagrams
import gt7helper
from gt7diagrams import (
    get_throttle_braking_race_line_diagram,
    get_throttle_velocity_diagram_for_reference_lap_and_last_lap,
)
from gt7lap import Lap


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

        reference_lap = self.test_laps[0]
        last_lap = self.test_laps[1]

        lap_data = gt7helper.get_data_dict_from_lap(
            last_lap, distance_mode=True
        )
        reference_lap_data = gt7helper.get_data_dict_from_lap(
            reference_lap, distance_mode=True
        )

        throttle_line_data.data_source.data = lap_data
        breaking_line_data.data_source.data = lap_data
        coasting_line_data.data_source.data = lap_data

        reference_throttle_line_data.data_source.data = reference_lap_data
        reference_breaking_line_data.data_source.data = reference_lap_data
        reference_coasting_line_data.data_source.data = reference_lap_data

        gt7diagrams.add_annotations_to_race_line(race_line, last_lap, reference_lap)

        out_file = "test_out/test_get_throttle_braking_race_line_diagram.html"
        output_file(out_file)
        save(race_line)
        print("View file for reference at %s" % out_file)

        # get file size, should be about 3.5MB
        file_size = os.path.getsize(out_file)
        self.assertAlmostEqual(file_size, 7500000, delta=1000000)

    def helper_get_race_diagram(self):
        rd = get_throttle_velocity_diagram_for_reference_lap_and_last_lap(600)

        lap_data_1 = gt7helper.get_data_dict_from_lap(
            self.test_laps[0], distance_mode=True
        )
        lap_data_2 = gt7helper.get_data_dict_from_lap(
            self.test_laps[1], distance_mode=True
        )

        median_lap_data = gt7helper.get_data_dict_from_lap(
            gt7helper.get_median_lap(self.test_laps), distance_mode=True
        )

        rd.source_time_diff.data = gt7helper.calculate_time_diff_by_distance(
            self.test_laps[0], self.test_laps[1]
        )
        rd.source_last_lap.data = lap_data_2
        rd.source_reference_lap.data = lap_data_1
        rd.source_median_lap.data = median_lap_data

        return rd

    def test_race_diagram(self):

        rd = self.helper_get_race_diagram()

        out_file = "test_out/test_race_diagram.html"
        print("View file for reference at %s" % out_file)
        output_file(out_file)
        save(rd.get_layout())

        # get file size, should be about 5MB
        file_size = os.path.getsize(out_file)
        self.assertAlmostEqual(file_size, 5000000, delta=1000000)

    def test_add_5_additional_laps_to_race_diagram(self):

        rd = self.helper_get_race_diagram()

        # Add a random new lap to the mix
        # TODO Unfortunately, we have only 2 to pick from. Maybe improve this later
        gray_lap_source = rd.add_additional_lap_to_race_diagram("gray", self.test_laps[1], True)

        # Should now contain 1 source
        self.assertEqual(1, len(rd.sources_additional_laps))

        out_file = "test_out/test_add_5_additional_laps_to_race_diagram_with_additional_lap.html"
        print("View file for reference at %s" % out_file)
        output_file(out_file)
        save(rd.get_layout())

        rd.delete_all_additional_laps()
        self.assertEqual(0, len(rd.sources_additional_laps))

        out_file = "test_out/test_add_5_additional_laps_to_race_diagram_without_additional_lap.html"
        print("View file for reference at %s" % out_file)
        output_file(out_file)
        save(rd.get_layout())

        # get file size, should be about 6MB
        file_size = os.path.getsize(out_file)
        self.assertAlmostEqual(file_size, 6000000, delta=1000000)

        with open(out_file, 'r') as fp:
            data = fp.read()
            self.assertNotIn("1:28.465", data)


    def test_get_fuel_map_html_table(self):
        d = Div()
        lap = Lap()
        lap.fuel_at_start = 100
        lap.fuel_at_end = 80
        lap.lap_finish_time = 90 * 1000

        fuel_map_html_table = gt7diagrams.get_fuel_map_html_table(lap)
        d.text = fuel_map_html_table
        out_file = "test_out/test_get_fuel_map_html_table.html"
        output_file(out_file)
        save(d)
        print("View file for reference at %s" % out_file)

    def test_get_fuel_map_html_table_with_no_consumption(self):
        d = Div()
        fuel_map_html_table = gt7diagrams.get_fuel_map_html_table(self.test_laps[0])
        d.text = fuel_map_html_table
        out_file = "test_out/test_get_fuel_map_html_table_with_no_consumption.html"
        output_file(out_file)
        save(d)
        print("View file for reference at %s" % out_file)
