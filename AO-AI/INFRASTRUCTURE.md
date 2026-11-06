# AΩ | AI — Always-on Research Infrastructure

## Deployment status

The GitHub repository contains a complete containerized **research worker**
and an isolated Docker Compose deployment definition. A GitHub Actions
smoke test builds the image, runs one real bounded research cycle with
`network_mode: none`, and verifies the persistent heartbeat across
container executions.

**The container is not currently installed on a permanent host.**
This repository by itself cannot provide 24/7 compute. The existing
GitHub Actions schedules continue to run as a separate best-effort service.

## What the always-on worker does

While a Linux host with Docker is running, one Python worker runs
successive research cycles with a short configurable pause. Each cycle:

1. Reads the previously **verified research recipe**, if any, from
   persistent storage. Malformed or untrusted state causes a safe halt.
2. Generates new bounded search-method compositions and a review-only
   executable Python candidate. No untrusted free-form code is accepted.
3. Runs independent tests: 1,000 fresh synthetic cases, five seeds,
   two reference baselines and the incumbent (if any), equal objective
   budgets, per-regime no-regression checks and compute limits.
4. Persists a new champion **as JSON data only** if every condition passes;
   otherwise retains the old one.
5. Records the outcome in a persistent SQLite audit log and daily totals.
   Recent candidate artifacts are kept in a bounded archive (16 runs;
   the audit keeps the last 20,000 detailed runs).
6. Updates a health heartbeat. If a bounded cycle fails repeatedly, the
   process exits and Docker's restart policy relaunches it.

The worker runs only through **6 May 2027 UTC** and becomes idle
on **7 May 2027**. It has no real-world actuator and no AI-model API
connection: the underlying research is synthetic.

## Requirements

- A continuously powered Linux machine or approved VPS.
- Docker Engine and Docker Compose v2.
- Approximately 2 CPU cores, 1 GB+ RAM, and persistent disk space
  (actual capacity/usage needs monitoring). The container is
  configured for 1.5 CPU and 768 MiB RAM.
- No inbound ports are required. The research container's network
  is disabled. Image building initially needs internet access to
  obtain the public Python base image.
- If the machine is the user's existing computer, it must stay on.
  Dedicated hosting can have a charge. **No hosting or billing was
  provisioned by these repository changes.**

## Install on an approved host

After an owner/admin installs Docker and clones the public repository:

```sh
cd oneplusdesign
docker compose -f AO-AI/compose.yaml config -q
docker compose -f AO-AI/compose.yaml build
docker compose -f AO-AI/compose.yaml up -d
docker compose -f AO-AI/compose.yaml ps
docker compose -f AO-AI/compose.yaml logs -f --tail 30
```

Inspect the internal checkpoint without publishing data:

```sh
docker compose -f AO-AI/compose.yaml exec ao-ai-worker \
  python -m always_on_worker --healthcheck --state-dir /state
```

Stop and restart without losing the champion:

```sh
docker compose -f AO-AI/compose.yaml stop
docker compose -f AO-AI/compose.yaml start
```

Stop permanently without deleting state:

```sh
docker compose -f AO-AI/compose.yaml down
```

**Do not use `down -v` on a production deployment:** it deletes
the persistent state volume. A regular host-level backup of the
`ao-ai-state` volume and the relevant SQLite files is recommended;
the container deliberately has no network access for cloud backup.

## Security model and limits

- **No network** inside the worker, no published ports and no
  Docker daemon socket.
- Non-root UID 65532, read-only root filesystem, all Linux
  capabilities dropped, no-new-privileges, memory/CPU/PID limits.
- Only /state is persistent. Generated source lives in that
  volume and is checked against the trusted finite whitelist.
- A single-writer file lock prevents multiple simultaneous processes
  from corrupting the champion.
- Cycle execution is bounded to 300 seconds. Audit state is written
  to disk. Rejected/failed candidates do not overwrite the champion.
- Docker restarts a process that exits unexpectedly, but a stale
  Docker **healthcheck alone does not automatically restart it**.
  A separate host-level monitoring service is required to restart
  truly hung containers and to alert a human about persistent failures.
- This is isolation by ordinary Docker controls, **not a proof
  of total safety**. Do not add unreviewed model-generated code,
  host filesystem mounts or elevated capabilities.

## Handover / avoid duplicate research

Do NOT leave both the existing ten-minute GitHub scheduled evolution
job and a new always-on host running indefinitely as two independent
champions. They maintain separate state and may diverge. After the
host has passed a real multi-cycle test with restart and persistence,
the owner should explicitly approve disabling the scheduled GitHub
code-proposal workflow, retaining its manual test trigger.

The separate ChatGPT research automation can investigate broader
source-code hypotheses and propose draft PRs, but it is NOT inside this
container. No fully general self-programming research agent exists yet.

## Verification

- Core Python tests: GitHub Actions `AΩ AI — core tests`.
- Docker container smoke test:
  [AO infrastructure CI](../../.github/workflows/ao-ai-infrastructure-ci.yml).
- Safety contract: [Good-of-All](research/SAFETY_AND_GOVERNANCE.md).

The engineering objective is a bounded, observable, reproducible
research engine that seeks beneficial methods while blocking external
actions, **not** a claim that it is conscious, an unrestricted AI
scientist, or mathematically incapable of causing harm.
