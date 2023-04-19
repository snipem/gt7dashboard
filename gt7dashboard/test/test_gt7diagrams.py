import os
import pickle
import unittest

from bokeh.io import output_file, show
from bokeh.layouts import layout
from bokeh.models import Div, Plot, Scatter, Label
from bokeh.plotting import save, figure

import gt7dashboard.gt7diagrams
import gt7dashboard.gt7helper
from gt7dashboard.gt7diagrams import (
    get_throttle_braking_race_line_diagram,
)
from gt7dashboard.gt7lap import Lap


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

        lap_data = last_lap.get_data_dict()
        reference_lap_data = reference_lap.get_data_dict()

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
        rd = gt7diagrams.RaceDiagram(600)

        lap_data_1 = self.test_laps[0].get_data_dict()
        lap_data_2 = self.test_laps[1].get_data_dict()

        median_lap_data = gt7helper.get_median_lap(self.test_laps).get_data_dict()

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

        # get file size, should be about 5MB
        file_size = os.path.getsize(out_file)
        self.assertAlmostEqual(file_size, 5000000, delta=1000000)

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


    def test_race_table(self):
        rt = gt7diagrams.RaceTimeTable()
        rt.show_laps(self.test_laps)

        out_file = "test_out/test_race_table.html"
        output_file(out_file)
        save(rt.t_lap_times)

    def test_display_variance(self):
        rd = self.helper_get_race_diagram()
        rd.update_fastest_laps_variance(self.test_laps)

        out_file = "test_out/test_get_last_variance.html"
        print("View file for reference at %s" % out_file)
        output_file(out_file)
        save(rd.get_layout())

        # get file size, should be about 5MB
        file_size = os.path.getsize(out_file)
        self.assertAlmostEqual(file_size, 5000000, delta=1000000)

    def test_display_flat_line_variance(self):
        rd = self.helper_get_race_diagram()
        # three times the same lap should result in a flat line
        rd.update_fastest_laps_variance([self.test_laps[0], self.test_laps[0], self.test_laps[0]])

        out_file = "test_out/test_display_flat_line_variance.html"
        print("View file for reference at %s" % out_file)
        output_file(out_file)
        save(layout(rd.f_speed_variance))

        # get file size, should be about 5MB
        file_size = os.path.getsize(out_file)
        self.assertAlmostEqual(file_size, 140000, delta=1000000)
