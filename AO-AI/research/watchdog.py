"""AΩ | AI: conservative watchdog for missed GitHub research runs.

Only emits a recommendation based on GitHub's recorded run history.
The GitHub Action wrapper performs the bounded, fixed-target dispatch.
No model is loaded and no repo content is modified by this module.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

WINDOW_START = datetime(2026, 11, 6, tzinfo=timezone.utc)
WINDOW_END_EXCLUSIVE = datetime(2026, 12, 6, tzinfo=timezone.utc)
ACTIVE = frozenset(("queued", "in_progress", "waiting", "pending", "requested"))
MAX_HISTORY = 50


def _parse_utc(value: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError("Run creation time is missing")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("Run creation time must have a timezone")
    return result.astimezone(timezone.utc)


def decide(now: datetime, payload: dict, *, stale_after_minutes: int = 65) -> dict:
    """Choose NO_ACTION / RECOVER without relying on fabricated heartbeats.

    The latest created run is deliberately the throttle even if it failed.
    Active executions block recovery, preventing overlapping work. This
    watchdog catches missed starts, not scientific failures or frozen
    GitHub infrastructure. It never changes existing research results.
    """
    if now.tzinfo is None:
        raise ValueError("Expected timezone-aware UTC time")
    now = now.astimezone(timezone.utc)
    if not 30 <= stale_after_minutes <= 180:
        raise ValueError("Stale threshold outside bounded range")
    if not isinstance(payload, dict) or not isinstance(payload.get("workflow_runs"), list):
        raise ValueError("Expected GitHub Actions workflow_runs response")
    runs = payload["workflow_runs"]
    if len(runs) > MAX_HISTORY:
        raise ValueError("Unexpected oversized API response")
    if not WINDOW_START <= now < WINDOW_END_EXCLUSIVE:
        return {"action": "NO_ACTION", "reason": "outside_30_day_trial",
                "stale_after_minutes": stale_after_minutes}
    if any(not isinstance(r, dict) for r in runs):
        raise ValueError("Malformed GitHub run entry")
    # Never restart during any queued or actively running series, even if
    # the start itself is old. Such a case needs separate investigation.
    active = [r for r in runs if r.get("status") in ACTIVE]
    if active:
        return {"action": "NO_ACTION", "reason": "research_already_queued_or_running",
                "active_count": len(active), "stale_after_minutes": stale_after_minutes}
    started = [_parse_utc(r.get("created_at")) for r in runs]
    latest = max(started, default=WINDOW_START)
    if latest > now:
        raise ValueError("Future run timestamp: refusing to start duplicate")
    idle_minutes = round((now - latest).total_seconds() / 60, 2)
    if idle_minutes < stale_after_minutes:
        return {"action": "NO_ACTION", "reason": "recent_run_already_recorded",
                "minutes_since_latest_start": idle_minutes,
                "stale_after_minutes": stale_after_minutes}
    return {"action": "RECOVER", "reason": "no_run_started_within_threshold",
            "minutes_since_latest_start": idle_minutes,
            "stale_after_minutes": stale_after_minutes}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--threshold-minutes", type=int, default=65)
    args = parser.parse_args()
    payload = json.loads(args.runs_file.read_text(encoding="utf-8"))
    result = decide(datetime.now(timezone.utc), payload,
                    stale_after_minutes=args.threshold_minutes)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
