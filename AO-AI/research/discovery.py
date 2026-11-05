"""AΩ | AI — constrained automatic hypothesis search (research prototype).

The system generates and mutates *parameterized search policies*, compares
each against fixed reference baselines on TRAIN cases, freezes a candidate,
then evaluates it ONCE on disjoint HOLDOUT cases. It cannot modify its own
source, make API calls, or claim a scientific discovery.

This is established algorithm configuration, NOT a new field of AI research.
All environments are SYNTHETIC and all conclusions provisional.
Python standard library only.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import date
from hashlib import sha256
from itertools import combinations
import json
from math import exp, sqrt
from random import Random
from statistics import mean
from time import perf_counter

from benchmark import evaluate, pareto_improvement
from daily_study import candidate_bundles, generate_case, search

OBJECTIVES = ("sum", "min", "deficit", "blend", "product")
FAMILIES = ("mixed", "synergy", "scarcity", "balanced", "adversarial")
BASELINES = ("uniform_random", "weighted_local_search", "maximin_local_search")
DEFAULT_BUDGET = 12
POLICY_VERSION = 1


@dataclass(frozen=True)
class Hypothesis:
    """Restricted, auditable search-policy grammar; NEVER executable code."""
    objective: str
    radius: int
    explore: float
    tournament: int
    restart: int
    anchor: str

    def __post_init__(self):
        if (self.objective not in OBJECTIVES
            or self.radius not in (1, 2, 3, 4)
            or self.explore not in (0.0, 0.1, 0.25, 0.5)
            or self.tournament not in (1, 2, 4, 8)
            or self.restart not in (0, 5, 10)
            or self.anchor not in ("best", "recent")):
            raise ValueError("Invalid hypothesis: outside the safe policy grammar")

    def signature(self) -> str:
        return sha256(json.dumps(asdict(self), sort_keys=True).encode()).hexdigest()[:12]


def generate_hypothesis(rng: Random) -> Hypothesis:
    return Hypothesis(
        rng.choice(OBJECTIVES), rng.choice((1, 2, 3, 4)),
        rng.choice((0.0, 0.1, 0.25, 0.5)),
        rng.choice((1, 2, 4, 8)),
        rng.choice((0, 5, 10)),
        rng.choice(("best", "recent")),
    )


def mutate_hypothesis(policy: Hypothesis, rng: Random) -> Hypothesis:
    params = asdict(policy)
    keys = list(params)
    key = rng.choice(keys)
    values = {
        "objective": OBJECTIVES, "radius": (1, 2, 3, 4),
        "explore": (0.0, 0.1, 0.25, 0.5),
        "tournament": (1, 2, 4, 8), "restart": (0, 5, 10),
        "anchor": ("best", "recent"),
    }[key]
    alternatives = [x for x in values if x != params[key]]
    params[key] = rng.choice(alternatives)
    return Hypothesis(**params)


def _score(gains: tuple[int, ...], objective: str) -> tuple[float, float]:
    low = min(gains)
    total = sum(gains)
    if objective == "sum":
        return total, low
    if objective == "min":
        return low, total
    if objective == "deficit":
        return sum(min(0, v) for v in gains), low
    if objective == "blend":
        return 2 * low + total / len(gains), total
    # Positive shift is an objective *heuristic*, not a bargaining theorem.
    if objective == "product":
        product = 1.0
        for v in gains:
            product *= max(0.01, v + 8)
        return product, low
    raise ValueError("Unrecognized objective")


def run_hypothesis(case, policy: Hypothesis, budget: int, seed: int) -> dict:
    """Bounded black-box search; no access to hidden utility values."""
    if budget < 1:
        raise ValueError("budget must be positive")
    rng = Random(seed)
    options = candidate_bundles(case)
    targets = min(budget, len(options))
    seen = {}
    current = None
    first_found = None
    for attempt in range(targets):
        available = [x for x in options if x not in seen]
        if not seen or rng.random() < policy.explore or (
                policy.restart and attempt % policy.restart == 0):
            proposal = rng.choice(available)
        else:
            if policy.anchor == "best":
                base = max(seen, key=lambda x: _score(seen[x], policy.objective))
            else:
                base = current
            neighbors = [
                x for x in available
                if len(set(base).symmetric_difference(x)) <= policy.radius
            ]
            pool = neighbors if neighbors else available
            sample = rng.sample(pool, min(policy.tournament, len(pool)))
            # No lookahead / ground truth: candidate choice uses only distance
            # to promising observed configurations.
            proposal = min(
                sample,
                key=lambda x: (
                    len(set(base).symmetric_difference(x)),
                    abs(len(x) - len(base)),
                    x,
                ),
            )
        outcome = evaluate(case, proposal)
        if outcome is None:
            raise AssertionError("Generated infeasible candidate")
        seen[proposal] = outcome.gains
        current = proposal
        if first_found is None and pareto_improvement(outcome):
            first_found = attempt + 1
    return {
        "found": first_found is not None,
        "first_found_at": first_found,
        "objective_calls": len(seen),
    }


def training_cases(seed: int, n: int):
    """Synthetic instances with known separate seeds and regime labels."""
    for i in range(n):
        yield generate_case(seed, i, regime_override=FAMILIES[i % len(FAMILIES)])


def evaluate_policy(policy: Hypothesis, cases: list, budget: int, seed: int):
    # Deliberately fixed paired seeds for fair stochastic evaluation.
    results = []
    for i, case in enumerate(cases):
        r = run_hypothesis(case, policy, budget, seed + i * 1009)
        results.append(int(r["found"]))
    return results


def evaluate_baseline(method: str, cases: list, budget: int, seed: int):
    if method not in BASELINES:
        raise ValueError("Unknown baseline")
    return [
        int(search(case, candidate_bundles(case), method, budget,
                   seed + i * 1009)["found_mutual_gain"])
        for i, case in enumerate(cases)
    ]


def _paired_bootstrap_ci(candidate: list[int], baseline: list[int],
                         seed: int, replicates: int = 400):
    """Percentile CI for paired binary outcome difference (exploratory)."""
    if len(candidate) != len(baseline) or not candidate:
        raise ValueError("Paired observations required")
    rng = Random(seed)
    n = len(candidate)
    deltas = [a - b for a, b in zip(candidate, baseline)]
    samples = []
    for _ in range(replicates):
        samples.append(sum(deltas[rng.randrange(n)] for _ in range(n)) / n)
    samples.sort()
    return round(samples[int(0.025 * replicates)], 4), round(
        samples[min(replicates - 1, int(0.975 * replicates))], 4
    )


def discover(run_key: int, count_train: int = 40, count_holdout: int = 120,
             budget: int = DEFAULT_BUDGET, population: int = 8,
             generations: int = 3) -> dict:
    """Propose -> evaluate on train -> mutate -> freeze -> test held-out ONCE.

    This is not LLM-based code invention; proposals are generated within a
    pre-declared finite grammar. The holdout is never used for tuning this
    round, and repeated rounds are exploratory, not independent confirmation.
    """
    if (run_key < 0 or min(count_train, count_holdout, budget, population, generations) < 1
            or count_train > 2000 or count_holdout > 4000
            or budget > 200 or population > 100 or generations > 100):
        raise ValueError("Configuration is outside bounded study limits")
    rng = Random(run_key)
    train = list(training_cases(run_key * 2 + 100003, count_train))
    holdout = list(training_cases(run_key * 2 + 2000003, count_holdout))
    fixed_seed = run_key * 13 + 99
    champions = []
    checked = set()
    pool = [generate_hypothesis(rng) for _ in range(population)]
    candidate_evaluations = 0
    for gen in range(generations):
        scored = []
        for candidate in pool:
            sig = candidate.signature()
            if sig in checked:
                continue
            checked.add(sig)
            train_successes = evaluate_policy(candidate, train, budget, fixed_seed)
            candidate_evaluations += 1
            scored.append((sum(train_successes), sig, candidate))
        if not scored:
            break
        scored.sort(key=lambda x: (-x[0], x[1]))
        champions.extend(scored[:2])
        champions.sort(key=lambda x: (-x[0], x[1]))
        leaders = champions[:2]
        pool = [leaders[0][2]]
        while len(pool) < population:
            parent = rng.choice(leaders)[2]
            pool.append(mutate_hypothesis(parent, rng))

    if not champions:
        raise AssertionError("No generated hypotheses")
    selected = champions[0][2]  # Holdout remains unseen until selection.
    train_baselines = {
        m: sum(evaluate_baseline(m, train, budget, fixed_seed))
        for m in BASELINES
    }
    holdout_candidates = evaluate_policy(selected, holdout, budget, fixed_seed)
    holdout_baselines = {
        m: evaluate_baseline(m, holdout, budget, fixed_seed)
        for m in BASELINES
    }
    # Best baseline chosen by TRAIN performance, NOT the held-out responses.
    strongest_baseline = max(
        BASELINES, key=lambda m: (train_baselines[m], -BASELINES.index(m))
    )
    baseline = holdout_baselines[strongest_baseline]
    diff = mean(a - b for a, b in zip(holdout_candidates, baseline))
    lo, hi = _paired_bootstrap_ci(holdout_candidates, baseline, run_key + 9973)
    return {
        "method": "parameterized_candidate_generation_and_train_select_holdout_test",
        "research_status": "exploratory_not_confirmatory",
        "run_key": run_key,
        "synthetic_only": True,
        "hypotheses_evaluated": candidate_evaluations,
        "generated_policy": asdict(selected),
        "policy_signature": selected.signature(),
        "train_cases": len(train),
        "holdout_cases": len(holdout),
        "utility_queries_per_method_per_case": budget,
        "training_baselines_successes": train_baselines,
        "frozen_baseline_name": strongest_baseline,
        "holdout_candidate_successes": sum(holdout_candidates),
        "holdout_baselines_successes": {
            m: sum(outcomes) for m, outcomes in holdout_baselines.items()
        },
        "holdout_paired_rate_delta": round(diff, 4),
        "holdout_delta_bootstrap_ci95": [lo, hi],
        "baseline_beaten_on_holdout": lo > 0 and diff > 0,
        "independent_replication": False,
        "prior_art_novelty_verified": False,
        "research_breakthrough_claim": False,
        "caveats": [
            "Automatic configuration of predefined search components is established prior art.",
            "Only simulated utility changes and explicit feasibility are evaluated.",
            "Candidate policies are interpreted data, never executable generated code.",
            "Selecting across many holdout rounds would cause multiple-comparison bias.",
            "Holdout tests are exploratory: independent replication is not performed.",
            "Matched utility evaluation counts do not establish matched wall-clock cost.",
            "A single metric is not sufficient to validate common human benefit.",
        ],
    }
