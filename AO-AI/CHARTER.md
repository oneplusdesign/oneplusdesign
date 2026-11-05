# AΩ | AI — Technical Research Scope

**Version:** 0.3 · 2026-11-05

## Aim

Evaluate whether multi-agent proposal generation can discover feasible **Pareto-improving** solutions more efficiently than established multi-objective optimization baselines under matched computational budgets.

## Formal setup

For stakeholders \(i=1,...,n\), utilities \(u_i:X\to\mathbb{R}\), baseline \(x_0\) and hard feasibility constraints \(C(x)\), seek \(x\) such that \(C(x)=true\), \(u_i(x)\ge u_i(x_0)\) for all \(i\), and \(u_j(x)>u_j(x_0)\) for some \(j\).

A Pareto improvement may not exist. Stakeholder utilities may be unknown, strategic, unstable, or incommensurable. Real-world rights, authorization, privacy and non-discrimination requirements must be treated as hard constraints rather than merely score penalties.

## Experimental safeguards

- Fixed seeds, preregistered methodology and held-out datasets.
- Transparent code, matched compute budgets, and strong baseline comparisons.
- Per-stakeholder outcomes, uncertainty, robustness and failure reporting.
- Privacy-preserving input handling and reviewable external actions.
- Independent checking of all empirical claims; no reliance on self-reported agent assertions.

## Non-claims

This is not a foundation model, proven novel optimizer, solved AI-alignment problem, production authorization layer, or empirically validated social-welfare engine. The current implementation only provides an educational deterministic action-screening component.

See [RESEARCH.md](RESEARCH.md) and [MISSION-01.md](MISSION-01.md).

Research correspondence: **tasos.tsikriteas@gmail.com**
