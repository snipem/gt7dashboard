import os
import pickle
import unittest

from bokeh.io import output_file, show
from bokeh.layouts import layout
from bokeh.models import Div, Plot, Scatter, Label
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


COMPARISON_FIGURES = (
    "f_speed",
    "f_throttle",
    "f_braking",
    "f_coasting",
    "f_tires",
    "f_gear",
    "f_rpm",
    "f_boost",
    "f_yaw_rate",
)


class TestLapComparison(unittest.TestCase):
    def setUp(self) -> None:
        self.laps = gt7helper.load_laps_from_json("test_data/broad_bean_raceway_time_trial_4laps.json")
        self.diagram = gt7diagrams.RaceDiagram(600)
        self.table = gt7diagrams.RaceTimeTable()
        self.default_sources = {
            name: [renderer.data_source for renderer in getattr(self.diagram, name).renderers]
            for name in COMPARISON_FIGURES
        }
        self.default_renderers = {
            name: list(getattr(self.diagram, name).renderers)
            for name in COMPARISON_FIGURES
        }

    def _wire_table(self):
        def on_select(attr, old, new):
            if self.table.syncing:
                return
            self.table.apply_plot_selection(self.diagram)

        self.table.lap_times_source.selected.on_change("indices", on_select)

    def _assert_defaults_preserved(self):
        for name in COMPARISON_FIGURES:
            renderers = list(getattr(self.diagram, name).renderers)
            self.assertEqual(renderers[:3], self.default_renderers[name])
            self.assertIn(self.diagram.source_last_lap, self.default_sources[name])
            self.assertIn(self.diagram.source_reference_lap, self.default_sources[name])
            self.assertIn(self.diagram.source_median_lap, self.default_sources[name])
        self.assertEqual(len(self.diagram.f_time_diff.renderers), 1)
        self.assertIs(self.diagram.f_time_diff.renderers[0].data_source, self.diagram.source_time_diff)
        self.assertEqual(len(self.diagram.f_speed_variance.renderers), 1)

    def _assert_no_duplicate_sources(self):
        for name in COMPARISON_FIGURES:
            sources = [renderer.data_source for renderer in getattr(self.diagram, name).renderers]
            self.assertEqual(len(sources), len({id(source) for source in sources}))

    def test_plot_checkbox_is_independent_of_row_highlight(self):
        self.assertEqual(self.table.t_lap_times.selectable, "checkbox")
        self.assertIsNone(self.table.t_lap_times.index_position)
        self.assertEqual(self.table.t_lap_times.frozen_columns, 1)

    def test_toggle_on_adds_one_comparison(self):
        self._wire_table()
        self.table.show_laps(self.laps)
        self.table.lap_times_source.selected.indices = [1]

        self.assertEqual(self.diagram.comparison_laps(), [self.laps[1]])
        self.assertEqual(len(self.diagram.sources_additional_laps), 1)
        for name in COMPARISON_FIGURES:
            self.assertEqual(len(getattr(self.diagram, name).renderers), 4)
        self._assert_defaults_preserved()
        self._assert_no_duplicate_sources()

    def test_toggle_off_removes_only_that_lap(self):
        self._wire_table()
        self.table.show_laps(self.laps)
        self.table.lap_times_source.selected.indices = [0, 2]
        self.table.lap_times_source.selected.indices = [2]

        self.assertEqual(self.diagram.comparison_laps(), [self.laps[2]])
        self.assertEqual(len(self.diagram.sources_additional_laps), 1)
        extra = [
            renderer.data_source for renderer in self.diagram.f_speed.renderers
            if renderer.data_source not in (
                self.diagram.source_last_lap,
                self.diagram.source_reference_lap,
                self.diagram.source_median_lap,
            )
        ]
        self.assertEqual(list(extra[0].data["speed"]), list(self.laps[2].data_speed))
        self._assert_defaults_preserved()
        for name in ("f_gear", "f_rpm"):
            self.assertEqual(len(getattr(self.diagram, name).renderers), 4)

    def test_repeated_toggle_does_not_duplicate_traces(self):
        self.diagram.sync_comparison_laps([self.laps[0], self.laps[0]])
        self.diagram.sync_comparison_laps([self.laps[0]])
        self.assertEqual(len(self.diagram.sources_additional_laps), 1)
        self.assertEqual(len(self.diagram.f_speed.renderers), 4)
        self._assert_no_duplicate_sources()

        self.diagram.sync_comparison_laps([])
        self.assertEqual(self.diagram.comparison_laps(), [])
        self.assertEqual(len(self.diagram.sources_additional_laps), 0)
        for name in COMPARISON_FIGURES:
            self.assertEqual(list(getattr(self.diagram, name).renderers), self.default_renderers[name])

    def test_reference_lap_stays_independent(self):
        reference = self.laps[0]
        original_reference = self.diagram.source_reference_lap
        original_last = self.diagram.source_last_lap
        original_median = self.diagram.source_median_lap
        self.diagram.source_reference_lap.data = reference.get_data_dict()
        reference_speed = list(self.diagram.source_reference_lap.data["speed"])

        self.diagram.sync_comparison_laps([self.laps[1], self.laps[2]])
        self.diagram.sync_comparison_laps([self.laps[2]])

        self.assertIs(self.diagram.source_reference_lap, original_reference)
        self.assertIs(self.diagram.source_last_lap, original_last)
        self.assertIs(self.diagram.source_median_lap, original_median)
        self.assertEqual(list(self.diagram.source_reference_lap.data["speed"]), reference_speed)
        self.assertNotIn(original_reference, self.diagram.sources_additional_laps)
        self.assertNotIn(original_last, self.diagram.sources_additional_laps)
        self.assertNotIn(original_median, self.diagram.sources_additional_laps)
        self._assert_defaults_preserved()

    def test_session_change_syncs_checks_with_plotted_laps(self):
        self._wire_table()
        self.table.show_laps(self.laps)
        self.table.lap_times_source.selected.indices = [0, 2]

        remaining = self.laps[1:]
        self.diagram.retain_comparison_laps(remaining)
        self.table.show_laps(remaining, self.diagram.comparison_laps())

        self.assertEqual(self.diagram.comparison_laps(), [self.laps[2]])
        self.assertEqual(list(self.table.lap_times_source.selected.indices), [1])
        self.assertEqual(len(self.diagram.sources_additional_laps), 1)
        self._assert_defaults_preserved()
        self._assert_no_duplicate_sources()

        self.diagram.delete_all_additional_laps()
        self.table.show_laps([])
        self.assertEqual(list(self.table.lap_times_source.selected.indices), [])
        self.assertEqual(self.diagram.comparison_laps(), [])
        self.assertEqual(self.table.laps, [])
        for name in COMPARISON_FIGURES:
            self.assertEqual(list(getattr(self.diagram, name).renderers), self.default_renderers[name])

        self.table.show_laps(self.laps, self.diagram.comparison_laps())
        self.assertEqual(list(self.table.lap_times_source.selected.indices), [])
        self.assertEqual(len(self.diagram.sources_additional_laps), 0)

    def _plotted_colors(self):
        colors = {}
        for lap, (source, color) in self.diagram._comparison_by_lap.items():
            for name in COMPARISON_FIGURES:
                matches = [
                    renderer.glyph.line_color
                    for renderer in getattr(self.diagram, name).renderers
                    if renderer.data_source is source
                ]
                self.assertEqual(matches, [color])
            colors[lap] = color
        return colors

    def test_select_all_adds_and_removes_every_comparison(self):
        self._wire_table()
        self.table.show_laps(self.laps)
        all_rows = list(range(len(self.laps)))

        self.table.lap_times_source.selected.indices = all_rows
        self.assertEqual(self.diagram.comparison_laps(), self.laps)
        self.assertEqual(list(self.table.lap_times_source.selected.indices), all_rows)
        self.table.show_laps(self.laps, self.diagram.comparison_laps())
        self.assertEqual(list(self.table.lap_times_source.selected.indices), all_rows)
        self._assert_no_duplicate_sources()
        self._assert_defaults_preserved()

        self.table.lap_times_source.selected.indices = []
        self.assertEqual(self.diagram.comparison_laps(), [])
        self.assertEqual(list(self.table.lap_times_source.selected.indices), [])
        for name in COMPARISON_FIGURES:
            self.assertEqual(list(getattr(self.diagram, name).renderers), self.default_renderers[name])

    def test_recheck_keeps_the_same_comparison_color(self):
        plotted = [self.laps[0], self.laps[1], self.laps[2]]
        self.diagram.sync_comparison_laps(plotted)
        original = self._plotted_colors()

        self.diagram.sync_comparison_laps([self.laps[0], self.laps[2]])
        self.diagram.sync_comparison_laps(plotted)
        self.assertEqual(self._plotted_colors(), original)

        self.diagram.sync_comparison_laps([])
        self.diagram.sync_comparison_laps([self.laps[2], self.laps[0], self.laps[1]])
        self.assertEqual(self._plotted_colors(), original)
        self._assert_no_duplicate_sources()
