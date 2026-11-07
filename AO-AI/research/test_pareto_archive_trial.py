"""Deterministic, negative-control tests for isolated archive experiment."""
import unittest

from benchmark import Action, Case
from daily_study import candidate_bundles, generate_case
from pareto_archive_trial import (
    add_to_archive, archive_search, compare, dominates_vector,
    paired_seed_block_bootstrap,
)


class ArchiveTrialTests(unittest.TestCase):
    def test_archive_dominance_and_equal_vector_deduplication(self):
        a, b, c, d = ("a",), ("b",), ("c",), ("d",)
        seen = {a: (1, -1, 0), b: (0, 1, 0), c: (2, 2, 0), d: (2, 2, 0)}
        archive = []
        self.assertTrue(add_to_archive(archive, seen, a))
        self.assertTrue(add_to_archive(archive, seen, b))
        self.assertTrue(add_to_archive(archive, seen, c))
        self.assertEqual(archive, [c])
        self.assertFalse(add_to_archive(archive, seen, d))
        self.assertEqual(archive, [c])
        self.assertTrue(dominates_vector((1, 1, 1), (1, 0, 1)))
        self.assertFalse(dominates_vector((1, 1, 1), (1, 1, 1)))
        with self.assertRaises(ValueError):
            dominates_vector((1,), (1, 2))

    def test_never_claims_pareto_gain_in_zero_sum_scarcity(self):
        for i in range(10):
            case = generate_case(1223, i, regime_override="scarcity")
            options = candidate_bundles(case)
            r = archive_search(case, options, 12, 99 + i)
            self.assertFalse(r["found"])
            self.assertEqual(r["objective_calls"], 12)
            self.assertEqual(r["hard_constraint_violations"], 0)

    def test_hard_cost_constraint_and_no_duplicate_queries(self):
        case = Case("tiny", ("a", "b", "c"), 1, (
            Action("x", 1, (2, -1, 0)),
            Action("y", 1, (-1, 2, 0)),
            Action("z", 1, (1, 1, 1)),
        ))
        options = candidate_bundles(case)
        a = archive_search(case, options, 200, 33)
        b = archive_search(case, options, 200, 33)
        self.assertEqual(a, b)
        self.assertEqual(a["objective_calls"], len(options))
        self.assertTrue(a["found"])
        self.assertEqual(a["hard_constraint_violations"], 0)
        with self.assertRaises(ValueError):
            archive_search(case, options, 0, 33)
        with self.assertRaises(ValueError):
            archive_search(case, options + [options[0]], 12, 33)

    def test_cluster_bootstrap_zero_effect_and_invalid_inputs(self):
        x = [0, 1, 1, 0, 1, 0]
        ids = [0, 0, 0, 1, 1, 1]
        self.assertEqual(paired_seed_block_bootstrap(x, x, ids, 7, 100), (0, 0))
        with self.assertRaises(ValueError):
            paired_seed_block_bootstrap(x, x[:-1], ids, 7, 100)
        with self.assertRaises(ValueError):
            paired_seed_block_bootstrap(x, x, [0] * 6, 7, 100)

    def test_small_frozen_comparison_is_deterministic_except_wall_time(self):
        a = compare(seed_key=81, seeds=2, cases_per_seed=5, budget=8)
        b = compare(seed_key=81, seeds=2, cases_per_seed=5, budget=8)
        for result in (a, b):
            self.assertEqual(result["heldout_cases"], 10)
            self.assertEqual(result["hard_constraint_violations"], 0)
            self.assertFalse(result["real_world_application_allowed"])
            self.assertFalse(result["independent_replication"])
        for key in ("candidate_successes", "comparisons", "seed_blocks"):
            # compute_ratio/regime results include wall time; compare only
            # stochastic outcomes and confidence bounds.
            if key == "comparisons":
                for m in a[key]:
                    for field in ("successes", "delta_pp", "seed_block_bootstrap_ci95_pp", "regime_deltas_pp"):
                        self.assertEqual(a[key][m][field], b[key][m][field])
            else:
                self.assertEqual(a[key], b[key])


if __name__ == "__main__":
    unittest.main()
