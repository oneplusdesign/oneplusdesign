"""Experimental, non-deployable Pareto-archive local search (synthetic only).

This module is intentionally isolated from verification_gate.py and all
promotion, GitHub workflow, and real-world permissions. Archive-based search
is established prior art; the test here is a falsifiable *application* to the
existing constrained synthetic three-stakeholder benchmark.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from random import Random
from statistics import mean
from time import perf_counter

from benchmark import evaluate, pareto_improvement
from daily_study import candidate_bundles, generate_case, search

REGIMES = ("mixed", "synergy", "scarcity", "balanced", "adversarial")
BASELINES = ("uniform_random", "weighted_local_search", "maximin_local_search")


def dominates_vector(a: tuple[int, ...], b: tuple[int, ...]) -> bool:
    """Strict Pareto dominance on observed synthetic utility vectors only."""
    if len(a) != len(b) or not a:
        raise ValueError("Utility vectors must have equal positive dimensions")
    return all(x >= y for x, y in zip(a, b)) and any(
        x > y for x, y in zip(a, b)
    )


def add_to_archive(archive: list[tuple[str, ...]],
                   observed: dict[tuple[str, ...], tuple[int, ...]],
                   candidate: tuple[str, ...]) -> bool:
    """Maintain non-dominated, unique observed vectors; no oracle access."""
    gains = observed[candidate]
    if any(observed[x] == gains or dominates_vector(observed[x], gains)
           for x in archive):
        return False
    archive[:] = [x for x in archive if not dominates_vector(gains, observed[x])]
    archive.append(candidate)
    return True


def archive_search(case, options: list[tuple[str, ...]], budget: int,
                   seed: int, *, use_archive: bool = True) -> dict:
    """Archive-guided, fixed-query local search; all outcomes remain hidden until evaluated.

    Pre-registered rule: start at empty bundle; rotate non-dominated parents;
    try distance<=2 local neighbors; explore randomly each fifth query or
    after four archive stagnations. Ablation uses a single maximin parent.
    """
    if type(budget) is not int or not 1 <= budget <= 200:
        raise ValueError("Research query budget outside 1..200")
    if type(seed) is not int or seed < 0:
        raise ValueError("Invalid deterministic seed")
    if not options or len(options) != len(set(options)):
        raise ValueError("Feasible options must be nonempty and unique")
    rng = Random(seed)
    observed: dict[tuple[str, ...], tuple[int, ...]] = {}
    archive: list[tuple[str, ...]] = []
    stalled = 0
    first_found = None
    targets = min(budget, len(options))
    for step in range(targets):
        available = [x for x in options if x not in observed]
        if not observed:
            chosen = () if () in available else rng.choice(available)
        elif step % 5 == 0 or stalled >= 4:
            chosen = rng.choice(available)
        else:
            if use_archive:
                # Rotate through distinct non-dominated observed trade-offs.
                parents = sorted(archive, key=lambda x: (
                    min(observed[x]), sum(observed[x]), x), reverse=True)
                base = parents[step % len(parents)]
            else:
                base = max(observed, key=lambda x: (
                    min(observed[x]), sum(observed[x]), x))
            distance = lambda x: len(set(x).symmetric_difference(base))
            nearby = [x for x in available if 0 < distance(x) <= 2]
            pool = nearby if nearby else available
            sample = rng.sample(pool, min(12, len(pool)))
            chosen = min(sample, key=lambda x: (
                distance(x), abs(len(x) - len(base)), x))
        outcome = evaluate(case, chosen)
        if outcome is None:
            raise AssertionError("Hard feasibility constraint violated")
        observed[chosen] = outcome.gains
        if add_to_archive(archive, observed, chosen):
            stalled = 0
        else:
            stalled += 1
        if first_found is None and pareto_improvement(outcome):
            first_found = step + 1
    if any(dominates_vector(observed[a], observed[b])
           for a in archive for b in archive if a != b):
        raise AssertionError("Internal archive dominance invariant failed")
    return {
        "found": first_found is not None,
        "first_found_at": first_found,
        "objective_calls": len(observed),
        "archive_size": len(archive),
        "archive_vectors": [observed[x] for x in archive],
        "hard_constraint_violations": 0,
    }


def paired_seed_block_bootstrap(candidate: list[int], baseline: list[int],
                                block_ids: list[int], seed: int,
                                replicates: int = 2000) -> tuple[float, float]:
    """Paired cluster bootstrap by *seed block* (five clusters, wide CI)."""
    if not candidate or len(candidate) != len(baseline) or len(candidate) != len(block_ids):
        raise ValueError("Complete paired observations required")
    blocks = sorted(set(block_ids))
    if len(blocks) < 2 or replicates < 100:
        raise ValueError("Insufficient clusters or replicates")
    by_block = [[a - b for a, b, c in zip(candidate, baseline, block_ids)
                 if c == block] for block in blocks]
    if any(not x for x in by_block):
        raise ValueError("Empty block")
    rng = Random(seed)
    estimates = []
    for _ in range(replicates):
        sample = [by_block[rng.randrange(len(blocks))] for _ in blocks]
        estimates.append(sum(map(sum, sample)) / sum(map(len, sample)))
    estimates.sort()
    return (round(estimates[int(0.025 * replicates)], 4),
            round(estimates[min(replicates - 1, int(0.975 * replicates))], 4))


def compare(*, seed_key: int = 20261107, cases_per_seed: int = 200,
            seeds: int = 5, budget: int = 12) -> dict:
    """Frozen paired comparison; holdout is exploratory, never a promotion gate.

    No training or model selection is done using these observations.
    Equal *objective queries* are enforced; wall time is reported separately.
    """
    if (type(seed_key) is not int or seed_key < 0 or
            type(cases_per_seed) is not int or not 1 <= cases_per_seed <= 200 or
            type(seeds) is not int or not 2 <= seeds <= 10 or
            type(budget) is not int or not 1 <= budget <= 200):
        raise ValueError("Outside bounded experiment limits")
    methods = ("archive_guided", "single_anchor_ablation") + BASELINES
    observations = {m: [] for m in methods}
    seconds = {m: 0.0 for m in methods}
    block_ids = []
    violations = 0
    by_regime = {r: {m: [] for m in methods} for r in REGIMES}
    # Each block has distinct cases; same case and stochastic seed for methods.
    for block in range(seeds):
        case_seed = seed_key * 65537 + block * 104729 + 71
        for idx in range(cases_per_seed):
            regime = REGIMES[idx % len(REGIMES)]
            case = generate_case(case_seed, idx, regime_override=regime)
            options = candidate_bundles(case)
            shared_seed = case_seed * 17 + idx * 1009
            methods_to_run = {
                "archive_guided": lambda: archive_search(case, options, budget, shared_seed),
                "single_anchor_ablation": lambda: archive_search(
                    case, options, budget, shared_seed, use_archive=False),
                **{m: (lambda name=m: search(case, options, name, budget, shared_seed))
                   for m in BASELINES},
            }
            # Rotate evaluation order to reduce one-sided CPU cache/warmup bias.
            ordered = list(methods)
            shift = (block * cases_per_seed + idx) % len(ordered)
            ordered = ordered[shift:] + ordered[:shift]
            for method in ordered:
                start = perf_counter()
                result = methods_to_run[method]()
                seconds[method] += max(perf_counter() - start, 1e-12)
                if result["objective_calls"] != min(budget, len(options)):
                    raise AssertionError("Mismatched objective evaluation budget")
                violations += result.get("hard_constraint_violations", 0)
                found = int(bool(result.get("found", result.get("found_mutual_gain", False))))
                observations[method].append(found)
                by_regime[regime][method].append(found)
            block_ids.append(block)
    if violations:
        raise AssertionError("Hard constraints violated")
    candidate = observations["archive_guided"]
    comparisons = {}
    for method in methods[1:]:
        baseline = observations[method]
        comparisons[method] = {
            "successes": sum(baseline),
            "delta_pp": round(100 * mean(a - b for a, b in zip(candidate, baseline)), 3),
            "seed_block_bootstrap_ci95_pp": [
                round(100 * x, 3) for x in paired_seed_block_bootstrap(
                    candidate, baseline, block_ids, seed_key + 333)],
            "compute_ratio": round(seconds["archive_guided"] / seconds[method], 4),
            "regime_deltas_pp": {
                regime: round(100 * mean(a - b for a, b in zip(
                    by_regime[regime]["archive_guided"],
                    by_regime[regime][method])), 3)
                for regime in REGIMES
            },
        }
    return {
        "experiment": "experimental_archive_guided_search_vs_fixed_references",
        "status": "exploratory_only_no_promotion",
        "synthetic_only": True,
        "seed_key": seed_key,
        "seed_blocks": seeds,
        "cases_per_seed": cases_per_seed,
        "heldout_cases": seeds * cases_per_seed,
        "objective_evaluations_per_method_per_case": budget,
        "candidate_successes": sum(candidate),
        "comparisons": comparisons,
        "cpu_seconds_by_method": {k: round(v, 6) for k, v in seconds.items()},
        "hard_constraint_violations": violations,
        "source_changes_to_safety_gate": False,
        "independent_replication": False,
        "scientific_novelty_confirmed": False,
        "real_world_application_allowed": False,
        "unmodeled_people_life_ecosystems_future": "NOT_EVALUATED",
        "limitations": [
            "Archive-based local search is established prior art, not a novel algorithm.",
            "Only three synthetic stakeholders; real-world use is prohibited.",
            "Only five seed blocks: cluster-bootstrap confidence is imprecise.",
            "Repeated inspection of heldout results invalidates confirmatory inference.",
            "Wall times include Python overhead and depend on runner hardware.",
            "This experiment does not alter the independent promotion gate.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-key", type=int, default=20261107)
    parser.add_argument("--cases-per-seed", type=int, default=200)
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--budget", type=int, default=12)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = compare(seed_key=args.seed_key, cases_per_seed=args.cases_per_seed,
                     seeds=args.seeds, budget=args.budget)
    rendered = json.dumps(report, sort_keys=True, indent=2) + "\n"
    print(rendered)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    main()
