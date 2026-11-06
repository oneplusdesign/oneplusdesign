"""AΩ | AI: safe, reproducible *source-code proposal* pipeline.

Evolves method recipes, then emits executable Python source as a REVIEW-ONLY
artifact. Produced programs are generated solely from a fixed whitelist and
tested in a separate unprivileged process before archiving. This is bounded
program synthesis, NOT autonomous general-purpose programming, model training,
or permission to modify the main research software.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys

from method_evolution import Recipe, evolve_method

FEATURE_EXPRESSIONS = {
    "minimum": "min(gains)",
    "total": "sum(gains)",
    "positive": "sum(max(0, g) for g in gains)",
    "harm": "sum(max(0, -g) for g in gains)",
    "losers": "sum(g < 0 for g in gains)",
    "spread": "max(gains) - min(gains)",
}


def source_from_recipe(recipe: Recipe) -> str:
    """Compile a validated finite-grammar recipe into a complete search module.

    There is no untrusted prompt, arbitrary code token, dynamic import, or
    arbitrary executable expression in the generated source.
    """
    if type(recipe) is not Recipe:
        raise ValueError("Only a validated Recipe can generate Python source")
    expression = " + ".join(
        f"({weight} * ({FEATURE_EXPRESSIONS[feature]}))"
        for feature, weight in zip(recipe.features, recipe.weights)
    )
    explorer_code = {
        "steady": "0.20",
        "decay": "0.4 * (1 - step / max(1, budget))",
        "stagnation": "0.65 if stalled >= 3 else 0.1",
    }[recipe.explorer]
    anchor_code = {
        "best": "max(seen, key=lambda x: (_score(seen[x]), x))",
        "recent": "recent",
    }[recipe.anchor]
    proposal_code = {
        "local": "True",
        "diverse": "False",
        "alternate": "step % 2 == 0",
    }[recipe.proposal]
    return f'''"""AUTO-GENERATED AΩ REVIEW PROPOSAL — NOT APPROVED OR DEPLOYED.

Generated from whitelisted method components. Synthetic experiments only.
Do not represent these outcomes as proof of benefit to people or ecosystems.
"""
from random import Random

from benchmark import evaluate, pareto_improvement
from daily_study import candidate_bundles


def _score(gains):
    return {expression}


def _exploration(step, budget, stalled):
    return {explorer_code}


def search(case, budget, seed):
    """Evaluate no more than budget feasible synthetic candidates."""
    if not 1 <= budget <= 200:
        raise ValueError("Invalid research evaluation budget")
    rng = Random(seed)
    options = candidate_bundles(case)
    seen = {{}}
    recent = None
    best = None
    stalled = 0
    found = None
    for step in range(min(budget, len(options))):
        available = [x for x in options if x not in seen]
        if not seen or rng.random() < _exploration(step, budget, stalled):
            chosen = rng.choice(available)
        else:
            base = {anchor_code}
            pool = rng.sample(available, min(12, len(available)))
            distance = lambda x, y: len(set(x).symmetric_difference(y))
            if {proposal_code}:
                chosen = min(pool, key=lambda x: (distance(x, base), x))
            else:
                chosen = max(pool, key=lambda x: (
                    min(distance(x, s) for s in seen), distance(x, base), x))
        outcome = evaluate(case, chosen)
        if outcome is None:
            raise AssertionError("Generated action is not feasible")
        seen[chosen], recent = outcome.gains, chosen
        value = _score(outcome.gains)
        if best is None or value > best:
            best, stalled = value, 0
        else:
            stalled += 1
        if found is None and pareto_improvement(outcome):
            found = step + 1
    return {{"found": found is not None, "first_found_at": found,
             "objective_calls": len(seen)}}
'''


def recover_inherited(path: Path | None) -> Recipe | None:
    """Recover DATA from an older proposal, not source or executable code."""
    if path is None or not path.is_file() or path.stat().st_size > 300_000:
        return None
    try:
        content = json.loads(path.read_text(encoding="utf-8"))
        if (type(content) is not dict or
                content.get("synthetic_only") is not True or
                content.get("unattended_source_promotion") is not False):
            return None
        return Recipe.from_data(content["training_selected_recipe"])
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return None


def make_proposal(
    run_key: int, output_dir: Path,
    *,
    inherited: Recipe | None = None,
    train_count: int = 40,
    holdout_count: int = 120,
    population: int = 8,
    generations: int = 3,
) -> dict:
    """Generate code, then independently execute bounded conformance tests."""
    if type(run_key) is not int or run_key < 0:
        raise ValueError("Invalid run key")
    result = evolve_method(
        run_key, inherited=inherited, train_count=train_count,
        holdout_count=holdout_count, budget=12,
        population=population, generations=generations,
    )
    selected = Recipe.from_data(result["recipe"])
    source = source_from_recipe(selected)
    compile(source, "<generated_proposal>", "exec")  # syntax check
    output_dir.mkdir(parents=True, exist_ok=True)
    source_path = output_dir / "candidate_optimizer.py"
    source_path.write_text(source, encoding="utf-8")
    probe_path = Path(__file__).resolve().with_name("code_proposal_probe.py")
    cmd = [
        sys.executable, "-I", str(probe_path),
        "--source", str(source_path.resolve()),
        "--recipe", selected.signature(),
    ]
    # No inherited env containing tokens, API keys or credentials.
    safe_env = {"PYTHONHASHSEED": "0", "PYTHONDONTWRITEBYTECODE": "1"}
    if os.name == "nt":
        safe_env["SYSTEMROOT"] = os.environ.get("SYSTEMROOT", "C:\\Windows")
    completed = subprocess.run(
        cmd, cwd=output_dir, env=safe_env,
        capture_output=True, text=True, timeout=35, check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "Generated code conformance test failed: " +
            (completed.stderr or completed.stdout)[-1500:]
        )
    verified = json.loads(completed.stdout)
    if (not verified.get("passed") or
            verified.get("source_matches_whitelist") is not True or
            verified.get("independent_trials", 0) < 30):
        raise AssertionError("Insufficient generated-code conformance checks")
    manifest = {
        "project": "AO-AI",
        "experiment": "bounded_source_code_proposal_and_conformance",
        "synthetic_only": True,
        "run_key": run_key,
        "generated_source_sha256": sha256(source.encode("utf-8")).hexdigest(),
        "training_selected_recipe": asdict(selected),
        "inherited_recipe_used": inherited is not None,
        "conformance": verified,
        "training_cases": result["training_cases"],
        "holdout_cases": result["holdout_cases"],
        "methods_evaluated": result["methods_evaluated"],
        "holdout_successes": result["holdout_successes"],
        "holdout_baseline_successes": result["holdout_baseline_successes"],
        "holdout_ci95": result["holdout_ci95"],
        "holdout_delta": result["holdout_delta"],
        "status": "REVIEW_ONLY_NOT_DEPLOYED",
        "automatic_merge_allowed": False,
        "unattended_source_promotion": False,
        "source_code_modified_by_worker": False,
        "independent_scientific_replication": False,
        "real_world_benefit_verified": False,
        "research_breakthrough_claim": False,
        "limitations": [
            "New source is emitted from fixed human-designed components.",
            "Conformance tests ensure fidelity to the recipe, not scientific novelty.",
            "Holdout is exploratory, not an independent confirmatory replication.",
            "A separate authorized review is required for any deployment.",
            "No assessment of real people's interests or unknown stakeholders.",
        ],
    }
    (output_dir / "proposal.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-key", type=int, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--previous-report", type=Path)
    parser.add_argument("--train-count", type=int, default=40)
    parser.add_argument("--holdout-count", type=int, default=120)
    parser.add_argument("--population", type=int, default=8)
    parser.add_argument("--generations", type=int, default=3)
    args = parser.parse_args()
    inherited = recover_inherited(args.previous_report)
    report = make_proposal(
        args.run_key, args.output_dir, inherited=inherited,
        train_count=args.train_count, holdout_count=args.holdout_count,
        population=args.population, generations=args.generations,
    )
    print(json.dumps({
        "status": report["status"],
        "methods_evaluated": report["methods_evaluated"],
        "generated_source_sha256": report["generated_source_sha256"],
        "holdout_delta": report["holdout_delta"],
        "verified_code_tests": report["conformance"]["independent_trials"],
        "automatic_merge_allowed": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
