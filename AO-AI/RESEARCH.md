# AΩ | AI — Experimental Evaluation Protocol

## Hypothesis

Investigate whether a precisely specified candidate mechanism can discover feasible Pareto improvements over baseline allocations more efficiently than strong standard baselines at **matched evaluation budgets**. No candidate method has been established and no superiority is claimed.

## Baseline methods

1. Uniform/random search, at a fixed number of utility evaluations.
2. Weighted-sum scalarization with documented weights.
3. Pareto frontier / ε-constraint approximation.
4. Nash bargaining objective as an additional reference where its assumptions apply.

## Test environment

- Synthetic allocations with 2–5 agents.
- Convex and non-convex feasible sets.
- Identical utility function access for all methods.
- Conflict, scarcity, asymmetry and no-mutual-gain instances.
- Independent random seeds and hold-out problem instances.

## Metrics

- Fraction of generated candidates satisfying feasibility constraints.
- Fraction that genuinely Pareto-improve upon \(x_0\).
- Per-agent utility deltas and the minimum delta.
- Pareto set coverage / hypervolume where applicable.
- Compute time, objective calls, and constraint violations.
- Uncertainty intervals and all negative outcomes.

## Failure-mode investigations

- Misreported preferences and incentives.
- Unobserved or excluded stakeholders.
- Incompatible constraints.
- Utility estimation errors and robust feasibility.
- Optimization gaming and benchmark contamination.
- Limits of synthetic evidence for real-world adoption.

## Status

The interactive interface currently demonstrates a deterministic **policy declaration gate**, not this research experiment. Tests for that component do not establish the hypothesis above. All new research claims must be reproducible.

Contact: **tasos.tsikriteas@gmail.com**
