"""AΩ | AI: transparent reference baselines for constrained multi-agent allocation.

All utility values and synergies in the demonstration are synthetic.
This is NOT an AI model, a novel algorithm, or a claim of real-world benefit.
Standard library only; Python 3.10+.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import combinations
from math import prod
from random import Random
import json


@dataclass(frozen=True)
class Action:
    name: str
    cost: int
    gains: tuple[int, ...]


@dataclass(frozen=True)
class Case:
    name: str
    stakeholders: tuple[str, ...]
    budget: int
    actions: tuple[Action, ...]
    # Pairwise interactions: (first action, second action, additional utility gains).
    interactions: tuple[tuple[str, str, tuple[int, ...]], ...] = ()


@dataclass(frozen=True)
class Outcome:
    actions: tuple[str, ...]
    cost: int
    gains: tuple[int, ...]


def evaluate(case: Case, selected: tuple[str, ...]) -> Outcome | None:
    """Return the exact synthetic outcome, or None if the budget is exceeded."""
    if len(set(selected)) != len(selected):
        raise ValueError("Duplicate actions are not allowed")
    names = {a.name for a in case.actions}
    if not set(selected).issubset(names):
        raise ValueError("Unknown action")
    chosen = tuple(a for a in case.actions if a.name in selected)
    cost = sum(a.cost for a in chosen)
    if cost > case.budget:
        return None
    gains = [0] * len(case.stakeholders)
    for a in chosen:
        if len(a.gains) != len(gains):
            raise ValueError("Invalid utility dimension")
        for i, amount in enumerate(a.gains):
            gains[i] += amount
    for left, right, interaction in case.interactions:
        if left in selected and right in selected:
            if len(interaction) != len(gains):
                raise ValueError("Invalid interaction dimension")
            for i, amount in enumerate(interaction):
                gains[i] += amount
    return Outcome(tuple(sorted(selected)), cost, tuple(gains))


def enumerate_feasible(case: Case) -> list[Outcome]:
    """Full enumeration is practical only for small synthetic cases."""
    results = []
    for n in range(len(case.actions) + 1):
        for group in combinations(case.actions, n):
            result = evaluate(case, tuple(a.name for a in group))
            if result is not None:
                results.append(result)
    return results


def pareto_improvement(outcome: Outcome) -> bool:
    """Improves >=1 stakeholder and harms none, against the zero-delta baseline."""
    return all(g >= 0 for g in outcome.gains) and any(g > 0 for g in outcome.gains)


def dominates(a: Outcome, b: Outcome) -> bool:
    return all(x >= y for x, y in zip(a.gains, b.gains)) and any(
        x > y for x, y in zip(a.gains, b.gains)
    )


def pareto_frontier(options: list[Outcome]) -> list[Outcome]:
    return [x for x in options if not any(dominates(y, x) for y in options)]


def display(outcome: Outcome | None) -> dict | None:
    return asdict(outcome) if outcome is not None else None


def benchmark(case: Case, seed: int = 7, random_budget: int = 8) -> dict:
    """Reference methods; exact baselines enumerate the full search space.

    The random baseline gets a fixed sample of proposals. These compute budgets
    are NOT comparable: this is infrastructure validation, not a performance study.
    """
    all_options = enumerate_feasible(case)
    improvements = [x for x in all_options if pareto_improvement(x)]
    weighted = max(
        all_options, key=lambda x: (sum(x.gains), min(x.gains), -x.cost)
    )
    maximin = max(
        all_options, key=lambda x: (min(x.gains), sum(x.gains), -x.cost)
    )
    strictly_positive = [x for x in all_options if all(g > 0 for g in x.gains)]
    nash = max(
        strictly_positive,
        key=lambda x: (prod(x.gains), sum(x.gains), -x.cost),
        default=None,
    )
    sampled = Random(seed).sample(all_options, min(random_budget, len(all_options)))
    sampled_improvements = [x for x in sampled if pareto_improvement(x)]
    return {
        "case": case.name,
        "synthetic": True,
        "stakeholders": case.stakeholders,
        "feasible_outcomes": len(all_options),
        "pareto_frontier_outcomes": len(pareto_frontier(all_options)),
        "mutual_gain_outcomes": len(improvements),
        "weighted_sum_exact": display(weighted),
        "maximin_exact": display(maximin),
        "nash_positive_exact": display(nash),
        "random_budget": len(sampled),
        "random_mutual_gain_found": len(sampled_improvements),
        "best_mutual_gain_example": display(
            max(improvements, key=lambda x: (min(x.gains), sum(x.gains))),
        ) if improvements else None,
        "interpretation": (
            "A known feasible mutual-gain option exists in this synthetic case."
            if improvements else
            "No mutual-gain option exists among the fully enumerated feasible options."
        ),
        "limitation": (
            "Illustrative exact enumeration and an unequal-budget random sample; "
            "no new optimizer, matched-budget evaluation or generalization claim."
        ),
    }


def cases() -> tuple[Case, Case]:
    cooperation = Case(
        name="composable_cooperation",
        stakeholders=("organization", "workers", "public"),
        budget=5,
        actions=(
            Action("automation", 2, (7, -5, -2)),
            Action("training", 2, (-2, 4, 1)),
            Action("revenue_sharing", 1, (-4, 5, 0)),
            Action("accessibility", 1, (-1, 0, 4)),
            Action("privacy_audit", 1, (-1, 0, 2)),
        ),
        interactions=(
            ("automation", "training", (1, 2, 2)),
            ("automation", "revenue_sharing", (2, 1, 1)),
        ),
    )
    zero_sum = Case(
        name="incompatible_zero_sum",
        stakeholders=("organization", "workers", "public"),
        budget=1,
        actions=(
            Action("shift_to_organization", 1, (2, -2, 0)),
            Action("shift_to_workers", 1, (0, 2, -2)),
            Action("shift_to_public", 1, (-2, 0, 2)),
        ),
    )
    return cooperation, zero_sum


def main() -> None:
    print(json.dumps([benchmark(c) for c in cases()], indent=2))


if __name__ == "__main__":
    main()
