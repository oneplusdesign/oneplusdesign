"""Safety and scientific separation tests for automatic hypothesis generator."""
import unittest
from dataclasses import asdict
from random import Random
from discovery import (
    Hypothesis, _paired_bootstrap_ci, discover, evaluate_policy,
    generate_hypothesis, mutate_hypothesis, run_hypothesis, training_cases
)


class DiscoveryTests(unittest.TestCase):
    def test_generated_hypothesis_restricted_to_grammar(self):
        rng = Random(6)
        for _ in range(70):
            h = generate_hypothesis(rng)
            self.assertEqual(mutate_hypothesis(h, rng).__class__, Hypothesis)

    def test_invalid_policy_rejected(self):
        with self.assertRaises(ValueError):
            Hypothesis("exec", 2, 0.1, 4, 0, "best")

    def test_query_budget_exact(self):
        h = Hypothesis("deficit", 2, 0.1, 4, 5, "best")
        case = next(training_cases(6, 1))
        self.assertEqual(run_hypothesis(case, h, 12, 7)["objective_calls"], 12)

    def test_tuned_hypothesis_reproducible(self):
        a = discover(17, count_train=8, count_holdout=16,
                     budget=10, population=5, generations=2)
        b = discover(17, count_train=8, count_holdout=16,
                     budget=10, population=5, generations=2)
        self.assertEqual(a, b)
        self.assertTrue(a["hypotheses_evaluated"] > 0)
        self.assertEqual(a["holdout_cases"], 16)
        self.assertFalse(a["research_breakthrough_claim"])

    def test_heldout_cannot_auto_claim_breakthrough(self):
        a = discover(18, count_train=6, count_holdout=12,
                     budget=8, population=4, generations=1)
        self.assertFalse(a["independent_replication"])
        self.assertFalse(a["prior_art_novelty_verified"])
        self.assertFalse(a["research_breakthrough_claim"])
        self.assertIn(a["frozen_baseline_name"], a["holdout_baselines_successes"])

    def test_warm_start_train_only(self):
        original = Hypothesis("min", 2, 0.1, 4, 5, "best")
        result = discover(27, count_train=5, count_holdout=12,
                          budget=8, population=4, generations=2,
                          seed_hypothesis=original)
        self.assertEqual(
            result["inherited_training_policy_signature"],
            original.signature(),
        )
        self.assertFalse(result["research_breakthrough_claim"])

    def test_paired_bootstrap(self):
        self.assertEqual(
            _paired_bootstrap_ci([1]*15, [0]*15, 13),
            (1, 1)
        )
        with self.assertRaises(ValueError):
            _paired_bootstrap_ci([1], [], 7)


if __name__ == "__main__":
    unittest.main()
