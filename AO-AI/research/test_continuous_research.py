"""Test the consecutive, automatically varied research series."""
from datetime import date
from pathlib import Path
import tempfile
import unittest

from continuous_research import BUDGETS, FAMILIES, run_series


class SequentialResearchTests(unittest.TestCase):
    def test_research_series_runs_more_than_one_experiment(self):
        a = run_series(date(2026, 11, 6), run_key=14,
                       duration_seconds=0, max_experiments=4, count=5)
        self.assertEqual(a["completed_experiments"], 4)
        self.assertEqual(a["total_synthetic_cases"], 20)
        self.assertEqual(len(a["parameter_sweep"]), 4)
        self.assertFalse(a["research_breakthrough_claim"])

    def test_reproducibility_of_aggregated_results(self):
        a = run_series(date(2026, 11, 6), run_key=3,
                       max_experiments=3, count=4)
        b = run_series(date(2026, 11, 6), run_key=3,
                       max_experiments=3, count=4)
        self.assertEqual(a["parameter_sweep"], b["parameter_sweep"])

    def test_each_experiment_changes_regime_and_then_budget(self):
        a = run_series(date(2026, 11, 6), run_key=15,
                       max_experiments=6, count=2)
        keys = list(a["parameter_sweep"])
        self.assertEqual(keys[0], FAMILIES[0] + ":budget_" + str(BUDGETS[0]))
        self.assertEqual(keys[5], FAMILIES[0] + ":budget_" + str(BUDGETS[1]))

    def test_outside_window_does_not_run(self):
        a = run_series(date(2026, 12, 6), run_key=3,
                       duration_seconds=0, max_experiments=10)
        self.assertEqual(a["completed_experiments"], 0)
        self.assertFalse(a["executed"])

    def test_no_unbounded_run(self):
        with self.assertRaises(ValueError):
            run_series(date(2026, 11, 6), run_key=10,
                       max_experiments=0, duration_seconds=0)

    def test_produces_checkpoint_and_no_private_details(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "result.json"
            report = run_series(date(2026, 11, 6), run_key=10,
                                max_experiments=2, count=2, output=path)
            self.assertTrue(path.exists())
            self.assertEqual(report["completed_experiments"], 2)
            self.assertNotIn("password", path.read_text())
            self.assertIn("research_breakthrough_claim", path.read_text())


if __name__ == "__main__":
    unittest.main()
