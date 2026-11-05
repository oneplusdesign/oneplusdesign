# Research Prototype 01 — Constrained Multi-Stakeholder Allocation

**Status:** A reference benchmark, not a novel optimizer and not a multi-model AI system.

## Run

- Python 3.10+ (standard library only).
- Run the experiment: `python3 AO-AI/research/benchmark.py`
- Run the unit tests: `python3 -m unittest discover -s AO-AI/research -p 'test_*.py' -v`

## What the benchmark actually measures

Two deliberately small synthetic cases with three stakeholders each:

1. **Composable cooperation:** interventions have individual costs, individual utility effects, and pairwise interaction terms. Some combinations produce a feasible, mutually beneficial option.
2. **Incompatible zero-sum:** the budget permits only a single redistribution, each of which harms another participant; no Pareto improvement is possible.

Each subset of interventions is evaluated against a no-action baseline with zero gains. Feasibility is determined by the resource budget. A Pareto improvement is feasible and has all stakeholder utility changes nonnegative, with at least one strictly positive.

The reference solvers are exact enumeration with weighted total gain, maximin gain, Pareto-frontier enumeration, and the Nash product of strictly positive gains. A random-search sample is also shown **only as a sanity check**. The exact algorithms and sample do not share a matched compute budget, so the output **cannot demonstrate algorithmic superiority**. Nash, weighted-sum, maximin and Pareto methods are established tools.

All preferences, interventions and interactions are synthetic numbers; they cannot demonstrate actual social benefits.

## Next empirical milestone

- Generate hold-out synthetic cases with different objective landscapes, nonconvex feasible regions, constraints and strategic misreporting.
- Preregister a fixed objective-evaluation budget shared by all search algorithms.
- Add strong matching-budget baselines (including NSGA-II where appropriate).
- Build and describe a precise candidate hypothesis that differs materially from prior methods.
- Publish raw trial results, confidence intervals, resource counts and negative results.

Research correspondence: **tasos.tsikriteas@gmail.com**.
