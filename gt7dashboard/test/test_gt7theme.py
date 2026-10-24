import unittest

from bokeh.document import Document
from bokeh.models import GlobalInlineStyleSheet
from bokeh.plotting import figure

from gt7dashboard import gt7theme


class TestTelemetryColors(unittest.TestCase):
    def test_additional_lap_colors_do_not_collide_with_defaults(self):
        defaults = set(gt7theme.DEFAULT_LAP_COLORS)
        additional = list(gt7theme.ADDITIONAL_LAP_COLORS)
        banned = {"black", "#000", "#000000", "#000000ff"}

        self.assertTrue(additional)
        self.assertTrue(defaults.isdisjoint(additional))
        for color in list(defaults) + additional:
            self.assertNotIn(color.lower(), banned)

    def test_document_theme_uses_dark_surface_and_visible_axes(self):
        doc = Document()
        gt7theme.apply(doc)
        plot = figure()
        plot.line([0, 1], [0, 1], legend_label="Last Lap")
        doc.add_root(plot)

        self.assertEqual(plot.background_fill_color, gt7theme.PLOT)
        self.assertEqual(plot.border_fill_color, gt7theme.SURFACE)
        self.assertGreater(plot.xaxis.axis_line_alpha, 0)
        self.assertEqual(plot.xaxis.major_label_text_color, gt7theme.INK)
        self.assertGreater(plot.xgrid.grid_line_alpha, 0)
        self.assertEqual(plot.title.text_color, gt7theme.INK)
        self.assertEqual(plot.legend.label_text_color, gt7theme.INK)
        self.assertEqual(plot.legend.padding, 4)
        self.assertEqual(plot.legend.margin, 4)
        self.assertEqual(plot.legend.glyph_height, 10)
        self.assertEqual(plot.legend.label_height, 14)
        self.assertTrue(plot.legend.visible)

    def test_page_sheet_is_global_and_controls_target_shadow_roots(self):
        sheet = gt7theme.page_stylesheet()
        self.assertIsInstance(sheet, GlobalInlineStyleSheet)
        self.assertIsNot(sheet, gt7theme.page_stylesheet())
        self.assertIn(gt7theme.SURFACE, sheet.css)
        self.assertIn("--bokeh-font-size", sheet.css)
        self.assertIn(".bk-tab", gt7theme.TABS_CSS)
        self.assertIn(".bk-btn-default", gt7theme.BUTTON_CSS)
        self.assertIn(".bk-input", gt7theme.SELECT_CSS)
        self.assertIn('input[type="checkbox"]', gt7theme.CHECKBOX_CSS)
        self.assertIn(".slick-header", gt7theme.TABLE_CSS)
