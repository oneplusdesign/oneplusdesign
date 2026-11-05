"""Checks for thirty-day scheduled research runner."""
from datetime import date
import unittest
from daily_study import (
    CASES_PER_DAY, EVALUATION_BUDGET, METHODS, START, END,
    candidate_bundles, generate_case, run_study, search
)


class DailyStudyTests(unittest.TestCase):
    def test_date_window_rejects_before_and_after(self):
        for day in (date(2026, 11, 5), date(2026, 12, 6), date(2027, 11, 6)):
            r = run_study(day)
            self.assertFalse(r["executed"])
            self.assertFalse(r["research_breakthrough_claim"])

    def test_inclusive_window(self):
        for day in (START, END):
            r = run_study(day, count=1)
            self.assertTrue(r["executed"])

    def test_matched_budget(self):
        case = generate_case(20261106, 0)
        options = candidate_bundles(case)
        for method in METHODS:
            result = search(case, options, method, 24, 7)
            self.assertEqual(result["objective_calls"], 24)

    def test_reproducibility(self):
        a = run_study(START, count=5)
        b = run_study(START, count=5)
        self.assertEqual(a, b)

    def test_no_breakthrough_claim(self):
        r = run_study(START, count=5)
        self.assertFalse(r["research_breakthrough_claim"])
        self.assertFalse(r["candidate_research_algorithm_implemented"])

    def test_solvability_partition(self):
        r = run_study(START, count=5)
        self.assertEqual(r["synthetic_cases"], r["cases_with_possible_mutual_gain"] +
                         r["cases_with_no_mutual_gain_possible"])


if __name__ == "__main__":
    unittest.main()
