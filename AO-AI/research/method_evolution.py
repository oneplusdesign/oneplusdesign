"""AΩ | AI — bounded evolution of compositional search methods.

The worker evolves safe, structured METHOD DATA, not executable source code.
Training selects a method and independent synthetic holdout tests its result.
This is known genetic-programming methodology; it proves no human benefit.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from random import Random
from statistics import mean

from benchmark import evaluate, pareto_improvement
from daily_study import candidate_bundles
from discovery import BASELINES, _paired_bootstrap_ci, evaluate_baseline, training_cases

FEATURES = ("minimum", "total", "positive", "harm", "losers", "spread")
WEIGHTS = (-2, -1, 1, 2)
PROPOSALS = ("local", "diverse", "alternate")
EXPLORERS = ("steady", "decay", "stagnation")
ANCHORS = ("best", "recent")


@dataclass(frozen=True)
class Recipe:
    features: tuple[str, ...]
    weights: tuple[int, ...]
    proposal: str
    explorer: str
    anchor: str

    def __post_init__(self):
        if (type(self.features) is not tuple or
            type(self.weights) is not tuple or
            not 1 <= len(self.features) <= 4 or
            len(self.weights) != len(self.features) or
            len(set(self.features)) != len(self.features) or
            any(f not in FEATURES for f in self.features) or
            any(type(w) is not int or w not in WEIGHTS for w in self.weights) or
            self.proposal not in PROPOSALS or
            self.explorer not in EXPLORERS or self.anchor not in ANCHORS):
            raise ValueError("Recipe is outside the fixed, safe grammar")

    @classmethod
    def from_data(cls, data: dict) -> "Recipe":
        if (type(data) is not dict or set(data) !=
                {"features", "weights", "proposal", "explorer", "anchor"} or
                type(data["features"]) not in (list, tuple) or
                type(data["weights"]) not in (list, tuple)):
            raise ValueError("Invalid JSON recipe schema")
        return cls(tuple(data["features"]), tuple(data["weights"]),
                   data["proposal"], data["explorer"], data["anchor"])

    def signature(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))


def random_recipe(rng: Random) -> Recipe:
    count = rng.randint(1, 3)
    return Recipe(
        tuple(rng.sample(FEATURES, count)),
        tuple(rng.choice(WEIGHTS) for _ in range(count)),
        rng.choice(PROPOSALS), rng.choice(EXPLORERS), rng.choice(ANCHORS),
    )


def mutate(recipe: Recipe, rng: Random) -> Recipe:
    """Grow, shrink or recombine method components, never edit source."""
    features, weights = list(recipe.features), list(recipe.weights)
    proposal, explorer, anchor = recipe.proposal, recipe.explorer, recipe.anchor
    change = rng.choice(("grow", "shrink", "feature", "weight", "proposal", "explorer", "anchor"))
    if change == "grow" and len(features) < 4:
        features.append(rng.choice([f for f in FEATURES if f not in features]))
        weights.append(rng.choice(WEIGHTS))
    elif change == "shrink" and len(features) > 1:
        index = rng.randrange(len(features))
        features.pop(index)
        weights.pop(index)
    elif change == "feature":
        index = rng.randrange(len(features))
        features[index] = rng.choice([f for f in FEATURES if f not in features])
    elif change in ("weight", "grow", "shrink"):
        index = rng.randrange(len(features))
        weights[index] = rng.choice([w for w in WEIGHTS if w != weights[index]])
    elif change == "proposal":
        proposal = rng.choice([x for x in PROPOSALS if x != proposal])
    elif change == "explorer":
        explorer = rng.choice([x for x in EXPLORERS if x != explorer])
    else:
        anchor = rng.choice([x for x in ANCHORS if x != anchor])
    return Recipe(tuple(features), tuple(weights), proposal, explorer, anchor)


def score(gains: tuple[int, ...], recipe: Recipe) -> int:
    values = {
        "minimum": min(gains),
        "total": sum(gains),
        "positive": sum(max(0, g) for g in gains),
        "harm": sum(max(0, -g) for g in gains),
        "losers": sum(g < 0 for g in gains),
        "spread": max(gains) - min(gains),
    }
    return sum(values[k] * w for k, w in zip(recipe.features, recipe.weights))


def run_recipe(case, recipe: Recipe, budget: int, seed: int) -> dict:
    if not 1 <= budget <= 200:
        raise ValueError("Invalid research evaluation budget")
    rng = Random(seed)
    options = candidate_bundles(case)
    seen: dict[tuple[str, ...], tuple[int, ...]] = {}
    recent = None
    best = None
    stalled = 0
    found = None
    for step in range(min(budget, len(options))):
        available = [x for x in options if x not in seen]
        if recipe.explorer == "steady":
            explore = 0.20
        elif recipe.explorer == "decay":
            explore = 0.4 * (1 - step / max(1, budget))
        else:
            explore = 0.65 if stalled >= 3 else 0.1
        if not seen or rng.random() < explore:
            chosen = rng.choice(available)
        else:
            base = (max(seen, key=lambda x: (score(seen[x], recipe), x))
                    if recipe.anchor == "best" else recent)
            pool = rng.sample(available, min(12, len(available)))
            distance = lambda x, y: len(set(x).symmetric_difference(y))
            if (recipe.proposal == "local" or
                (recipe.proposal == "alternate" and step % 2 == 0)):
                chosen = min(pool, key=lambda x: (distance(x, base), x))
            else:
                chosen = max(pool, key=lambda x: (
                    min(distance(x, s) for s in seen), distance(x, base), x))
        outcome = evaluate(case, chosen)
        if outcome is None:
            raise AssertionError("Generated action is not feasible")
        seen[chosen], recent = outcome.gains, chosen
        value = score(outcome.gains, recipe)
        if best is None or value > best:
            best, stalled = value, 0
        else:
            stalled += 1
        if found is None and pareto_improvement(outcome):
            found = step + 1
    return {"found": found is not None, "first_found_at": found,
            "objective_calls": len(seen)}


def evaluate_recipe(recipe: Recipe, cases: list, budget: int, seed: int) -> list[int]:
    return [int(run_recipe(case, recipe, budget, seed + i * 1009)["found"])
            for i, case in enumerate(cases)]


def evolve_method(run_key: int, inherited: Recipe | None = None,
                  *, train_count: int = 20, holdout_count: int = 60,
                  budget: int = 12, population: int = 6, generations: int = 3) -> dict:
    """Select on training data only; freeze; test once on separate holdout."""
    if (type(run_key) is not int or run_key < 0 or
        min(train_count, holdout_count, budget, population, generations) < 1 or
        train_count > 2000 or holdout_count > 4000 or
        budget > 200 or population > 60 or generations > 50 or
        (inherited is not None and type(inherited) is not Recipe)):
        raise ValueError("Invalid bounded study parameters")
    rng = Random(run_key)
    train = list(training_cases(run_key * 3 + 100001, train_count))
    holdout = list(training_cases(run_key * 3 + 3000001, holdout_count))
    paired_seed = run_key * 17 + 77
    pool = [inherited] if inherited is not None else []
    while len(pool) < population:
        pool.append(random_recipe(rng))
    scored: dict[str, tuple[int, Recipe]] = {}
    grown = 0
    for _ in range(generations):
        for candidate in pool:
            sig = candidate.signature()
            if sig not in scored:
                scored[sig] = (
                    sum(evaluate_recipe(candidate, train, budget, paired_seed)), candidate
                )
        ordered = sorted(scored.values(), key=lambda x: (
            -x[0], -int(x[1] == inherited), x[1].signature()
        ))
        leaders = [x[1] for x in ordered[:2]]
        pool = [leaders[0]]
        while len(pool) < population:
            parent = rng.choice(leaders)
            child = mutate(parent, rng)
            grown += int(len(child.features) > len(parent.features))
            pool.append(child)
    selected_score, selected = sorted(scored.values(), key=lambda x: (
        -x[0], -int(x[1] == inherited), x[1].signature()
    ))[0]
    prior_score = (sum(evaluate_recipe(inherited, train, budget, paired_seed))
                   if inherited is not None else None)
    training_baselines = {
        name: sum(evaluate_baseline(name, train, budget, paired_seed))
        for name in BASELINES
    }
    baseline_name = max(
        BASELINES, key=lambda name: (training_baselines[name], -BASELINES.index(name))
    )
    candidate_holdout = evaluate_recipe(selected, holdout, budget, paired_seed)
    baseline_holdout = evaluate_baseline(
        baseline_name, holdout, budget, paired_seed
    )
    ci = _paired_bootstrap_ci(candidate_holdout, baseline_holdout, run_key + 553)
    return {
        "experiment": "compositional_method_evolution",
        "status": "exploratory_not_confirmatory",
        "synthetic_only": True, "run_key": run_key,
        "methods_evaluated": len(scored),
        "growth_mutations": grown,
        "recipe": asdict(selected),
        "selected_component_count": len(selected.features),
        "training_cases": train_count,
        "training_successes": selected_score,
        "inherited_training_successes": prior_score,
        "training_gain_over_inherited": (
            selected_score - prior_score if prior_score is not None else None
        ),
        "baseline_selected_on_training": baseline_name,
        "holdout_cases": holdout_count,
        "holdout_successes": sum(candidate_holdout),
        "holdout_baseline_successes": sum(baseline_holdout),
        "holdout_delta": round(mean(a - b for a, b in zip(
            candidate_holdout, baseline_holdout)), 4),
        "holdout_ci95": list(ci),
        "research_breakthrough_claim": False,
        "independent_replication": False,
        "real_world_benefit_verified": False,
        "source_code_modified_by_worker": False,
    }
