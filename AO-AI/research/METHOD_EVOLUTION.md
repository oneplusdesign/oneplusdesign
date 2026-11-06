# AΩ | AI — Method Evolution and Bounded Program Growth

**Purpose:** the research should change *what it tries*, based on what
worked in prior synthetic experiments, instead of only collecting counts.

## Implemented

The new method-evolution engine evolves a typed, finite-grammar search
recipe containing a **variable-length set of utility-scoring features**,
their signed weights, a candidate-proposal operator, an exploration
schedule, and a policy for which observed solution to build on.

An evolutionary mutation may:
- grow the method with another feature (up to four);
- shrink it by removing a feature;
- replace a feature or adjust its weight;
- change exploration, incumbent choice, or proposal structure.

This is a simple, auditable instance of existing genetic programming.
It **does not** mean the system writes arbitrary new Python or has
independent creative reasoning.

## Evaluation and memory

Every **25 short research experiments** the worker compares candidate
recipes on common synthetic training cases, promotes the best
training performer, freezes it, and tests once on separate holdout cases
against a reference method selected on training only. It records gains,
losses, confidence intervals, and failures in the aggregate report.

A validated training-selected recipe can be inherited from the previous
successful GitHub research artifact. Missing artifacts safely reset the
evolution. Holdout scores are **not** used to select the inherited
recipe. Continuous re-testing on multiple holdouts is exploratory and
does not yield independent scientific confirmation.

## Executable code proposal workflow

The [code-proposal pipeline](CODE_PROPOSALS.md) compiles selected
methods into new, executable standalone Python source files, checks
them in a separate subprocess, archives all evidence every four hours,
and never automatically merges or deploys generated code.

## Limits — must not be confused with breakthroughs

- No mutation of GitHub source files or automatic deploys. Research
  workers retain read-only permissions.
- No arbitrary executable strings: all method components are from
  a fixed grammar, of maximum four feature terms.
- All outcomes are **synthetic mathematical proxies**, not human or
  ecological well-being. Omitted stakeholders are still an unsolved
  problem. The separate interaction-integrity suite only tests
  human-authored synthetic annotations.
- No guarantees of long-term gains. Some changes worsen holdout
  performance. Report them rather than hiding them.
- A true self-improving *software-development agent* would require
  separately authorized, sandboxed patch proposals and tests, external
  evaluation, human review, constrained permissions, and rollback.
  That is NOT included in this phase.

## Reproduce

Run the full test suite:

    python3 -m unittest discover -s AO-AI/research -p 'test_*.py' -v

Run a bounded local integration case:

    python3 AO-AI/research/continuous_research.py --run-date 2026-11-06 --run-key 77 --max-experiments 25 --count 2 --output ao-demo.json

Inspect method_evolution_outcomes in ao-demo.json.

Research contact: tasos.tsikriteas@gmail.com
