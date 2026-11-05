# AΩ | AI — 30-day scheduled research study

**Public technical scope. No personal narratives.**

- **Trial dates (UTC):** 2026-11-06 through 2026-12-05 (30 days).
- **Scheduler:** GitHub Actions, daily at 06:17 UTC (08:17 in Greece in November).
- **Compute:** GitHub-hosted Python standard library. No paid LLM API, no autonomous external action.
- **Outputs:** one public Actions run per scheduled day, plus a machine-readable `daily-report.json` artifact (90-day retention).
- **Location:** [workflow runs](https://github.com/oneplusdesign/oneplusdesign/actions/workflows/ao-ai-daily.yml).

## What happens automatically

For each scheduled day, the script uses a new deterministic calendar-derived seed to generate **80 synthetic** three-stakeholder allocation problems. Each has eight possible interventions and a budget of four interventions.

It compares established reference search strategies under the **same objective-query budget (24 evaluations per method per problem)**: uniform random search, weighted-sum local search and maximin local search. The exact truth oracle is for scoring only, and its computational cost is *not* counted in method budgets; consequently the output is **not** a total compute or runtime comparison.

The script explicitly marks **`research_breakthrough_claim: false`**. A successful GitHub workflow run means that scripts executed successfully, not that a scientific breakthrough occurred. The present implementation generates changing test data, not new research hypotheses or autonomous algorithm modifications.

## Success criteria for future research

Before claiming an original technical advance, a new candidate method must be precisely specified, peer-reviewed for prior-art novelty, independently replicated on held-out cases, and outperform strong existing baselines under comparable information and compute budgets. Any claim must be backed by a public reproduction package and limitations.

No automatic email is sent by this workflow. Any separate notification should require substantive independently verified evidence, not CI success or a subjective feeling.

## End-of-window behavior

After 2026-12-05, scheduled workflow invocations **skip the experiment**. The GitHub scheduler entry will still exist and will trigger a very short window check until someone disables the workflow; GitHub Actions cannot natively express a one-off 30-day cron with automatic expiry. Disable the workflow after the study to eliminate even that overhead.

Research correspondence: **tasos.tsikriteas@gmail.com**.
