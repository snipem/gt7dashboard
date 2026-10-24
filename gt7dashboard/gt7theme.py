"""Dark telemetry colors and page chrome for the Bokeh document.

Plot fills, grids, axes, titles, and legends come from ``TELEMETRY_THEME``.
Glyph colors do not: Bokeh's plotting helpers set line and text colors
explicitly, and a theme cannot override those. Series colors are therefore
constants applied where each glyph is created.

Page background and ``--bokeh-font-size`` go in ``PAGE_STYLESHEET``, which
Bokeh appends to ``document.head``. Tabs, buttons, selects, checkboxes, and
the lap table paint their own colors inside open shadow roots, so those rules
are CSS strings on each model. A shared ``InlineStyleSheet`` model is one DOM
node and can only be installed in one shadow root.
"""

from bokeh.models import GlobalInlineStyleSheet
from bokeh.themes import Theme

SURFACE = "#15191C"
PLOT = "#1C2228"
INK = "#E8EAED"
GRID = "#C5CAD6"
MUTED = "#9AA3B2"

LAST_LAP = "#7AA2F7"
REFERENCE_LAP = "#D46AB8"
MEDIAN_LAP = "#3DDC97"
TIME_DIFF = "#7AA2F7"
VARIANCE = "#9AA3B2"
THROTTLE = "#3DDC97"
BRAKE = "#F07178"
COAST = "#7AA2F7"
ZERO_DELTA = "#C5CAD6"

TRACE_WIDTH = 1.5

DEFAULT_LAP_COLORS = (LAST_LAP, REFERENCE_LAP, MEDIAN_LAP)

# Distinct from the last, reference, and median series. No black.
ADDITIONAL_LAP_COLORS = (
    "#E0AF68",
    "#F07178",
    "#BB9AF7",
    "#7DCFFF",
    "#C0CA33",
    "#FF9E64",
)

TELEMETRY_THEME = Theme(json={
    "attrs": {
        "Plot": {
            "background_fill_color": PLOT,
            "border_fill_color": SURFACE,
            "outline_line_color": GRID,
            "outline_line_alpha": 0.25,
        },
        "Grid": {
            "grid_line_color": GRID,
            "grid_line_alpha": 0.18,
        },
        "Axis": {
            "axis_line_color": GRID,
            "axis_line_alpha": 0.9,
            "major_tick_line_color": GRID,
            "major_tick_line_alpha": 0.7,
            "minor_tick_line_color": GRID,
            "minor_tick_line_alpha": 0,
            "major_label_text_color": INK,
            "major_label_text_font": "Helvetica",
            "major_label_text_font_size": "13px",
            "axis_label_text_color": INK,
            "axis_label_text_font": "Helvetica",
            "axis_label_text_font_size": "13px",
            "axis_label_text_font_style": "normal",
        },
        "Legend": {
            "label_text_color": INK,
            "label_text_font": "Helvetica",
            "label_text_font_size": "12px",
            "label_height": 14,
            "glyph_height": 10,
            "padding": 4,
            "margin": 4,
            "background_fill_color": PLOT,
            "background_fill_alpha": 0.85,
            "border_line_color": GRID,
            "border_line_alpha": 0.3,
        },
        "Title": {
            "text_color": INK,
            "text_font": "Helvetica",
            "text_font_size": "15px",
            "text_font_style": "normal",
        },
    }
})


def apply(doc) -> None:
    """Install the telemetry theme on a Bokeh document before its figures are built."""
    doc.theme = TELEMETRY_THEME


# Inherited by shadow hosts. Component CSS that sets its own color ignores this.
PAGE_CSS = f"""
html, body {{
  background: {SURFACE};
  color: {INK};
  margin: 0;
}}
:root {{
  --bokeh-base-font: Helvetica, Arial, sans-serif;
  --bokeh-font-size: 14px;
}}
"""

def page_stylesheet():
    """A new sheet for each Bokeh session. One model cannot join two documents."""
    return GlobalInlineStyleSheet(css=PAGE_CSS)

CHROME = "#2A3138"
CHROME_LINE = "#3A424A"
CHROME_HOVER = "#343C44"

TABS_CSS = f"""
:host {{
  background: {SURFACE};
  color: {INK};
}}
.bk-header {{
  background: {SURFACE};
}}
:host(.bk-above) .bk-header {{
  border-bottom: 1px solid {CHROME_LINE};
}}
.bk-tab {{
  color: {MUTED};
  background: transparent;
  font-size: 14px;
  padding: 8px 14px;
}}
.bk-tab:hover {{
  color: {INK};
  background: {PLOT};
}}
.bk-tab.bk-active {{
  color: {INK};
  background: {PLOT};
  border-color: {CHROME_LINE};
}}
.bk-tab:focus, .bk-tab:active {{
  outline-color: {GRID};
}}
"""

BUTTON_CSS = f"""
.bk-btn-default {{
  color: {INK};
  background-color: {PLOT};
  border-color: {CHROME_LINE};
  font-size: 14px;
}}
.bk-btn-default:hover {{
  color: {INK};
  background-color: {CHROME_HOVER};
  border-color: {GRID};
}}
.bk-btn-default:focus, .bk-btn-default:active {{
  outline-color: {GRID};
}}
"""

SELECT_CSS = f"""
.bk-input {{
  color: {INK};
  background-color: {PLOT};
  border-color: {CHROME_LINE};
  font-family: Helvetica, Arial, sans-serif;
  font-size: 14px;
}}
.bk-input:focus {{
  border-color: {LAST_LAP};
}}
"""

CHECKBOX_CSS = f"""
:host {{
  color: {INK};
  font-size: 14px;
}}
.bk-input-group label,
input[type="checkbox"] + span {{
  color: {INK};
  font-size: 14px;
}}
"""

TABLE_CSS = f"""
:host {{
  background: {SURFACE};
  color: {INK};
  font-size: 13px;
}}
.slick-header,
.slick-header-columns,
.slick-header-column,
.slick-header-column.ui-state-default {{
  background: {PLOT} !important;
  background-image: none !important;
  color: {INK} !important;
  border-color: {CHROME_LINE} !important;
}}
.slick-viewport,
.slick-pane {{
  background: {SURFACE};
}}
.slick-row {{
  background: {SURFACE};
  color: {INK};
}}
.slick-row.odd {{
  background: {PLOT};
}}
.slick-cell {{
  color: {INK};
  border-color: {CHROME};
}}
.slick-cell.selected {{
  background: {CHROME_HOVER};
  color: {INK};
}}
"""


def install_chrome(root, tabs, buttons, selects, checkboxes, tables) -> None:
    """Install page CSS on ``root`` and shadow CSS on each control.

    ``root`` and ``tabs`` may be the same model. The page sheet is kept in
    that case so it is not replaced by the tab rules.
    """
    page_sheet = page_stylesheet()
    if root is tabs:
        tabs.stylesheets = [page_sheet, TABS_CSS]
    else:
        root.stylesheets = [page_sheet]
        tabs.stylesheets = [TABS_CSS]
    for button in buttons:
        button.stylesheets = [BUTTON_CSS]
    for select in selects:
        select.stylesheets = [SELECT_CSS]
    for checkbox in checkboxes:
        checkbox.stylesheets = [CHECKBOX_CSS]
    for table in tables:
        table.stylesheets = [TABLE_CSS]
