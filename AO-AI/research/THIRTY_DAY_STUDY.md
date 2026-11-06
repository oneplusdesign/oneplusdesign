# AΩ | AI — Consecutive Research Cycles (30-Day Trial)

**Trial window (UTC):** 2026-11-06 to 2026-12-05 inclusive.

## Execution design

- **GitHub Actions schedule:** at minute 07 and 37 of every hour (UTC).
- **Each run:** up to 24 minutes of back-to-back synthetic experiments, then runner exits; the next scheduled run starts a new sequence.
- **Each experiment:** 40 distinct synthetic allocation environments, tested with *equal utility-query budgets* using uniform random, weighted local search and maximin local search.
- **Alternating conditions:** five environment families (mixed, synergy, scarcity, balanced, adversarial) and three objective-evaluation budgets (12, 24, 48); deterministic unique case seeds per workflow execution / experiment.
- **Output:** a compact, atomic-checkpoint JSON aggregate artifact saved by the workflow (35-day retention). Public GitHub workflow history is the only activity signal, not a claim of a conscious or always-active AI.

### Autonomous hypothesis/configuration search

Each scheduled session also executes a constrained evolutionary search of optimizer policy hypotheses: generate candidate configurations, evaluate them on training cases, select and mutate promising candidates, freeze a selected policy, and evaluate against a training-selected baseline on disjoint holdout cases. This is documented in [DISCOVERY_PROTOCOL.md](DISCOVERY_PROTOCOL.md). Results are exploratory; no scientific novelty or advantage has been demonstrated.

### Self-expanding search-method compositions

Every 25 short baseline experiments, a separate
[method-evolution engine](METHOD_EVOLUTION.md) combines, adds, removes and
reweights safe search features and exploration operators. It evaluates
candidate methods on training data, freezes the training-selected winner,
and compares it once on synthetic holdout cases. Only validated recipe
data may carry over to later sessions. It does **not** write or deploy
Python code, update model weights, or claim any real-world benefit.

### Learning between scheduled runs

At the beginning of each scheduled session, a read-only GitHub CLI step attempts to retrieve the prior successful research run's own JSON report artifact. Only the latest **training-selected policy configuration** or **validated method recipe** may be reused as a seed for the next round's candidate generation, and only after strict schema validation. The previous holdout scores are **not** used to choose a policy. Missing/expired artifacts are allowed; the experiment then starts with a fresh training population. No downloaded data is executed as code.

### Interaction integrity control suite

Every five experiment iterations the system also runs a reproducible
[interaction-integrity control suite](INTERACTION_INTEGRITY.md), covering
unsupported feeling/action claims, emotional pressure, human choice,
correction handling and disclosure of uncertainty. Results are based on
**synthetic externally annotated traces only**. They are not evidence of an
actual model's conduct in real interactions and do not change model weights.

### Watchdog for missed schedules

A separate [self-recovery watchdog](WATCHDOG.md) probes GitHub's actual
research run history at :18 and :48 UTC. If there has been no new research
run for 65 minutes and none is queued/running, it dispatches the fixed
research workflow automatically. It stops after the 30-day trial,
avoids duplicate runs, and does not require the user to be logged in.
The watchdog itself is also subject to GitHub schedule delays/drops.

### Separate six-month closed-loop self-improvement

The original high-frequency baseline study is intentionally limited
to 30 days. A **separate scheduled, read-only [code evolution loop](CODE_PROPOSALS.md)**
runs every ten minutes through **2027-05-06 UTC**, and has an explicit
[Good-of-All Safety Contract](SAFETY_AND_GOVERNANCE.md).

It automatically generates executable candidate code from a fixed
method grammar, verifies 30 paired conformance cases and 1,000
fresh synthetic held-out cases over five seeds, and stores ONLY a
validated research JSON recipe if the independent gate beats both
existing reference baselines and the previous champion with
predefined statistical, compute and per-regime constraints.

Failed candidates never overwrite the champion. The method's generated
source is review-only and no research worker can change production
code, external systems, permissions or any real-world behavior.
The separately scheduled ChatGPT research task can attempt
human-reviewable code revisions, subject to connected tool access.

### What this does NOT do

- No real-world data, model weights, paid external AI API or arbitrary executable-code generation is involved. The automatic hypothesis generator operates within a fixed, auditable parameter grammar.
- More simulations ≠ scientific discovery. Methods are known reference heuristics; output is observational, not evidence of a novel optimizer.
- GitHub-hosted scheduled events are best-effort: queues, throttling and dropped events can produce gaps. A fully uninterrupted worker would require dedicated infrastructure.
- Equal objective evaluations do not imply equal CPU wall-clock budgets.
- No messages/emails are sent from GitHub Actions on ordinary runs.

### Reproduce

```sh
python3 -m unittest discover -s AO-AI/research -p 'test_*.py' -v
python3 AO-AI/research/continuous_research.py --run-date 2026-11-06 --run-key 17 --max-experiments 6 --count 40 --output ao-research-series.json
```

Study validation criteria and original research scope remain in [RESEARCH.md](../RESEARCH.md) and [MISSION-01.md](../MISSION-01.md).

## Resource controls and exit conditions

- Jobs use only standard GitHub-hosted runners in a public repository, with **read-only repository permissions for the research loop**; the separate watchdog uses narrowly scoped `actions: write` only to dispatch the existing workflow. GitHub currently provides free standard hosted compute for public repositories; account-specific settings and storage billing should still be monitored.
- Maximum 29 minute job timeout, no paid cloud services, no autonomous writes or external actions outside read-only GitHub artifact retrieval. The research workflow token is restricted to read-only contents and actions access; the watchdog's short-lived token can dispatch an existing workflow.
- Repo artifacts store aggregated synthetic measurements; no personal narratives.
- After 2026-12-05, jobs immediately skip experiments. Removing the cron afterward requires a separate workflow edit or the scheduled research review.
- New scientifically meaningful methods, independent replication and peer review remain necessary before any major scientific claim.

**Research contact:** tasos.tsikriteas@gmail.com.
