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

        gt7diagrams.add_starting_line_to_diagram(race_line, last_lap)

        gt7diagrams.add_peaks_and_valleys_to_diagram(race_line, last_lap, reference_lap)

        out_file = "test_out/test_get_throttle_braking_race_line_diagram.html"
        output_file(out_file)
        save(race_line)
        print("View file for reference at %s" % out_file)

        # get file size, should be about 3.5MB
        file_size = os.path.getsize(out_file)
        self.assertAlmostEqual(file_size, 7500000, delta=1000000)

    def helper_get_throttle_velocity_diagram_for_reference_lap_and_last_lap(self):
        rd = get_throttle_velocity_diagram_for_reference_lap_and_last_lap(600)

        lap_data_1 = gt7helper.get_data_dict_from_lap(
            self.test_laps[0], distance_mode=True
        )
        lap_data_2 = gt7helper.get_data_dict_from_lap(
            self.test_laps[1], distance_mode=True
        )

        # Add a random new lap to the mix
        # TODO Unfortunately, we have only 2 to pick from. Maybe improve this later
        gray_lap_source = rd.add_lap_to_race_diagram("gray", "Gray Lap", True)

        rd.sources[0].data = gt7helper.calculate_time_diff_by_distance(
            self.test_laps[0], self.test_laps[1]
        )
        rd.sources[1].data = lap_data_2
        rd.sources[2].data = lap_data_1
        rd.sources[3].data = lap_data_2
        gray_lap_source.data = lap_data_2

        return rd

    def test_get_throttle_velocity_diagram_for_reference_lap_and_last_lap(self):

        rd = self.helper_get_throttle_velocity_diagram_for_reference_lap_and_last_lap()

        out_file = "test_out/test_get_throttle_velocity_diagram_for_reference_lap_and_last_lap.html"
        print("View file for reference at %s" % out_file)
        output_file(out_file)
        save(rd.get_layout())

        # get file size, should be about 6MB
        file_size = os.path.getsize(out_file)
        self.assertAlmostEqual(file_size, 6000000, delta=1000000)

    def test_get_throttle_velocity_diagram_for_reference_lap_and_last_lap(self):

        rd = self.helper_get_throttle_velocity_diagram_for_reference_lap_and_last_lap()

        out_file = "test_out/test_get_throttle_velocity_diagram_for_reference_lap_and_last_lap.html"
        print("View file for reference at %s" % out_file)
        output_file(out_file)
        save(rd.get_layout())

        # get file size, should be about 6MB
        file_size = os.path.getsize(out_file)
        self.assertAlmostEqual(file_size, 6000000, delta=1000000)


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

    def test_remove_all_scatters(self):
        self.skipTest("Does not work yet")
        f = figure()

        f.scatter(10, 20, marker="dash", color="black", size=20, line_width=5, line_dash="dashed")
        f.scatter(30, 40, marker="dash", color="black", size=20, line_width=5, line_dash="dashed")
        f.scatter(50, 60, marker="dash", color="black", size=20, line_width=5, line_dash="dashed")

        magic_word = "test show me in the file"
        f.add_layout(Label(x=0,y=0, text=magic_word))


        magic_x = 4711
        magic_y = 993388457
        f.scatter(magic_x, magic_y, marker="dash", color="black", size=20, line_width=5, line_dash="dashed")

        gt7diagrams.remove_all_scatters_from_figure(f)

        filename = "test_out/test_remove_all_scatters.html"

        output_file(filename, title="Test")
        save(f)

        # check if file contains string
        with open(filename, 'r') as fp:
            data = fp.read()
            self.assertIn(magic_word, data)
            self.assertNotIn("Scatter", data)
            self.assertNotIn(str(magic_x), data)
            self.assertNotIn(str(magic_y), data)
            # FIXME does not work, will have to use a proper model for the scatters
            self.assertFalse(True)
