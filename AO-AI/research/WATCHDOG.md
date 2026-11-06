# AΩ | AI — Automatic missed-run watchdog

The research workflow (`.github/workflows/ao-ai-daily.yml`) is
scheduled at minute 07 and 37 UTC. GitHub can delay or drop scheduled
runs. The independent `.github/workflows/ao-ai-watchdog.yml` is scheduled
at minute 18 and 48 UTC, and makes a *read-then-conditionally-dispatch*
decision from GitHub's own recorded workflow-run history.

## Recovery trigger

- Fetch the latest 50 research workflow runs from the GitHub Actions API.
- Never dispatch if any research job is queued, pending or currently running.
- When no research run has **started in the last 65 minutes**, dispatch
  **one** new `workflow_dispatch` run of exactly `ao-ai-daily.yml` on `main`.
- A just-started manual or restarted run counts as recent. Recovery
  does not use scientific success to decide whether to dispatch.
- Stop this policy outside **2026-11-06 to 2026-12-05 inclusive (UTC)**.
- A malformed API response fails the watchdog instead of making
  assumptions and possibly duplicating research executions.
- A manual or push invocation of the watchdog is **dry-run only**.
  Only scheduled watchdog invocations have permission to dispatch.
- Main research workflow retains its original `concurrency` group,
  which prevents concurrent series. The watchdog has its own group.

## Security and resource limits

Only the watchdog workflow receives `actions: write` for its short-lived
GitHub-hosted token; the research workflow remains strictly read-only.
The recovery target and branch are fixed. No PAT, external service, paid
API, human content or external code execution is needed. Watchdog runtime
has a 5-minute timeout and the research loop retains its 29-minute timeout.
A GitHub schedule may still fail to invoke *both* jobs; this is
best-effort redundancy, not independent monitoring infrastructure.
Queued jobs that remain stuck require investigation rather than forcing
overlapping executions. Automated notification of persistent outages
would require a separate external scheduler.

## Testing

```sh
python3 -m unittest discover -s AO-AI/research -p 'test_watchdog.py' -v
```

The continuous tests include deterministic simulated cases for recovery
thresholds, healthy/recent starts, queued and running series, manual
restarts, malformed responses and trial-window expiry.

**This watcher does not change or validate research findings.**
