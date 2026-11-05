# AΩ | AI — Research Milestone 01

**Status:** planned / not executed.

## Research objective

Test whether a specified candidate search procedure finds feasible, Pareto-improving allocations more frequently or efficiently than standard optimization baselines, at matched computational cost.

## Formal acceptance criteria

For a candidate \(x\), baseline \(x_0\), utility functions \(u_i\), and hard constraints \(C(x)\):

1. \(C(x)=true\)
2. \(u_i(x)\ge u_i(x_0)\) for all \(i\)
3. \(u_j(x)>u_j(x_0)\) for at least one \(j\)

No improvement is asserted when the constraints exclude all viable alternatives.

## Experimental plan

1. Preregister datasets, random seeds, trial counts, thresholds and compute budgets.
2. Implement synthetic 2–5-agent environments with specified utility functions.
3. Measure random-search, weighted-sum and Pareto-frontier baselines.
4. Propose a candidate mechanism only if a testable gap can be identified.
5. Use held-out trials and report feasibility, per-agent deltas and compute.
6. Publish positive, null and negative results, independently reproducible.

## Measured results

**None yet.** The existing deterministic policy gate is not the candidate optimizer.

## Resource and safety constraints

No paid model API, new hosting spend or real-world autonomous action is required for this milestone. External actions must be authorized. Legal, privacy and stakeholder rights constraints cannot be traded away for an aggregate utility gain.

## Next deliverable

A published synthetic benchmark specification and reference baseline implementations.

Contact: **tasos.tsikriteas@gmail.com**
