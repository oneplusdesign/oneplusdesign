"""Regressions for the safe method-composition evolutionary engine."""
import unittest
from random import Random

from daily_study import candidate_bundles, generate_case
from method_evolution import Recipe, evolve_method, mutate, random_recipe, run_recipe


class EvolutionTests(unittest.TestCase):
    def test_cannot_embed_code_in_recipe(self):
        with self.assertRaises(ValueError):
            Recipe(("__import__('os')",), (1,), "local", "steady", "best")
        with self.assertRaises(ValueError):
            Recipe(("total",), (True,), "local", "steady", "best")
        with self.assertRaises(ValueError):
            Recipe(("total",), (1,), "execute", "steady", "best")

    def test_mutation_can_grow_and_shrink_method(self):
        rng = Random(23)
        recipe = Recipe(("minimum",), (1,), "local", "steady", "best")
        observed = set()
        for _ in range(240):
            recipe = mutate(recipe, rng)
            observed.add(len(recipe.features))
        self.assertTrue(any(n > 1 for n in observed))
        self.assertIn(1, observed)
        self.assertLessEqual(max(observed), 4)

    def test_strict_data_loader(self):
        valid = {
            "features": ["minimum"], "weights": [1], "proposal": "local",
            "explorer": "steady", "anchor": "best"
        }
        self.assertEqual(Recipe.from_data(valid).features, ("minimum",))
        with self.assertRaises(ValueError):
            Recipe.from_data(dict(valid, arbitrary_python="print(2)"))

    def test_matched_budget_and_feasibility(self):
        case = generate_case(23, 0)
        output = run_recipe(case, random_recipe(Random(4)), 12, 99)
        self.assertEqual(output["objective_calls"],
                         min(12, len(candidate_bundles(case))))

    def test_reproducible_experiment(self):
        kwargs = dict(train_count=8, holdout_count=12,
                      budget=8, population=4, generations=2)
        a = evolve_method(29, **kwargs)
        self.assertEqual(a, evolve_method(29, **kwargs))
        self.assertGreater(a["methods_evaluated"], 0)
        self.assertFalse(a["source_code_modified_by_worker"])
        self.assertFalse(a["research_breakthrough_claim"])

    def test_prior_method_competes_on_new_training_not_holdout(self):
        prior = Recipe(("total",), (1,), "local", "steady", "best")
        result = evolve_method(
            32, inherited=prior, train_count=8, holdout_count=12,
            budget=8, population=4, generations=2
        )
        self.assertGreaterEqual(result["training_gain_over_inherited"], 0)
        self.assertFalse(result["independent_replication"])

    def test_rejects_unbounded_runs(self):
        with self.assertRaises(ValueError):
            evolve_method(22, population=500)


if __name__ == "__main__":
    unittest.main()
