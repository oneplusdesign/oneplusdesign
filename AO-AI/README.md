# AΩ | AI — Cooperative Intelligence Research

**Area:** multi-agent systems, constrained multi-objective optimization, Pareto efficiency, cooperative decision synthesis and reproducible benchmarking.

**Current status:** open research prototype. No candidate optimizer or measured performance improvement over conventional algorithms has been demonstrated.

## Research question

Given agents \(i\in\{1,...,n\}\), feasible outcomes \(x\in X\), utility functions \(u_i(x)\), baseline \(x_0\), and hard constraints \(C(x)\), search for outcomes satisfying:

- \(C(x)=true\)
- \(u_i(x)\ge u_i(x_0)\) for every stakeholder \(i\)
- \(u_j(x)>u_j(x_0)\) for at least one stakeholder \(j\)

This is a standard **Pareto improvement** relative to the baseline, not a new mathematical result. Existence is not guaranteed. Utility functions are imperfect representations of human interests and are insufficient, alone, to establish real-world welfare.

## Current artifact

The present site is a responsive research overview plus a **deterministic agent-action declaration gate**; it is not a cooperative multi-agent solver or AI model. Source: `index.html`, `style.css`, `app.mjs`, `core.mjs`. Unit tests: `tests/core.test.mjs`.

The current gate applies explicit conditions to self-declared inputs, returning `BLOCK`, `REVIEW`, or `PROVISIONAL`. **No output is actual execution authorization, proof of safety, or independently verified assessment.**

## Replication

Start a local web server in this directory:

```sh
python -m http.server 8765
```

Open `http://localhost:8765/`.

Run the deterministic core tests using Node.js 20+:

```sh
node --test tests/core.test.mjs
```

No third-party package, external model API or credential is needed to run the existing component.

## Proposed research roadmap

1. Define synthetic 2–5-agent allocation environments with reproducible utilities and constraints.
2. Establish baseline results using random search, weighted-sum optimization and Pareto-frontier methods, with equal evaluation budgets.
3. Preregister test conditions, independent seeds and held-out instances before designing a candidate algorithm.
4. Measure feasible rate, Pareto-improving rate, worst-off utility change, solution-set coverage, computation and constraint violations.
5. Publish negative results and compare any candidate method to strong conventional baselines without overclaiming.

See [technical scope](CHARTER.md), [evaluation protocol](RESEARCH.md) and [milestone 01](MISSION-01.md).

## Constraints and non-claims

- No deployed independent optimizer or multi-agent research result at present.
- No unreviewed access to other AI services or model internals.
- No claim that aggregate utility substitutes for protected rights or legitimate human oversight.
- No model provider affiliation or endorsement.
- The host repository currently has GitHub Issues disabled.

## Contact

Research correspondence: **tasos.tsikriteas@gmail.com**

## License

MIT, see [LICENSE](LICENSE).
