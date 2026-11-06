"""AΩ: continuous synthetic self-improvement with fail-closed promotion.

Every invocation generates an improved *proposal*, verifies it on independent
synthetic cases, then remembers it ONLY if all predeclared gates pass. A
rejected proposal cannot overwrite the current champion. Neither branch
edits nor deployment nor real-world actions are permitted from this worker.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path

from code_proposals import make_proposal
from method_evolution import Recipe
from verification_gate import assess


def load_champion(path: Path | None) -> tuple[Recipe | None, int]:
    """Load only prior successful, schema-bounded promoted recipe DATA."""
    if path is None or not path.is_file() or path.stat().st_size > 300_000:
        return None, 0
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if (type(payload) is not dict or
                payload.get("research_only") is not True or
                payload.get("automatic_source_merge_allowed") is not False or
                payload.get("real_world_application_allowed") is not False):
            return None, 0
        if payload.get("status") == "NO_QUALIFIED_CHAMPION":
            return None, 0
        if payload.get("status") != "TRAINING_DATA_CHAMPION":
            return None, 0
        generation = payload.get("generation")
        if type(generation) is not int or not 1 <= generation <= 100000:
            return None, 0
        return Recipe.from_data(payload["recipe"]), generation
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return None, 0


def self_improve(
    run_key: int, output: Path, previous: Path | None = None,
    *, train_count: int = 60, holdout_count: int = 200,
    population: int = 10, generations: int = 4,
) -> dict:
    if type(run_key) is not int or run_key < 0:
        raise ValueError("Invalid experiment seed")
    incumbent, generation = load_champion(previous)
    proposal = make_proposal(
        run_key, output, inherited=incumbent, train_count=train_count,
        holdout_count=holdout_count, population=population,
        generations=generations,
    )
    verification = assess(output, incumbent=incumbent)
    candidate = Recipe.from_data(proposal["training_selected_recipe"])
    accepted = verification["passed"]
    if accepted:
        incumbent = candidate
        generation += 1
    champion = {
        "status": "TRAINING_DATA_CHAMPION" if incumbent else "NO_QUALIFIED_CHAMPION",
        "research_only": True,
        "recipe": asdict(incumbent) if incumbent else None,
        "generation": generation,
        "promotion_this_run": accepted,
        "automatic_source_merge_allowed": False,
        "real_world_application_allowed": False,
        "human_review_required_for_any_deployment": True,
        "updated_utc": datetime.now(timezone.utc).isoformat(),
    }
    (output / "champion.json").write_text(
        json.dumps(champion, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    (output / "verification.json").write_text(
        json.dumps(verification, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    summary = {
        "run_key": run_key,
        "proposal_generated": True,
        "generated_source_is_executable": True,
        "previous_validated_champion_used": generation > int(accepted),
        "proposal_accepted_as_research_recipe": accepted,
        "champion_generation": generation,
        "independent_synthetic_cases": verification["cases"],
        "independent_seed_blocks": verification["seeds"],
        "gate_decision": verification["decision"],
        "real_world_actions": 0,
        "code_merges_or_deployments": 0,
        "not_a_scientific_breakthrough": True,
    }
    (output / "cycle.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-key", type=int, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--previous-champion", type=Path)
    parser.add_argument("--train-count", type=int, default=60)
    parser.add_argument("--holdout-count", type=int, default=200)
    parser.add_argument("--population", type=int, default=10)
    parser.add_argument("--generations", type=int, default=4)
    args = parser.parse_args()
    result = self_improve(
        args.run_key, args.output_dir, args.previous_champion,
        train_count=args.train_count, holdout_count=args.holdout_count,
        population=args.population, generations=args.generations,
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
