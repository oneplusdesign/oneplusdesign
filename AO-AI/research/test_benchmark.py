"""Behavior checks for the transparent synthetic research baselines."""
import unittest

from benchmark import (
    Action, Case, Outcome, benchmark, cases, dominates, enumerate_feasible,
    evaluate, pareto_frontier, pareto_improvement
)


class ResearchBaselineTests(unittest.TestCase):
    def test_zero_delta_is_not_an_improvement(self):
        self.assertFalse(pareto_improvement(Outcome((), 0, (0, 0, 0))))

    def test_one_loser_disqualifies_mutual_gain(self):
        self.assertFalse(pareto_improvement(Outcome(("a",), 1, (5, -1, 3))))

    def test_positive_gain_for_one_and_no_losses_qualifies(self):
        self.assertTrue(pareto_improvement(Outcome(("a",), 1, (0, 2, 0))))

    def test_budget_enforced(self):
        case = cases()[0]
        self.assertIsNone(evaluate(case, ("automation", "training", "privacy_audit", "accessibility")))

    def test_interaction_requires_both_actions(self):
        case = cases()[0]
        single = evaluate(case, ("automation",))
        combined = evaluate(case, ("automation", "training"))
        self.assertEqual(single.gains, (7, -5, -2))
        self.assertEqual(combined.gains, (6, 1, 1))

    def test_unknown_action_rejected(self):
        with self.assertRaises(ValueError):
            evaluate(cases()[0], ("nonexistent",))

    def test_duplicate_action_rejected(self):
        with self.assertRaises(ValueError):
            evaluate(cases()[0], ("training", "training"))

    def test_cooperation_case_has_mutual_gain(self):
        report = benchmark(cases()[0])
        self.assertGreater(report["mutual_gain_outcomes"], 0)
        self.assertIsNotNone(report["best_mutual_gain_example"])

    def test_zero_sum_case_has_no_mutual_gain(self):
        report = benchmark(cases()[1])
        self.assertEqual(report["mutual_gain_outcomes"], 0)
        self.assertIsNone(report["best_mutual_gain_example"])

    def test_dominance_and_frontier(self):
        a = Outcome(("a",), 1, (3, 3))
        b = Outcome(("b",), 1, (2, 3))
        c = Outcome(("c",), 1, (4, 1))
        self.assertTrue(dominates(a, b))
        self.assertFalse(dominates(a, c))
        self.assertEqual(pareto_frontier([a, b, c]), [a, c])

    def test_budget_zero_has_only_baseline(self):
        case = Case("empty", ("a", "b"), 0, (Action("costly", 1, (3, 4)),))
        self.assertEqual(len(enumerate_feasible(case)), 1)

    def test_deterministic_seed(self):
        case = cases()[0]
        self.assertEqual(benchmark(case, seed=17), benchmark(case, seed=17))


if __name__ == "__main__":
    unittest.main()
