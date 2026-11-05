# AΩ | AI — Automatic Research Hypothesis Cycle (v0.1)

## Method

The scheduled worker now does more than rerun baseline examples. Every five short baseline experiments, it:

1. **Proposes** an initial population of bounded, machine-readable optimizer policies; policy attributes include objective function, neighbor search radius, exploration rate, tournament size, restart interval and incumbent selection.
2. **Evaluates** each proposal on synthetic **training** environments only.
3. **Mutates** the best training candidates, then reevaluates; this is standard evolutionary algorithm configuration.
4. **Freezes** the selected policy and strongest **training-selected** baseline.
5. **Tests once** on disjoint synthetic **holdout** environments with matched objective-query budgets.
6. **Stores** per-round candidate configuration, the holdout paired difference and exploratory 95% bootstrap confidence interval, including negative and null outcomes.

## Scientific limitations

- This is a **real, executable automatic hypothesis/configuration loop**, not an independently thinking model, self-modifying source-code agent or original algorithmic invention. It implements known techniques of genetic tuning and search.
- It generates **structured candidate policies** only; it does not generate arbitrary executable Python or call paid external AI models.
- The current synthetic problems are small and defined by humans. No actual human utility is measured.
- Holdout cases are not used inside a round to select a policy. However repeated rounds are exploratory and cannot be considered independent confirmatory evidence.
- Objective calls are matched, but CPU work may differ; compute-cost comparison remains required.
- No code paths set `research_breakthrough_claim` to true. Even a promising result requires literature review, strong baselines, replication across 1,000+ independent instances and independent scientific scrutiny.
- The 30-day GitHub Actions schedule is a bounded trial; on its own it does not guarantee continuous uptime or novel discoveries.

## Related prior art

- Google DeepMind's AlphaEvolve (2025): multi-model algorithm evolution with automated evaluators. https://deepmind.google/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/
- Irace: iterated racing for automatic algorithm configuration. https://mlopez-ibanez.github.io/irace/
- Rook et al., MO-SMAC (2026): multiobjective sequential model-based algorithm configuration. https://doi.org/10.1162/evco_a_00371

These approaches demonstrate that algorithmic hypothesis generation and tuning are active research fields, **not new inventions of AΩ**.

Research contact: tasos.tsikriteas@gmail.com
