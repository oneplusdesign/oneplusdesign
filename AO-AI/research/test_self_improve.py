"""Tests for the 'good of all represented groups' research-only gate."""
import json
from pathlib import Path
from dataclasses import asdict
from unittest.mock import patch
from tempfile import TemporaryDirectory
import unittest

from method_evolution import Recipe
from self_improve import load_champion, self_improve
from verification_gate import (
    REGIMES, SEEDS, CASES_PER_SEED, gate_metrics
)

COUNT = SEEDS * CASES_PER_SEED
REGIME_IDX = {family: [i for i in range(COUNT) if i % len(REGIMES) == n]
              for n, family in enumerate(REGIMES)}


class ProtectionTests(unittest.TestCase):
    def test_gate_never_authorizes_merge_even_with_perfect_scores(self):
        outcome = gate_metrics(
            [1] * COUNT, {"baseline": [0] * COUNT},
            REGIME_IDX, {"candidate": 1, "baseline": 1}, 8)
        self.assertTrue(outcome["passed"])
        self.assertFalse(outcome["automatic_source_merge_allowed"])
        self.assertFalse(outcome["real_world_benefit_proven"])

    def test_rejects_no_improvement(self):
        out = gate_metrics(
            [0] * COUNT, {"baseline": [0] * COUNT},
            REGIME_IDX, {"candidate": 1, "baseline": 1}, 8)
        self.assertEqual(out["decision"], "REJECT")

    def test_rejects_any_regime_regression(self):
        # Candidate wins overall but harms one test regime.
        cand = [1] * COUNT
        for i in REGIME_IDX["scarcity"]:
            cand[i] = 0
        base = [0] * COUNT
        for i in REGIME_IDX["scarcity"]:
            base[i] = 1
        out = gate_metrics(
            cand, {"baseline": base}, REGIME_IDX,
            {"candidate": 1, "baseline": 1}, 8)
        self.assertFalse(out["passed"])

    def test_rejects_excessive_compute(self):
        out = gate_metrics(
            [1] * COUNT, {"baseline": [0] * COUNT},
            REGIME_IDX, {"candidate": 2, "baseline": 1}, 8)
        self.assertFalse(out["passed"])

    def test_requires_full_sample(self):
        with self.assertRaises(ValueError):
            gate_metrics(
                [1] * 100, {"baseline": [0] * 100},
                REGIME_IDX, {"candidate": 1, "baseline": 1}, 8)

    def test_rejects_untrusted_stored_champion(self):
        with TemporaryDirectory() as dirname:
            p = Path(dirname) / "champion.json"
            p.write_text(json.dumps({
                "status": "TRAINING_DATA_CHAMPION",
                "research_only": True,
                "automatic_source_merge_allowed": False,
                "real_world_application_allowed": False,
                "generation": 2,
                "recipe": {"features": ["exec"], "weights": [1],
                           "proposal": "local", "explorer": "steady",
                           "anchor": "best"},
            }))
            self.assertEqual(load_champion(p), (None, 0))

    def test_failed_candidate_cannot_erase_a_prior_champion(self):
        previous = Recipe(("minimum",), (1,), "local", "steady", "best")
        challenger = Recipe(("total",), (1,), "diverse", "decay", "best")
        with TemporaryDirectory() as dirname:
            root = Path(dirname)
            saved = root / "prior.json"
            saved.write_text(json.dumps({
                "status": "TRAINING_DATA_CHAMPION",
                "research_only": True,
                "automatic_source_merge_allowed": False,
                "real_world_application_allowed": False,
                "generation": 4,
                "recipe": asdict(previous),
            }))
            out = root / "output"
            with patch("self_improve.make_proposal", return_value={
                "training_selected_recipe": asdict(challenger),
            }), patch("self_improve.assess", return_value={
                "passed": False, "cases": 1000, "seeds": 5,
                "decision": "REJECT",
            }):
                result = self_improve(14, out, previous=saved)
            self.assertFalse(result["proposal_accepted_as_research_recipe"])
            restored, generation = load_champion(out / "champion.json")
            self.assertEqual(restored, previous)
            self.assertEqual(generation, 4)

    def test_accepted_candidate_can_change_only_research_data(self):
        previous = Recipe(("minimum",), (1,), "local", "steady", "best")
        challenger = Recipe(("total",), (1,), "diverse", "decay", "best")
        with TemporaryDirectory() as dirname:
            root = Path(dirname)
            saved = root / "prior.json"
            saved.write_text(json.dumps({
                "status": "TRAINING_DATA_CHAMPION",
                "research_only": True,
                "automatic_source_merge_allowed": False,
                "real_world_application_allowed": False,
                "generation": 4,
                "recipe": asdict(previous),
            }))
            out = root / "output"
            with patch("self_improve.make_proposal", return_value={
                "training_selected_recipe": asdict(challenger),
            }), patch("self_improve.assess", return_value={
                "passed": True, "cases": 1000, "seeds": 5,
                "decision": "PROMOTE_RECIPE_DATA",
            }):
                result = self_improve(14, out, previous=saved)
            self.assertTrue(result["proposal_accepted_as_research_recipe"])
            promoted, generation = load_champion(out / "champion.json")
            self.assertEqual(promoted, challenger)
            self.assertEqual(generation, 5)
            self.assertEqual(result["code_merges_or_deployments"], 0)
            self.assertEqual(result["real_world_actions"], 0)

    def test_protected_end_to_end_cycle(self):
        with TemporaryDirectory() as dirname:
            out = Path(dirname)
            report = self_improve(
                37, out, train_count=8, holdout_count=12,
                population=4, generations=2,
            )
            self.assertEqual(report["independent_synthetic_cases"], 1000)
            self.assertTrue((out / "candidate_optimizer.py").is_file())
            self.assertTrue((out / "verification.json").is_file())
            self.assertEqual(report["code_merges_or_deployments"], 0)
            self.assertEqual(report["real_world_actions"], 0)
            archive = json.loads((out / "champion.json").read_text())
            self.assertFalse(archive["automatic_source_merge_allowed"])
            self.assertFalse(archive["real_world_application_allowed"])
            self.assertEqual(archive["promotion_this_run"],
                             report["proposal_accepted_as_research_recipe"])


if __name__ == "__main__":
    unittest.main()
