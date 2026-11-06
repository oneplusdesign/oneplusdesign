"""AΩ: independent synthetic promotion gate for read-only method evolution.

Promotes only validated JSON recipes, NEVER deployed source or real-world
actions. No measurement here certifies that *all* affected beings exist in
the synthetic model. Unknown stakeholders always block real-world use.
"""
from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
from statistics import mean
from time import perf_counter

from benchmark import evaluate, pareto_improvement
from code_proposals import source_from_recipe
from daily_study import candidate_bundles, generate_case, search
from discovery import _paired_bootstrap_ci
from method_evolution import Recipe, run_recipe

REGIMES = ("mixed", "synergy", "scarcity", "balanced", "adversarial")
SEEDS = 5
CASES_PER_SEED = 200
BUDGET = 12
MIN_DELTA = 0.05
MAX_COMPUTE_RATIO = 1.5
BASELINES = ("weighted_local_search", "maximin_local_search")


def gate_metrics(candidate, comparisons, regimes, seconds, seed):
    """Fail closed if *any* baseline, stakeholder regime or cost gate fails."""
    n = SEEDS * CASES_PER_SEED
    if (len(candidate) != n or any(v not in (0, 1) for v in candidate)
            or not comparisons or set(regimes) != set(REGIMES)):
        raise ValueError("Incomplete validation observations")
    conditions = {}
    details = {}
    for name, pair in comparisons.items():
        if len(pair) != n or any(v not in (0, 1) for v in pair):
            raise ValueError("Incomplete baseline or incumbent observations")
        delta = round(mean(a - b for a, b in zip(candidate, pair)), 4)
        low, high = _paired_bootstrap_ci(candidate, pair, seed + 37, 400)
        ratio = seconds["candidate"] / seconds[name] if seconds[name] > 0 else float("inf")
        by_regime = {}
        for regime in REGIMES:
            indices = regimes[regime]
            if len(indices) != n // len(REGIMES):
                raise ValueError("Every regime requires equal representation")
            by_regime[regime] = round(mean(candidate[i] - pair[i] for i in indices), 4)
        conditions[name] = (
            delta > MIN_DELTA and low > 0
            and ratio <= MAX_COMPUTE_RATIO
            and all(value >= 0 for value in by_regime.values())
        )
        details[name] = {
            "delta": delta, "paired_ci95": [low, high],
            "compute_ratio": round(ratio, 4), "per_regime_delta": by_regime,
            "passed": conditions[name],
        }
    passed = all(conditions.values())
    return {"passed": passed, "decision": "PROMOTE_RECIPE_DATA" if passed else "REJECT",
            "comparisons": details, "cases": n, "seeds": SEEDS,
            "no_real_world_actions": True, "real_world_benefit_proven": False,
            "automatic_source_merge_allowed": False}


def _load_generated(path: Path, recipe: Recipe, claimed_hash: str):
    source = path.read_text(encoding="utf-8")
    if (len(source) > 25000 or source != source_from_recipe(recipe)
            or sha256(source.encode()).hexdigest() != claimed_hash):
        raise ValueError("Source is not from the trusted, bounded compiler")
    spec = importlib.util.spec_from_file_location("reviewed_candidate", path)
    if spec is None or spec.loader is None:
        raise ValueError("Bad source proposal")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.search


def assess(proposal_dir: Path, incumbent: Recipe | None = None,
           cases_per_seed: int = CASES_PER_SEED):
    """Run independent held-out cases against references and current champion."""
    if cases_per_seed != CASES_PER_SEED:
        raise ValueError("Promotion requires the full 1000-case evaluation")
    manifest = json.loads((proposal_dir / "proposal.json").read_text(encoding="utf-8"))
    if (manifest.get("synthetic_only") is not True or
            manifest.get("automatic_merge_allowed") is not False or
            manifest.get("status") != "REVIEW_ONLY_NOT_DEPLOYED" or
            manifest.get("conformance", {}).get("passed") is not True):
        raise ValueError("Invalid candidate manifest")
    recipe = Recipe.from_data(manifest["training_selected_recipe"])
    search_code = _load_generated(
        proposal_dir / "candidate_optimizer.py",
        recipe, manifest["generated_source_sha256"])
    if incumbent is not None and type(incumbent) is not Recipe:
        raise ValueError("Incumbent must be validated recipe data")
    run_key = manifest["run_key"]
    if type(run_key) is not int or run_key < 0:
        raise ValueError("Invalid test seed")
    compared = list(BASELINES) + (["incumbent"] if incumbent else [])
    outcomes = {"candidate": []}
    outcomes.update({name: [] for name in compared})
    costs = {name: 0.0 for name in outcomes}
    regimes = defaultdict(list)
    verified_claims = 0
    for block in range(SEEDS):
        case_seed = run_key * 31 + 9_000_001 + block * 104729
        for idx in range(CASES_PER_SEED):
            regime = REGIMES[idx % len(REGIMES)]
            case = generate_case(case_seed, idx, regime_override=regime)
            options = candidate_bundles(case)
            seed = case_seed * 17 + idx * 1009
            functions = {
                "candidate": lambda: search_code(case, BUDGET, seed),
                "weighted_local_search": lambda: search(
                    case, options, "weighted_local_search", BUDGET, seed),
                "maximin_local_search": lambda: search(
                    case, options, "maximin_local_search", BUDGET, seed),
            }
            if incumbent:
                functions["incumbent"] = lambda: run_recipe(case, incumbent, BUDGET, seed)
            # Alternating ordering helps reduce one-sided measurement noise.
            for name in (reversed(list(functions)) if idx % 2 else functions):
                start = perf_counter()
                result = functions[name]()
                costs[name] += max(perf_counter() - start, 1e-12)
                if result["objective_calls"] != min(BUDGET, len(options)):
                    raise AssertionError("Objective-query budget violation")
                found = bool(result.get("found", result.get("found_mutual_gain", False)))
                outcomes[name].append(int(found))
                if name == "candidate" and found:
                    # Synthetic feasibility/Pareto oracle is used for AUDIT ONLY.
                    if not any(pareto_improvement(evaluate(case, opt)) for opt in options):
                        raise AssertionError("False claim of no-harm Pareto improvement")
                    verified_claims += 1
            regimes[regime].append(block * CASES_PER_SEED + idx)
    result = gate_metrics(
        outcomes["candidate"], {name: outcomes[name] for name in compared},
        dict(regimes), costs, run_key)
    result.update({
        "verification": "independent_synthetic_holdout",
        "verified_candidate_pareto_claims": verified_claims,
        "known_stakeholders_only": True,
        "unknown_or_unrepresented_stakeholders_in_real_world": "NOT_EVALUATED",
        "external_environmental_and_future_harms": "NOT_EVALUATED",
        "real_world_application_allowed": False,
        "source_sha256": manifest["generated_source_sha256"],
        "seed_key": run_key,
        "compute_seconds": {k: round(v, 6) for k, v in costs.items()},
        "candidate_wins": sum(outcomes["candidate"]),
        "baseline_wins": {name: sum(outcomes[name]) for name in compared},
        "scientific_novelty_confirmed": False,
    })
    return result
