"""AΩ | AI: thirty-day, reproducible synthetic baseline study.

This module DOES NOT invent or operate a new AI model.
All utilities are synthetic; no real-world welfare result is asserted.
Only the Python standard library is used.

Pre-registered initial study: 80 generated cases/day, three stakeholders,
eight actions, budget up to four actions, 24 distinct objective calls/method.
The study uses a different deterministic seed per calendar day. It records
reference algorithm statistics; there is NO automatic discovery flag.
"""
from __future__ import annotations

import argparse
from datetime import date
from itertools import combinations
import json
from pathlib import Path
from random import Random

from benchmark import Action, Case, evaluate, pareto_improvement

START = date(2026, 11, 6)
END = date(2026, 12, 5)
CASES_PER_DAY = 80
EVALUATION_BUDGET = 24
METHODS = ("uniform_random", "weighted_local_search", "maximin_local_search")


def generate_case(seed: int, index: int, regime_override: str | None = None) -> Case:
    rng = Random(seed * 131071 + index)
    regime = regime_override or ("mixed", "synergy", "scarcity", "mixed")[index % 4]
    if regime not in ("mixed", "synergy", "scarcity", "balanced", "adversarial"):
        raise ValueError("Unknown synthetic case family")
    actions = []
    for j in range(8):
        gains = [rng.randint(-5, 6) for _ in range(3)]
        if regime == "balanced":
            gains = [rng.randint(-3, 3) for _ in range(3)]
        if regime == "adversarial":
            gains = [rng.randint(-7, 3) for _ in range(3)]
        if regime == "scarcity":
            # Conserve total utility across the three agents.
            gains[2] = -gains[0] - gains[1]
        actions.append(Action("action_%s" % j, 1, tuple(gains)))
    interactions = []
    if regime in ("mixed", "synergy"):
        for left, right in combinations(actions, 2):
            if rng.random() < 0.24:
                values = tuple(rng.randint(-1, 5) for _ in range(3))
                interactions.append((left.name, right.name, values))
    return Case(
        name="case_%03d_%s" % (index, regime),
        stakeholders=("stakeholder_A", "stakeholder_B", "stakeholder_C"),
        budget=4,
        actions=tuple(actions),
        interactions=tuple(interactions),
    )


def candidate_bundles(case: Case) -> list[tuple[str, ...]]:
    """Feasible proposals can be generated from known costs WITHOUT utility queries."""
    names = [a.name for a in case.actions]
    costs = {a.name: a.cost for a in case.actions}
    return [
        subset
        for r in range(len(names) + 1)
        for subset in combinations(names, r)
        if sum(costs[a] for a in subset) <= case.budget
    ]


def utility_score(gains: tuple[int, ...], method: str) -> tuple[int, int]:
    if method == "weighted_local_search":
        return sum(gains), min(gains)
    if method == "maximin_local_search":
        return min(gains), sum(gains)
    raise ValueError("Not a local search method: " + method)


def search(case: Case, options: list[tuple[str, ...]], method: str,
           budget: int, seed: int) -> dict:
    """Evaluate no more than budget distinct candidates.

    Random search and two established local-search objective functions are
    matched for total evaluated outcomes. Feasible candidate generation is
    equal and free of utility access for all methods. No method sees the
    ground-truth results before selection.
    """
    rng = Random(seed)
    seen: dict[tuple[str, ...], tuple[int, ...]] = {}
    current = ()
    targets = min(budget, len(options))
    while len(seen) < targets:
        untested = [x for x in options if x not in seen]
        if method == "uniform_random":
            proposal = rng.choice(untested)
        else:
            if len(seen) == 0:
                proposal = ()
            elif len(seen) % 7 == 0:
                # A small randomized exploration move to escape local traps.
                proposal = rng.choice(untested)
            else:
                nearby = [
                    x for x in untested
                    if len(set(current).symmetric_difference(x)) <= 2
                ]
                proposal = rng.choice(nearby if nearby else untested)
        result = evaluate(case, proposal)
        if result is None:
            raise AssertionError("Candidate feasibility invariant broken")
        seen[proposal] = result.gains
        if method != "uniform_random":
            current_score = utility_score(seen[current], method) if current in seen else (-10**9, -10**9)
            if utility_score(result.gains, method) > current_score:
                current = proposal
    successful = [g for g in seen.values() if all(x >= 0 for x in g) and any(x > 0 for x in g)]
    return {
        "objective_calls": len(seen),
        "found_mutual_gain": bool(successful),
        "feasible_proposals": len(seen),
    }


def run_study(run_date: date, count: int = CASES_PER_DAY,
              budget: int = EVALUATION_BUDGET, experiment_id: int = 0,
              regime: str | None = None) -> dict:
    if not START <= run_date <= END:
        return {
            "status": "outside_30_day_window",
            "run_date": str(run_date),
            "executed": False,
            "research_breakthrough_claim": False,
        }
    if experiment_id < 0:
        raise ValueError("experiment_id must be nonnegative")
    if regime is not None and regime not in ("mixed", "synergy", "scarcity", "balanced", "adversarial"):
        raise ValueError("Unknown synthetic case family")
    if count < 1 or budget < 1:
        raise ValueError("Count and budget must both be positive")
    date_seed = int(run_date.strftime("%Y%m%d")) * 1000003 + experiment_id * 104729
    tally = {m: 0 for m in METHODS}
    possible = 0
    cases_with_no_solution = 0
    for index in range(count):
        case = generate_case(date_seed, index, regime_override=regime)
        options = candidate_bundles(case)
        # Exhaustive truth is computed ONLY for the final scoring oracle,
        # never supplied to search methods. It does not represent equal
        # total compute cost and should not be used for speed comparisons.
        oracle_possible = any(
            pareto_improvement(evaluate(case, option)) for option in options
        )
        possible += int(oracle_possible)
        cases_with_no_solution += int(not oracle_possible)
        for method in METHODS:
            result = search(
                case, options, method, budget,
                seed=date_seed * 31 + index * 101 + METHODS.index(method),
            )
            if result["objective_calls"] != min(budget, len(options)):
                raise AssertionError("Mismatched evaluation budget")
            tally[method] += int(result["found_mutual_gain"] and oracle_possible)
    return {
        "status": "baseline_observation_only",
        "run_date": str(run_date),
        "executed": True,
        "deterministic_seed": date_seed,
        "experiment_id": experiment_id,
        "synthetic_family": regime or "mixed_regimes",
        "synthetic_cases": count,
        "objective_evaluations_per_method_per_case": budget,
        "cases_with_possible_mutual_gain": possible,
        "cases_with_no_mutual_gain_possible": cases_with_no_solution,
        "matched_budget_references": {
            method: {
                "cases_where_found_mutual_gain": tally[method],
                "discovery_rate_among_solvable_cases":
                round(tally[method] / possible, 4) if possible else None,
            }
            for method in METHODS
        },
        "candidate_research_algorithm_implemented": False,
        "independent_replication": False,
        "research_breakthrough_claim": False,
        "limitations": [
            "Synthetic utility functions do not establish actual human welfare.",
            "Reference local searches are established heuristic ideas, not novelty.",
            "The scoring oracle exhaustively searches for evaluation only.",
            "Matched utility-query counts do not establish matched wall-clock cost.",
            "No claim of generalization, external validation or scientific breakthrough.",
        ],
        "contact": "tasos.tsikriteas@gmail.com",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-date", default=str(date.today()))
    parser.add_argument("--output")
    parser.add_argument("--count", type=int, default=CASES_PER_DAY)
    args = parser.parse_args()
    output = run_study(date.fromisoformat(args.run_date), count=args.count)
    rendered = json.dumps(output, sort_keys=True, indent=2) + "\n"
    print(rendered)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    main()
