# AΩ — Isolated archive-guided Pareto local-search experiment

**Experimental, review-only; not a new scientific result or approved for deployment.**
Only new files under AO-AI/research are proposed. No existing safety gates,
permissions, schedules, workflow code, model weights, or main-branch files change.

## Good-of-All assessment (required first)

The synthetic benchmark has exactly **three artificial stakeholders** and
a hard action-cost budget. Real people (present and future), other life,
ecosystems, indirect effects and unmodeled interests are **unknown**.
Those unknowns prohibit real-world application. No external actuators,
auto-merge, autonomous deployment or self-evaluation gate changes are present.
Synthetic Pareto improvement is not evidence of human or ecological benefit.

## Why test a different operator?

Inspected GitHub run [42333012455](https://github.com/oneplusdesign/oneplusdesign/actions/runs/42333012455),
dated 2026-11-07 03:13 UTC, including actual verification.json,
champion.json and cycle.json. The 1,000-case generated-code candidate
found 517 improvements versus maximin 545 and weighted local search 558.
The gate decision was **REJECT**, with champion generation 0.
Green CI means the pipeline executed; it does not mean the algorithm improved.

## Frozen falsifiable hypothesis (before testing)

H1: an archive of **observed** non-dominated utility vectors, rotated as
local-search parents, plus stagnation-triggered exploration will discover
more feasible no-harm Pareto improvements than a single-maximin-parent
ablation and three existing reference heuristics under 12 objective queries
per case. Strong support would require >5 percentage points over **each**
comparator, paired 95% bootstrap lower bound >0, no regression in any
regime, zero hard-constraint violations and comparable actual CPU compute.

Mechanism: first evaluate the empty bundle; maintain a non-dominated
archive from *previously queried* utilities only; rotate parents; choose
untested feasible distance<=2 neighbors; explore randomly each fifth
query or after four stagnant archive updates. Ablation selects one
maximin parent with otherwise matching rules. No lookahead, oracle
access, paid model API or real-world operation.

## Reproduction

Run from repository root with Python 3.10+ (standard library only):

    python3 -m unittest discover -s AO-AI/research -p 'test_*.py' -q
    python3 AO-AI/research/pareto_archive_trial.py \
      --seed-key 20261107 --seeds 5 --cases-per-seed 200 --budget 12 \
      --output pareto-archive-report.json

The second command creates 1,000 **newly seeded synthetic cases** in
five independent generator seed blocks and five regimes (mixed, synergy,
scarcity, balanced, adversarial), using matched case and stochastic seed.
Each method is checked to make exactly 12 objective evaluations per case.
Comparators: uniform random, weighted local, maximin local and the
single-parent ablation. Execution order rotates; measured Python wall
time is reported separately. Paired 95% CIs resample whole seed blocks
(not individual cases). Five clusters make the CI imprecise.

Unit tests include negative scarcity cases (zero-sum means no strictly
Pareto-positive outcome), invalid budgets, duplicate-query rejection,
non-dominated archive invariants, hard feasibility and deterministic
repeatability.

## Preliminary local dry run (not independent confirmation)

A local reconstruction of the repository's synthetic benchmark was used
for a 1,000-case exploratory dry run, with the frozen seed 20261107:

| Method | Discoveries/1000 | Archive difference |
|---|---:|---:|
| Archive-guided | 542 | reference |
| Single-anchor ablation | 565 | -2.3 pp |
| Weighted local search | 551 | -0.9 pp |
| Maximin local search | 532 | +1.0 pp |
| Uniform random | 524 | +1.8 pp |

Zero hard-constraint violations; matched 12 objective evaluations per
method per case. Seed-block bootstrap 95% CIs for archive minus
single-anchor: [-4.3, -0.4] pp; weighted: [-2.2, +0.4] pp;
maximin: [-0.3, +2.3] pp; random: [+0.2, +3.0] pp.
The archive method took ~1.36x weighted and ~1.49x maximin CPU time in
this local environment. **H1 is not supported**. The full repository
and CI results take precedence over this reconstructed local dry run.
No method tuning should be performed on these held-out cases.

## Prior art — no claim of originality

- Paquete, Chiarandini & Stützle (2004), *Pareto Local Optimum Sets*:
  https://doi.org/10.1007/978-3-642-17144-4_7
- Deb et al. (2002), *NSGA-II*, non-dominated sorting and diversity:
  https://doi.org/10.1109/4235.996017
- Zitzler, Laumanns & Thiele (2001), *SPEA2*, archive and density:
  https://doi.org/10.3929/ethz-a-004284029

Pareto archives and local search are established methods. This is a
specific experimental application, not an invented optimization paradigm.

## Important limitations

The test generator shares assumptions with the original project; it is
not an independent external benchmark. The five seed blocks provide
limited inferential power; repeated reuse of these held-out instances
would invalidate confirmatory claims. Matched objective calls do not
imply matched wall-clock compute, and local CPU timings depend on
hardware and Python. Stronger actual PLS, NSGA-II and SPEA2
implementations and independent evaluation are not included.
This code is **not wired into existing workflows or promotion gates**.
Human review is required for any future integration.
