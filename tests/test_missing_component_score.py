"""Window filter and missing-score chart behavior for the daily dashboard."""

import ast
import json
import unittest
from datetime import date
from pathlib import Path

NB_PATH = Path(__file__).resolve().parents[1] / "conflict_escalation_dashboard_ml_pdf_v5.ipynb"
FUNCS = (
    "incident_timestamps_from_export",
    "osint_dates_in_window",
    "component_bar_style",
)


def _load_notebook_funcs():
    nb = json.loads(NB_PATH.read_text())
    src = "".join(nb["cells"][10]["source"])
    tree = ast.parse(src)
    wanted = set(FUNCS)
    mod = ast.Module(
        body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in wanted],
        type_ignores=[],
    )
    ast.fix_missing_locations(mod)
    ns = {}
    exec(compile(mod, str(NB_PATH), "exec"), ns)
    missing = [name for name in FUNCS if name not in ns]
    if missing:
        raise AssertionError(f"notebook cell 10 is missing {missing}")
    return ns


class OsintWindowAndMissingScoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fn = _load_notebook_funcs()

    def test_export_parser_prefers_launch_time_and_skips_blank_rows(self):
        payload = {
            "operations": [
                {
                    "incidents": [
                        {"timing": {"probable_launch_time": "2026-03-14T13:30:00Z",
                                    "announced_utc": "2026-03-14T13:43:00Z"}},
                        {"timing": {"probable_launch_time": None,
                                    "announced_utc": "2026-03-27T12:00:00Z"}},
                        {"timing": {}},
                        {"timing": {"probable_launch_time": "", "announced_utc": None}},
                    ]
                }
            ]
        }
        timestamps = self.fn["incident_timestamps_from_export"](payload)
        self.assertEqual(
            timestamps,
            ["2026-03-14T13:30:00Z", "2026-03-27T12:00:00Z"],
        )

    def test_window_matches_the_october_cutoff_that_emptied_sqlite(self):
        timestamps = [
            "2026-03-14T13:30:00Z",  # last sqlite incident
            "2026-03-17T01:37:00Z",
            "2026-03-27T12:00:00Z",  # last JSON incident
            "not-a-date",
        ]
        in_window = self.fn["osint_dates_in_window"]

        # Last green run, 2026-10-10 UTC: March 14 is the inclusive edge (210 days).
        oct10 = in_window(timestamps, date(2026, 10, 10), 90, 120)
        self.assertIn(date(2026, 3, 14), oct10)
        self.assertIn(date(2026, 3, 27), oct10)

        # First failing UTC date: March 14 drops out; March 27 is still inside.
        oct11 = in_window(timestamps, date(2026, 10, 11), 90, 120)
        self.assertNotIn(date(2026, 3, 14), oct11)
        self.assertIn(date(2026, 3, 27), oct11)

        oct13 = in_window(timestamps, date(2026, 10, 13), 90, 120)
        self.assertEqual(oct13, [date(2026, 3, 17), date(2026, 3, 27)])

        # JSON's last day ages out the following UTC date.
        oct24 = in_window(timestamps, date(2026, 10, 24), 90, 120)
        self.assertEqual(oct24, [])

    def test_missing_component_is_na_and_not_colored_or_drawn(self):
        colors, texts, heights = self.fn["component_bar_style"]([None, 54.6, 70, 49.9, 0])
        score_colors = {"#163A5F", "#4F8BBF", "#A8C8E8"}
        self.assertEqual(texts[0], "n/a")
        self.assertIsNone(heights[0])
        self.assertNotIn(colors[0], score_colors)
        self.assertEqual(texts[1], "54.6")
        self.assertEqual(heights[1], 54.6)
        self.assertEqual(colors[1], "#4F8BBF")
        self.assertEqual(colors[2], "#163A5F")
        self.assertEqual(colors[3], "#A8C8E8")
        self.assertEqual(heights[4], 0)
        self.assertEqual(texts[4], "N/A")

    def test_chart_cell_uses_the_none_safe_helper(self):
        nb = json.loads(NB_PATH.read_text())
        chart = "".join(nb["cells"][17]["source"])
        self.assertIn("component_bar_style(component_values)", chart)
        self.assertNotIn("v >= 70", chart)
        self.assertNotIn("for v in component_values", chart)


if __name__ == "__main__":
    unittest.main()
