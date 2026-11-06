"""Check source proposal generation, arbitrary-code rejection and no auto-merge."""
from pathlib import Path
import tempfile
import unittest
from random import Random

from code_proposals import (
    make_proposal, recover_inherited, source_from_recipe
)
from method_evolution import Recipe, random_recipe


class CodeProposalTests(unittest.TestCase):
    def test_deterministic_source_from_structured_method(self):
        r = random_recipe(Random(9))
        a, b = source_from_recipe(r), source_from_recipe(r)
        self.assertEqual(a, b)
        compile(a, "<candidate>", "exec")
        self.assertIn("def search(case, budget, seed)", a)
        self.assertNotIn("import os", a)
        self.assertNotIn("import subprocess", a)

    def test_never_accept_arbitrary_python_from_recipe(self):
        with self.assertRaises(ValueError):
            Recipe.from_data({
                "features": ["__import__('os').system('false')"],
                "weights": [1], "proposal": "local", "explorer": "steady",
                "anchor": "best",
            })

    def test_end_to_end_generates_executable_artifact_not_commit(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            report = make_proposal(
                203, out, train_count=8, holdout_count=12,
                population=4, generations=2,
            )
            self.assertTrue((out / "candidate_optimizer.py").is_file())
            self.assertTrue((out / "proposal.json").is_file())
            self.assertEqual(report["status"], "REVIEW_ONLY_NOT_DEPLOYED")
            self.assertFalse(report["automatic_merge_allowed"])
            self.assertFalse(report["source_code_modified_by_worker"])
            self.assertGreaterEqual(report["conformance"]["independent_trials"], 30)

    def test_previous_report_is_validated_data_not_executable_code(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "prior.json"
            f.write_text('{"synthetic_only":true,"unattended_source_promotion":false,'
                         '"training_selected_recipe":{"features":["total"],'
                         '"weights":[1],"proposal":"local",'
                         '"explorer":"steady","anchor":"best"}}')
            self.assertIsInstance(recover_inherited(f), Recipe)
            f.write_text(f.read_text().replace('"total"', '"__import__(1)"'))
            self.assertIsNone(recover_inherited(f))

    def test_refuse_invalid_inputs(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                make_proposal(-1, Path(d))


if __name__ == "__main__":
    unittest.main()
