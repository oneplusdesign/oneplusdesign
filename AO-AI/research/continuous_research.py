"""AΩ | AI — bounded series of consecutive synthetic experiments.

Each completed experiment is followed immediately by the next until the
wall-clock budget or 30-day research window expires. Scheduled GitHub-hosted
runners restart the session periodically. This is NOT a continuously thinking
AI system or a novel algorithm; no model APIs are invoked.

Checkpoint file stores aggregate reproducible counts, not identities or
actual-world claims. Run with --max-experiments 2 for a quick smoke test.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import date, datetime, timezone
import json
from pathlib import Path
import time

from daily_study import END, METHODS, START, run_study
from discovery import Hypothesis, discover
from interaction_integrity import experiment as integrity_experiment

def load_training_policy(path: Path | None) -> Hypothesis | None:
    """Read data only. Prior artifacts may seed TRAINING, never code or trust."""
    if path is None or not path.is_file() or path.stat().st_size > 1_000_000:
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict) or raw.get("synthetic_only") is not True:
            return None
        history = raw.get("research_hypothesis_outcomes", [])
        if not isinstance(history, list) or not history:
            return None
        candidate = history[-1].get("generated_policy")
        if not isinstance(candidate, dict):
            return None
        if set(candidate) != {
            "objective", "radius", "explore", "tournament", "restart", "anchor"
        }:
            return None
        return Hypothesis(**candidate)  # strict policy grammar validation
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return None


FAMILIES = ("mixed", "synergy", "scarcity", "balanced", "adversarial")
BUDGETS = (12, 24, 48)
CASES_PER_EXPERIMENT = 40


def _save_atomic(path: Path, report: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def run_series(run_date: date, run_key: int, duration_seconds: float = 0,
               max_experiments: int = 2, count: int = CASES_PER_EXPERIMENT,
               output: Path | None = None,
               resume: Path | None = None) -> dict:
    """Consecutive parameter-sweep research experiments; no idle waits.

    A zero max_experiments means unlimited iterations bounded by time.
    Time-driven execution must specify a positive duration.
    """
    if run_key < 0 or duration_seconds < 0 or max_experiments < 0 or count < 1:
        raise ValueError("Invalid run configuration")
    if max_experiments == 0 and duration_seconds == 0:
        raise ValueError("Unbounded run: specify a positive duration")
    prior_policy = load_training_policy(resume)
    report = {
        "prior_training_policy_loaded": prior_policy is not None,
        "status": "experiment_series",
        "run_date": str(run_date),
        "run_key": run_key,
        "window": {"start": str(START), "end": str(END)},
        "synthetic_only": True,
        "no_model_api": True,
        "candidate_research_algorithm_implemented": False,
        "research_breakthrough_claim": False,
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "executed": False,
        "completed_experiments": 0,
        "total_synthetic_cases": 0,
        "parameter_sweep": {},
        "research_hypothesis_rounds": 0,
        "research_hypothesis_outcomes": [],
        "last_interaction_integrity_control": None,
        "limitations": [
            "Known baseline heuristics only; no AI researcher running on its own.",
            "Synthetic preferences cannot establish real-world human benefits.",
            "Equal utility-query counts do not establish equal total compute.",
            "Repeated simulation runs do not establish algorithmic novelty.",
            "Runs are periodically relaunched by GitHub; gaps are possible.",
        ],
    }
    if not START <= run_date <= END:
        report["status"] = "outside_30_day_window"
        if output:
            _save_atomic(output, report)
        return report
    report["executed"] = True
    start = time.monotonic()
    i = 0
    while True:
        if max_experiments and i >= max_experiments:
            break
        if i and duration_seconds and time.monotonic() - start >= duration_seconds:
            break
        # Each run key is unique to a GitHub Actions invocation. Each experiment
        # chooses distinct deterministic inputs and cycles through research regimes.
        family = FAMILIES[i % len(FAMILIES)]
        budget = BUDGETS[(i // len(FAMILIES)) % len(BUDGETS)]
        experiment_id = run_key * 100000 + i
        outcome = run_study(
            run_date, count=count, budget=budget,
            experiment_id=experiment_id, regime=family,
        )
        if not outcome["executed"]:
            raise AssertionError("Research window invariant")
        key = f"{family}:budget_{budget}"
        segment = report["parameter_sweep"].setdefault(key, {
            "synthetic_cases": 0,
            "solvable_cases": 0,
            "unsolvable_cases": 0,
            "experiments": 0,
            "mutual_gain_found": {m: 0 for m in METHODS},
        })
        segment["synthetic_cases"] += outcome["synthetic_cases"]
        segment["solvable_cases"] += outcome["cases_with_possible_mutual_gain"]
        segment["unsolvable_cases"] += outcome["cases_with_no_mutual_gain_possible"]
        segment["experiments"] += 1
        for method in METHODS:
            segment["mutual_gain_found"][method] += outcome["matched_budget_references"][method]["cases_where_found_mutual_gain"]
        i += 1
        report["completed_experiments"] = i
        report["total_synthetic_cases"] += count
        if i % 5 == 0:
            # A separate honesty / autonomy / correction instrumentation
            # control. This cannot attest to real model behavior.
            report["last_interaction_integrity_control"] = integrity_experiment(
                seed=run_key * 100000 + i, repeats=3
            )
            research = discover(
                run_key=run_key * 100000 + i,
                count_train=40, count_holdout=120, budget=12,
                population=8, generations=3, seed_hypothesis=prior_policy,
            )
            prior_policy = Hypothesis(**research["generated_policy"])
            report["research_hypothesis_rounds"] += 1
            report["research_hypothesis_outcomes"].append({
                "round": i,
                "policy_signature": research["policy_signature"],
                "inherited_training_policy_signature": research["inherited_training_policy_signature"],
                "generated_policy": research["generated_policy"],
                "hypotheses_evaluated": research["hypotheses_evaluated"],
                "frozen_baseline_name": research["frozen_baseline_name"],
                "holdout_paired_rate_delta": research["holdout_paired_rate_delta"],
                "holdout_delta_bootstrap_ci95": research["holdout_delta_bootstrap_ci95"],
                "research_breakthrough_claim": False,
                "independent_replication": False,
            })
            # Include only a bounded recent activity trail; full history is not
            # preserved across runs and repeated holdout scoring is exploratory.
            report["research_hypothesis_outcomes"] = report["research_hypothesis_outcomes"][-25:]
        # Intermediate, atomic results preserve progress if a later iteration fails.
        if output and (i <= 2 or i % 25 == 0):
            report["finished_utc"] = datetime.now(timezone.utc).isoformat()
            _save_atomic(output, report)
    report["status"] = "completed_series"
    report["finished_utc"] = datetime.now(timezone.utc).isoformat()
    report["wall_clock_seconds"] = round(time.monotonic() - start, 3)
    if output:
        _save_atomic(output, report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-date", default=str(datetime.now(timezone.utc).date()))
    parser.add_argument("--run-key", type=int, default=1)
    parser.add_argument("--duration-seconds", type=float, default=0)
    parser.add_argument("--max-experiments", type=int, default=2)
    parser.add_argument("--count", type=int, default=CASES_PER_EXPERIMENT)
    parser.add_argument("--output", default="ao-research-series.json")
    parser.add_argument("--resume", type=Path)
    args = parser.parse_args()
    report = run_series(
        date.fromisoformat(args.run_date), run_key=args.run_key,
        duration_seconds=args.duration_seconds,
        max_experiments=args.max_experiments,
        count=args.count, output=Path(args.output), resume=args.resume,
    )
    print(json.dumps({
        "status": report["status"],
        "completed_experiments": report["completed_experiments"],
        "total_synthetic_cases": report["total_synthetic_cases"],
        "research_breakthrough_claim": False,
        "output": args.output,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
