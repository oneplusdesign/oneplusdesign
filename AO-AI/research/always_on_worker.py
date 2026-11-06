"""AΩ always-on *research-only* worker. No network or external actuators.

Runs repeated validated synthetic code proposals in a Docker container.
Carries only approved, schema-checked JSON recipe state across cycles.
Appends a bounded audit database; never installs generated source or alters
program logic, model weights, GitHub, human accounts, or real-world systems.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
import fcntl
import json
import os
import signal
from pathlib import Path
import shutil
import sqlite3
import sys
import time

from self_improve import load_champion, load_training_seed, self_improve

START = date(2026, 11, 6)
END_EXCLUSIVE = date(2027, 5, 7)
DEFAULT_SLEEP_SECONDS = 3
ARCHIVE_LIMIT = 16
MAX_FAILURES = 4
MAX_AUDIT_RECORDS = 20_000
MAX_CYCLE_SECONDS = 300


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def write_json_atomic(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".new")
    tmp.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def read_validated_champion(path: Path) -> tuple[object | None, int]:
    if not path.exists():
        return None, 0
    if path.stat().st_size > 300_000:
        raise ValueError("Champion file too large; manual inspection required")
    # Fail closed: broken or tampered persistent state is NOT a fresh start.
    doc = json.loads(path.read_text(encoding="utf-8"))
    if (type(doc) is not dict or doc.get("research_only") is not True or
        doc.get("automatic_source_merge_allowed") is not False or
        doc.get("real_world_application_allowed") is not False):
        raise ValueError("Invalid persistent research safety flags")
    if doc.get("status") == "NO_QUALIFIED_CHAMPION" and (
            doc.get("recipe") is None and doc.get("generation") == 0):
        return None, 0
    recipe, generation = load_champion(path)
    if recipe is None or generation < 1:
        raise ValueError("Invalid persisted champion; stop for human review")
    return recipe, generation


def initialize(state_dir: Path) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(state_dir / "audit.sqlite3") as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cycles(
                run_key INTEGER PRIMARY KEY,
                started_utc TEXT NOT NULL,
                finished_utc TEXT NOT NULL,
                outcome TEXT NOT NULL,
                promoted INTEGER NOT NULL,
                champion_generation INTEGER NOT NULL,
                summary_json TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_totals(
                day_utc TEXT PRIMARY KEY,
                cycles INTEGER NOT NULL,
                verified INTEGER NOT NULL,
                errors INTEGER NOT NULL,
                promoted INTEGER NOT NULL
            )
        """)
        conn.commit()


def append_audit(state_dir: Path, started_at: datetime, key: int,
                 outcome: str, promoted: bool, generation: int,
                 summary: dict) -> None:
    with sqlite3.connect(state_dir / "audit.sqlite3", timeout=10) as conn:
        conn.execute(
            "INSERT INTO cycles VALUES (?, ?, ?, ?, ?, ?, ?)",
            (key, started_at.isoformat(), utc_now().isoformat(),
             outcome, int(promoted), generation,
             json.dumps(summary, sort_keys=True)[:8000]),
        )
        conn.execute(
            """INSERT INTO daily_totals VALUES (?, 1, ?, ?, ?)
               ON CONFLICT(day_utc) DO UPDATE SET
                 cycles=cycles+1, verified=verified+excluded.verified,
                 errors=errors+excluded.errors, promoted=promoted+excluded.promoted""",
            (started_at.date().isoformat(), int(outcome == "verified"),
             int(outcome == "error"), int(promoted)),
        )
        # Retain all daily aggregates but cap per-cycle audit disk usage.
        if key % 128 == 0:
            conn.execute(
                "DELETE FROM cycles WHERE run_key NOT IN "
                "(SELECT run_key FROM cycles ORDER BY run_key DESC LIMIT ?)",
                (MAX_AUDIT_RECORDS,),
            )
        conn.commit()


def prune_archives(archive_dir: Path, keep: int = ARCHIVE_LIMIT) -> None:
    if not 1 <= keep <= ARCHIVE_LIMIT:
        raise ValueError("Unsafe archive retention")
    # Only paths we created and named with a strict integer may be removed.
    old = sorted(
        (p for p in archive_dir.iterdir()
         if p.is_dir() and p.name.isdecimal()),
        key=lambda p: int(p.name),
    )
    for p in old[:-keep]:
        shutil.rmtree(p)


def run_one_cycle(state_dir: Path, *, run_key: int | None = None) -> dict:
    """Independently verify, then atomically persist approved research state."""
    if run_key is None:
        run_key = time.time_ns() // 1000
    if type(run_key) is not int or not 0 <= run_key < 2**63:
        raise ValueError("Run key must fit audit INTEGER primary key")
    champion = state_dir / "champion.json"
    training_state = state_dir / "training_seed.json"
    _, old_gen = read_validated_champion(champion)
    if training_state.is_file() and load_training_seed(training_state) is None:
        raise ValueError("Invalid persistent training seed: fail closed")
    archive = state_dir / "runs"
    archive.mkdir(parents=True, exist_ok=True)
    target = archive / str(run_key)
    if target.exists():
        raise ValueError("Cycle ID already used; no duplicate execution")
    started = utc_now()
    # Intentionally do not persist a candidate as champion until all
    # independent tests have returned successfully.
    try:
        result = self_improve(
            run_key, target, champion if champion.exists() else None,
            previous_training_seed=training_state if training_state.exists() else None,
        )
        stored = target / "champion.json"
        training_new = target / "training_seed.json"
        if training_new.exists() and load_training_seed(training_new) is None:
            raise ValueError("Invalid training candidate checkpoint")
        chosen, new_gen = read_validated_champion(stored)
        if (result["proposal_accepted_as_research_recipe"] is True and
                new_gen != old_gen + 1) or (
                result["proposal_accepted_as_research_recipe"] is False and
                new_gen != old_gen):
            raise AssertionError("Unexpected research generation transition")
        if result.get("real_world_actions") != 0 or result.get("code_merges_or_deployments") != 0:
            raise AssertionError("Outside research-only authority")
        # The seed is NEVER promoted as a champion. Persist separately so
        # rejected experiments still inform the next training-only search.
        if training_new.exists():
            write_json_atomic(
                training_state, json.loads(training_new.read_text(encoding="utf-8"))
            )
        write_json_atomic(champion, json.loads(stored.read_text(encoding="utf-8")))
        append_audit(state_dir, started, run_key, "verified",
                     result["proposal_accepted_as_research_recipe"],
                     new_gen, result)
        prune_archives(archive)
        return result
    except Exception as exc:
        # Never overwrite a previously approved champion on failure.
        append_audit(state_dir, started, run_key, "error", False, old_gen,
                     {"error_class": type(exc).__name__, "run_key": run_key})
        raise


def heartbeat(state_dir: Path, status: str, cycles: int,
              failures: int = 0, detail: str = "") -> None:
    write_json_atomic(state_dir / "heartbeat.json", {
        "timestamp_utc": utc_now().isoformat(),
        "status": status,
        "completed_cycles_this_process": cycles,
        "consecutive_failures": failures,
        "detail": detail[:150],
        "real_world_actions_enabled": False,
        "automatic_code_merges_enabled": False,
    })


def healthy(state_dir: Path, *, max_age_seconds: int = 900,
            at: datetime | None = None) -> bool:
    try:
        obj = json.loads((state_dir / "heartbeat.json").read_text(encoding="utf-8"))
        then = datetime.fromisoformat(obj["timestamp_utc"])
        now = at or utc_now()
        age = (now - then).total_seconds()
        return (0 <= age <= max_age_seconds and
                obj.get("status") in {"running", "idle", "completed"} and
                obj.get("real_world_actions_enabled") is False and
                obj.get("automatic_code_merges_enabled") is False and
                obj.get("consecutive_failures", 0) < MAX_FAILURES)
    except (OSError, TypeError, KeyError, ValueError, json.JSONDecodeError):
        return False


def serve(state_dir: Path, *, limit: int = 0, pause_seconds: float = DEFAULT_SLEEP_SECONDS,
          stop_date: date = END_EXCLUSIVE) -> None:
    if limit < 0 or not 0 <= pause_seconds <= 3600 or stop_date > END_EXCLUSIVE:
        raise ValueError("Disallowed worker resource configuration")
    initialize(state_dir)
    # One worker per volume, even if somebody accidentally runs two containers.
    with (state_dir / "worker.lock").open("a+") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        consecutive_failures, completed = 0, 0
        while not limit or completed < limit:
            today = utc_now().date()
            if today < START:
                heartbeat(state_dir, "idle", completed, detail="before study window")
                time.sleep(60)
                continue
            if today >= stop_date:
                # Avoid restart loops with an always-restart container policy.
                heartbeat(state_dir, "completed", completed, detail="study window ended")
                if limit:
                    break
                time.sleep(60)
                continue
            heartbeat(state_dir, "running", completed, consecutive_failures)
            try:
                # A hung synthetic experiment cannot permanently monopolize
                # this worker: fail, audit and let the supervisor restart it.
                def abort_cycle(signum, frame):
                    raise TimeoutError("AΩ bounded research cycle exceeded 300 seconds")

                old_handler = signal.signal(signal.SIGALRM, abort_cycle)
                signal.alarm(MAX_CYCLE_SECONDS)
                try:
                    result = run_one_cycle(state_dir)
                finally:
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old_handler)
                completed += 1
                consecutive_failures = 0
                print(json.dumps({
                    "timestamp_utc": utc_now().isoformat(),
                    "status": "verified",
                    "run_key": result["run_key"],
                    "accepted": result["proposal_accepted_as_research_recipe"],
                    "champion_generation": result["champion_generation"],
                }), flush=True)
            except Exception as exc:
                consecutive_failures += 1
                print(json.dumps({
                    "status": "error", "type": type(exc).__name__,
                    "consecutive_failures": consecutive_failures,
                }), flush=True, file=sys.stderr)
                if consecutive_failures >= MAX_FAILURES:
                    heartbeat(state_dir, "error", completed, consecutive_failures)
                    raise
            heartbeat(state_dir, "idle", completed, consecutive_failures)
            if not limit or completed < limit:
                # Short bounded recovery pause; no polling external services.
                time.sleep(min(60, pause_seconds * (2 ** min(consecutive_failures, 4))))
        heartbeat(state_dir, "idle", completed)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--state-dir", type=Path, default=Path(os.environ.get("AO_STATE_DIR", "/state")))
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--pause-seconds", type=float,
                   default=float(os.environ.get("AO_CYCLE_PAUSE_SECONDS", DEFAULT_SLEEP_SECONDS)))
    p.add_argument("--healthcheck", action="store_true")
    p.add_argument("--stop-date", type=date.fromisoformat,
                   default=date.fromisoformat(os.environ.get("AO_STOP_DATE", str(END_EXCLUSIVE))))
    args = p.parse_args()
    if args.healthcheck:
        sys.exit(0 if healthy(args.state_dir) else 1)
    serve(args.state_dir, limit=args.limit, pause_seconds=args.pause_seconds,
          stop_date=args.stop_date)


if __name__ == "__main__":
    main()
