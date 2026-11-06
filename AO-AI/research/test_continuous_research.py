"""Test the consecutive, automatically varied research series."""
from datetime import date
from pathlib import Path
import tempfile
import unittest

from continuous_research import BUDGETS, FAMILIES, run_series, load_training_policy, load_training_recipe
from discovery import Hypothesis
from method_evolution import Recipe
import json


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

    def test_resume_prior_training_policy_as_data_only(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "previous.json"
            previous = {
                "synthetic_only": True,
                "research_hypothesis_outcomes": [
                    {"generated_policy": {
                        "objective": "min", "radius": 2, "explore": 0.1,
                        "tournament": 4, "restart": 5, "anchor": "best"
                    }}
                ],
            }
            path.write_text(json.dumps(previous))
            loaded = load_training_policy(path)
            self.assertIsNotNone(loaded)
            self.assertIsInstance(loaded, Hypothesis)
            self.assertEqual(loaded.objective, "min")
            result = run_series(date(2026, 11, 6), run_key=21,
                                max_experiments=5, count=2, resume=path)
            self.assertTrue(result["prior_training_policy_loaded"])
            self.assertEqual(result["research_hypothesis_rounds"], 1)
            self.assertEqual(
                result["research_hypothesis_outcomes"][0]["inherited_training_policy_signature"],
                loaded.signature(),
            )

    def test_reject_untrusted_resumed_policy(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "injection.json"
            path.write_text(json.dumps({
                "synthetic_only": True,
                "research_hypothesis_outcomes": [{
                    "generated_policy": {
                        "objective": "__import__('os').system('date')",
                        "radius": 2, "explore": 0.1, "tournament": 4,
                        "restart": 5, "anchor": "best",
                    }
                }],
            }))
            self.assertIsNone(load_training_policy(path))

    def test_structural_method_evolution_is_part_of_real_series(self):
        run = run_series(date(2026, 11, 6), run_key=46,
                         max_experiments=25, count=1)
        self.assertTrue(run["bounded_method_composition_enabled"])
        self.assertEqual(run["method_evolution_rounds"], 1)
        trial = run["method_evolution_outcomes"][0]
        self.assertGreater(trial["methods_evaluated"], 0)
        self.assertFalse(trial["source_code_modified_by_worker"])
        self.assertFalse(trial["research_breakthrough_claim"])

    def test_structural_recipe_can_be_inherited_as_data_only(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "prior.json"
            data = {
                "synthetic_only": True,
                "method_evolution_outcomes": [{"recipe": {
                    "features": ["minimum", "total"], "weights": [2, 1],
                    "proposal": "alternate", "explorer": "steady",
                    "anchor": "best"
                }}],
            }
            path.write_text(json.dumps(data))
            self.assertIsInstance(load_training_recipe(path), Recipe)
            data["method_evolution_outcomes"][0]["recipe"]["features"] = ["exec"]
            path.write_text(json.dumps(data))
            self.assertIsNone(load_training_recipe(path))

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
