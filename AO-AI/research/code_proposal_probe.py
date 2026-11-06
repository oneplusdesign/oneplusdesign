"""Independent executable conformance probe for whitelisted generated source.

No token, network or GitHub write access. The generated file must be byte-for-
byte identical to the trusted generator's deterministic output before import.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from daily_study import generate_case  # noqa: E402
from method_evolution import Recipe, run_recipe  # noqa: E402
from code_proposals import source_from_recipe  # noqa: E402


def validate(source_path: Path, recipe: Recipe) -> dict:
    source = source_path.read_text(encoding="utf-8")
    if len(source) > 25_000 or source != source_from_recipe(recipe):
        raise ValueError("Source differs from validated whitelist generator")
    spec = importlib.util.spec_from_file_location("candidate_review_only", source_path)
    if spec is None or spec.loader is None:
        raise ValueError("Invalid candidate module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    checks = 0
    for family in ("mixed", "synergy", "scarcity", "balanced", "adversarial"):
        for case_idx in range(6):
            case = generate_case(7000 + case_idx, case_idx, regime_override=family)
            seed = 19 + case_idx * 47
            expected = run_recipe(case, recipe, budget=12, seed=seed)
            produced = module.search(case, budget=12, seed=seed)
            if expected != produced:
                raise AssertionError(
                    f"Source/interpreter mismatch on {family}/{case_idx}"
                )
            checks += 1
    try:
        module.search(case, budget=0, seed=19)
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid budget was accepted")
    return {
        "passed": True,
        "source_matches_whitelist": True,
        "independent_trials": checks,
        "matching_objective_evaluation_budgets": True,
        "boundary_rejection_checked": True,
        "scientific_novelty_established": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--recipe", type=str, required=True)
    args = parser.parse_args()
    recipe = Recipe.from_data(json.loads(args.recipe))
    print(json.dumps(validate(args.source, recipe), sort_keys=True))


if __name__ == "__main__":
    main()
