# AΩ | AI — Preregistered candidate hypothesis H01 (2026-11-06)

**Status: protocol only, untested.** This is a proposal, not an experimental
finding, a claim of novelty, or evidence of real-world human benefit.

## Mechanism and falsifiable prediction

**H01: Feasibility-first, uncertainty-aware Pareto frontier search.**
For a fixed utility-evaluation budget, a search policy that (a) retains all
observed non-dominated feasible outcomes, (b) proposes new configurations
near *diverse* members of this frontier, and (c) explicitly penalizes
near-duplicate previously evaluated configurations will find strictly
Pareto-improving allocations more often than the strongest training-selected
baseline. The policy must **never** use unobserved objective values.

Why test this? Existing `discovery.py` anchors search to the best or most
recent observed configuration and tunes a finite policy grammar. It does not
explicitly maintain a diverse non-dominated archive. In a constrained,
multi-agent landscape with disconnected beneficial regions, diversity might
reduce premature local convergence. Conversely, archive maintenance and
diversification might waste time or evaluations and lower success rates.
Either outcome falsifies or constrains H01.

**Primary outcome:** fraction of synthetic cases where a strictly Pareto
improvement over the specified status quo is found within the same number of
objective-function calls, with *all* hard constraints satisfied.

## Comparison plan, frozen before evaluating confirmatory holdouts

1. Implement H01 in a separate, restricted policy with a fixed bounded
   archive and no arbitrary generated code or external actions.
2. Baselines: uniform random, existing weighted local search, existing
   maximin local search, the existing tuned policy, and a simple Pareto
   archive without diversity control (ablation). Where practical include
   a well-implemented Pareto local search baseline. Choose the primary
   comparator on TRAIN only, never on the final held-out set.
3. Train / tune on at least 400 synthetic cases across all five environment
   families. Freeze the candidate, comparator, search budgets, seeds,
   constraints, and metrics before final confirmatory testing.
4. Confirm with **at least 1,000 entirely disjoint held-out cases and at
   least five independently generated case seeds**. Use paired outcomes
   and identical per-case objective-evaluation budgets, recording actual
   objective calls, feasibility checks and elapsed wall-clock CPU time.
   Evaluate at budgets 12, 24 and 48, declaring budget 24 the primary
   endpoint before testing.
5. For fair real-compute comparison, execute on identical pinned runner
   specifications with repeated randomized execution order, report
   median/quantile elapsed time and number of evaluations, and include
   a matched-wall-clock sensitivity analysis. Do not equate matched
   utility calls with matched CPU work.
6. Predefine success as a >5 percentage-point paired improvement over
   the strongest training-selected comparator, with 95% paired bootstrap
   **lower bound >0**, no hard-constraint violations, and no unexplained
   compute disadvantage. Report all five seeds and all negative results.
7. Keep all training, validation and final holdout seeds disjoint; never
   adapt policies to final holdout outcomes. Reusing a holdout repeatedly
   for iterative tuning invalidates confirmatory status.
8. Publish runnable code, versioned environment details, raw paired
   per-case results, full metrics, uncertainty intervals and failures.
   Independent reproduction by a separate reviewer is still required.

## Prior-art check / novelty risk

This hypothesis draws on known families of methods. **No novelty claim.**
Relevant established work includes:
- Knowles & Corne (2000), *Approximating the Nondominated Front Using the
  Pareto Archived Evolution Strategy*, Evolutionary Computation.
- Paquete, Chiarandini & Stützle (2004), *Pareto Local Optimum Sets in the
  Biobjective Traveling Salesman Problem: An Experimental Study*.
- Deb et al. (2002), *A Fast and Elitist Multiobjective Genetic Algorithm:
  NSGA-II*, IEEE Transactions on Evolutionary Computation.
- Zitzler, Laumanns & Thiele (2001), *SPEA2: Improving the Strength Pareto
  Evolutionary Algorithm*.
- Google DeepMind, AlphaEvolve (2025), automated algorithm design.
- López-Ibáñez et al., irace, automatic algorithm configuration.

These are initial literature anchors, not a complete systematic novelty
review. A serious prior-art search should examine constrained multiobjective
black-box optimization, archive diversity selection, Pareto local search and
cooperative multi-agent allocation before any publication claiming invention.

## Safeguards and limits

Synthetic utilities do not measure actual welfare. A Pareto improvement for
*modeled* agents can still harm omitted stakeholders. The existing
interaction-integrity synthetic control suite tests its own instrumentation,
not the actual behavior of deployed AI. Human rights, consent, interruption
and independent oversight cannot be reduced to this single optimization
metric.

**Current evidence:** the scheduled workflow has completed exploratory
simulations, but this proposed H01 mechanism has not been implemented or
evaluated. The hypothesis should remain unconfirmed until the entire
preregistered comparison and independent replication are complete.
