import os
import pickle
import unittest

from bokeh.io import output_file, show
from bokeh.layouts import layout
from bokeh.models import ColumnDataSource, Div, Plot, Scatter, Label
from bokeh.plotting import save, figure

import gt7dashboard.gt7diagrams
import gt7dashboard.gt7helper
from gt7dashboard import gt7diagrams, gt7helper
from gt7dashboard.gt7diagrams import (
    get_throttle_braking_race_line_diagram,
)
from gt7dashboard.gt7lap import Lap


class TestHelper(unittest.TestCase):
    def setUp(self) -> None:
        self.test_laps = gt7helper.load_laps_from_json("test_data/broad_bean_raceway_time_trial_4laps.json")

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

        file_size = os.path.getsize(out_file)
        self.assertAlmostEqual(file_size, 3000000, delta=1000000)

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
        self.assertAlmostEqual(file_size, 2500000, delta=1000000)

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
        self.assertAlmostEqual(file_size, 2600000, delta=1000000)

        with open(out_file, 'r') as fp:
            data = fp.read()
            self.assertNotIn("1:28.465", data)

    def test_delete_additional_laps_removes_every_added_renderer(self):
        rd = self.helper_get_race_diagram()
        default_renderers = {
            plot: list(getattr(rd, plot).renderers)
            for plot in (
                "f_speed",
                "f_throttle",
                "f_braking",
                "f_coasting",
                "f_tires",
                "f_gear",
                "f_rpm",
                "f_boost",
                "f_yaw_rate",
                "f_time_diff",
                "f_speed_variance",
            )
        }
        unrelated_speed = rd.f_speed.scatter([0], [0], size=4, color="red")
        unrelated_gear = rd.f_gear.line([0, 1], [1, 0], line_color="gray")

        for index, lap in enumerate(self.test_laps):
            source = rd.add_lap_to_race_diagram("black", "row-%d" % index, True)
            source.data = lap.get_data_dict()
        rd.add_additional_lap_to_race_diagram("gray", self.test_laps[0], True)
        added = len(self.test_laps) + 1
        self.assertEqual(1, len(rd.sources_additional_laps))
        self.assertEqual(rd.number_of_default_laps + added, len(rd.speed_lines))
        self.assertGreater(len(rd.f_speed.renderers), len(default_renderers["f_speed"]) + 1)
        self.assertGreater(len(rd.f_gear.renderers), len(default_renderers["f_gear"]))

        rd.delete_all_additional_laps()

        self.assertEqual(0, len(rd.sources_additional_laps))
        self.assertEqual(rd.number_of_default_laps, len(rd.speed_lines))
        self.assertEqual(rd.number_of_default_laps, len(rd.gears_lines))
        self.assertEqual(rd.number_of_default_laps, len(rd.rpm_lines))
        for plot_name, renderers in default_renderers.items():
            plot = getattr(rd, plot_name)
            if plot_name == "f_speed":
                self.assertEqual(renderers + [unrelated_speed], list(plot.renderers))
            elif plot_name == "f_gear":
                self.assertEqual(renderers + [unrelated_gear], list(plot.renderers))
            else:
                self.assertEqual(renderers, list(plot.renderers))
        self.assertEqual(
            ["Last Lap", "Reference Lap", "Median Lap"],
            [item.label.value for item in rd.f_speed.legend.items],
        )
        self.assertEqual(
            ["Last Lap", "Reference Lap", "Median Lap"],
            [item.label.value for item in rd.f_gear.legend.items],
        )


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

    def test_get_fuel_map_html_table_negative_fuel_consumption(self):
        d = Div()
        lap = Lap()
        lap.fuel_at_start = 0
        lap.fuel_at_end = 100
        lap.lap_finish_time = 90 * 1000

        fuel_map_html_table = gt7diagrams.get_fuel_map_html_table(lap)
        d.text = fuel_map_html_table
        out_file = "test_out/test_get_fuel_map_html_table_negative_fuel_consumption.html"
        output_file(out_file)
        save(d)
        print("View file for reference at %s" % out_file)

        with open(out_file, 'r') as fp:
            data = fp.read()
            self.assertIn("No Fuel", data)

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

    def test_race_table_clears_populated_rows_and_keeps_columns(self):
        rt = gt7diagrams.RaceTimeTable()
        rt.show_laps(self.test_laps)
        keys = list(rt.lap_times_source.data.keys())
        self.assertGreater(len(list(rt.lap_times_source.data["number"])), 0)

        rt.show_laps([])

        self.assertEqual(list(rt.lap_times_source.data.keys()), keys)
        for key in keys:
            self.assertEqual(len(list(rt.lap_times_source.data[key])), 0)

        rt.show_laps(self.test_laps)
        self.assertEqual(len(list(rt.lap_times_source.data["number"])), len(self.test_laps))

    def test_race_diagram_clears_populated_sources_without_changing_columns(self):
        rd = self.helper_get_race_diagram()
        rd.update_fastest_laps_variance(self.test_laps)
        sources = [
            rd.source_last_lap,
            rd.source_reference_lap,
            rd.source_median_lap,
            rd.source_time_diff,
            rd.source_speed_variance,
        ]
        schemas = [list(source.data.keys()) for source in sources]
        self.assertIn("speed", schemas[0])
        self.assertIn("timedelta", schemas[3])
        self.assertNotIn("speed", schemas[3])
        self.assertIn("speed_variance", schemas[4])
        self.assertNotIn("speed", schemas[4])

        rd.clear_lap_sources()

        for source, keys in zip(sources, schemas):
            self.assertEqual(list(source.data.keys()), keys)
            for key in keys:
                self.assertEqual(len(list(source.data[key])), 0)

        lap_data = self.test_laps[1].get_data_dict()
        rd.source_last_lap.data = lap_data
        self.assertGreater(len(list(rd.source_last_lap.data["speed"])), 0)

    def test_diagram_and_table_repopulate_after_clear(self):
        rd = self.helper_get_race_diagram()
        rd.update_fastest_laps_variance(self.test_laps)
        last_lap = self.test_laps[1]
        reference_lap = self.test_laps[0]
        median_lap = gt7helper.get_median_lap(self.test_laps)
        self.assertGreater(len(list(rd.source_last_lap.data["speed"])), 0)

        rd.clear_lap_sources()
        self.assertEqual(len(list(rd.source_last_lap.data["speed"])), 0)
        self.assertEqual(len(list(rd.source_time_diff.data["timedelta"])), 0)
        self.assertEqual(len(list(rd.source_speed_variance.data["speed_variance"])), 0)

        rd.source_last_lap.data = last_lap.get_data_dict()
        rd.source_reference_lap.data = reference_lap.get_data_dict()
        rd.source_median_lap.data = median_lap.get_data_dict()
        rd.source_time_diff.data = gt7helper.calculate_time_diff_by_distance(reference_lap, last_lap)
        rd.update_fastest_laps_variance(self.test_laps)

        self.assertEqual(len(list(rd.source_last_lap.data["speed"])), len(last_lap.data_speed))
        self.assertEqual(len(list(rd.source_reference_lap.data["speed"])), len(reference_lap.data_speed))
        self.assertEqual(len(list(rd.source_median_lap.data["speed"])), len(median_lap.data_speed))
        self.assertGreater(len(list(rd.source_time_diff.data["timedelta"])), 0)
        self.assertGreater(len(list(rd.source_speed_variance.data["speed_variance"])), 0)
        self.assertNotIn("speed", rd.source_time_diff.data.keys())

        rt = gt7diagrams.RaceTimeTable()
        rt.show_laps(self.test_laps)
        rt.show_laps([])
        rt.show_laps(self.test_laps)
        expected_times = [
            gt7helper.seconds_to_lap_time(lap.lap_finish_time / 1000) for lap in self.test_laps
        ]
        self.assertEqual(list(rt.lap_times_source.data["time"]), expected_times)
        self.assertNotIn("0:00.000", expected_times)

    def test_race_line_clears_glyphs_and_annotations(self):
        (
            race_line,
            throttle_line,
            breaking_line,
            coasting_line,
            reference_throttle_line,
            reference_breaking_line,
            reference_coasting_line,
        ) = get_throttle_braking_race_line_diagram()
        glyphs = [
            throttle_line,
            breaking_line,
            coasting_line,
            reference_throttle_line,
            reference_breaking_line,
            reference_coasting_line,
        ]
        lap_data = self.test_laps[1].get_data_dict()
        for glyph in glyphs:
            glyph.data_source.data = lap_data
        gt7diagrams.add_annotations_to_race_line(race_line, self.test_laps[1], self.test_laps[0])
        race_line.title.text = "Lap 2"
        self.assertTrue(any(isinstance(item, Label) for item in race_line.center))
        schemas = [list(glyph.data_source.data.keys()) for glyph in glyphs]
        self.assertIn("raceline_x_throttle", schemas[0])

        gt7diagrams.clear_race_line(race_line, glyphs)

        self.assertEqual(race_line.title.text, "Race Line")
        self.assertFalse(any(isinstance(item, Label) for item in race_line.center))
        for glyph, keys in zip(glyphs, schemas):
            self.assertEqual(list(glyph.data_source.data.keys()), keys)
            for key in keys:
                self.assertEqual(len(list(glyph.data_source.data[key])), 0)

    def test_clear_source_keeps_non_lap_columns(self):
        source = ColumnDataSource(data={"distance": [1.0, 2.0], "timedelta": [3.0, 4.0]})
        gt7diagrams.clear_source(source)
        self.assertEqual(set(source.data.keys()), {"distance", "timedelta"})
        self.assertEqual(len(list(source.data["distance"])), 0)
        self.assertEqual(len(list(source.data["timedelta"])), 0)

    def test_remove_scatter_glyphs_leaves_lines(self):
        plot = figure()
        plot.line([0, 1], [0, 1])
        plot.scatter([0], [0], marker="circle", size=10)
        self.assertEqual(len(plot.renderers), 2)
        gt7diagrams.remove_scatter_glyphs(plot)
        self.assertEqual(len(plot.renderers), 1)

    def test_display_variance(self):
        rd = self.helper_get_race_diagram()
        rd.update_fastest_laps_variance(self.test_laps)

        out_file = "test_out/test_get_last_variance.html"
        print("View file for reference at %s" % out_file)
        output_file(out_file)
        save(rd.get_layout())

        # get file size, should be about 5MB
        file_size = os.path.getsize(out_file)
        self.assertAlmostEqual(file_size, 3000000, delta=1000000)

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

    def test_get_speed_peak_and_valley_diagram_different_size(self):
        last_lap = self.test_laps[0]
        reference_lap = self.test_laps[3]
        div = Div()
        div.text = gt7diagrams.get_speed_peak_and_valley_diagram(last_lap, reference_lap)

        out_file = "test_out/test_get_speed_peak_and_valley_diagram_different_size.html"
        print("View file for reference at %s" % out_file)
        output_file(out_file)
        save(layout(div))

    def test_get_speed_peak_and_valley_diagram_same_size(self):
        last_lap = self.test_laps[0]
        reference_lap = self.test_laps[1]
        div = Div()
        div.text = gt7diagrams.get_speed_peak_and_valley_diagram(last_lap, reference_lap)

        out_file = "test_out/test_get_speed_peak_and_valley_diagram_same_size.html"
        print("View file for reference at %s" % out_file)
        output_file(out_file)
        save(layout(div))
