"""Deterministic watchdog checks: no duplicate, bounded self-recovery."""
import unittest
from datetime import datetime, timedelta, timezone

from watchdog import decide


UTC = timezone.utc
NOW = datetime(2026, 11, 6, 12, 0, tzinfo=UTC)


def payload(*runs):
    return {"workflow_runs": list(runs)}


def run(age_mins, status="completed", event="schedule"):
    return {
        "created_at": (NOW - timedelta(minutes=age_mins)).isoformat(),
        "status": status, "event": event,
    }


class WatchdogTests(unittest.TestCase):
    def test_healthy_scheduled_run_no_recovery(self):
        self.assertEqual(decide(NOW, payload(run(29)))["action"], "NO_ACTION")

    def test_missing_both_recent_schedules_triggers_recovery(self):
        result = decide(NOW, payload(run(67)))
        self.assertEqual(result["action"], "RECOVER")
        self.assertEqual(result["reason"], "no_run_started_within_threshold")

    def test_active_job_blocks_duplicate_even_when_old(self):
        for state in ("queued", "in_progress", "waiting"):
            with self.subTest(state=state):
                result = decide(NOW, payload(run(95, state), run(145)))
                self.assertEqual(result["reason"], "research_already_queued_or_running")

    def test_recent_manual_recovery_prevents_repeat(self):
        result = decide(NOW, payload(run(20, "completed", "workflow_dispatch"),
                                     run(200)))
        self.assertEqual(result["action"], "NO_ACTION")

    def test_failure_still_respects_throttle(self):
        result = decide(NOW, payload(run(30, "completed"), run(200)))
        self.assertEqual(result["action"], "NO_ACTION")

    def test_no_history_recovers_after_trial_begins(self):
        result = decide(NOW, payload())
        self.assertEqual(result["action"], "RECOVER")

    def test_start_of_trial_no_early_recovery(self):
        early = datetime(2026, 11, 6, 0, 25, tzinfo=UTC)
        self.assertEqual(decide(early, payload())["action"], "NO_ACTION")

    def test_outside_trial_wont_restart(self):
        for when in (datetime(2026, 11, 5, 12, tzinfo=UTC),
                     datetime(2026, 12, 6, 1, tzinfo=UTC)):
            self.assertEqual(decide(when, payload(run(200)))["reason"],
                             "outside_30_day_trial")

    def test_evolution_watchdog_recovers_after_skipped_four_hour_cycle(self):
        self.assertEqual(decide(NOW, payload(run(310)),
                                stale_after_minutes=300, evolution=True)["action"],
                         "RECOVER")
        self.assertEqual(decide(NOW, payload(run(250)),
                                stale_after_minutes=300, evolution=True)["action"],
                         "NO_ACTION")
        self.assertEqual(decide(NOW, payload(run(500, "in_progress")),
                                stale_after_minutes=300, evolution=True)["action"],
                         "NO_ACTION")

    def test_evolution_watchdog_stops_after_six_months(self):
        when = datetime(2027, 5, 7, 0, 1, tzinfo=UTC)
        self.assertEqual(decide(when, payload(),
                                stale_after_minutes=300,
                                evolution=True)["reason"],
                         "outside_6_month_trial")

    def test_ignores_old_success_if_a_newer_run_exists(self):
        self.assertEqual(decide(NOW, payload(run(20), run(800)))["action"], "NO_ACTION")

    def test_malformed_api_response_fails_closed(self):
        with self.assertRaises(ValueError):
            decide(NOW, {})
        with self.assertRaises(ValueError):
            decide(NOW, payload({"status": "completed"}))
        with self.assertRaises(ValueError):
            decide(NOW, payload({"status": "completed",
                                 "created_at": "not a date"}))

    def test_future_run_fails_closed(self):
        with self.assertRaises(ValueError):
            decide(NOW, payload(run(-1)))

    def test_no_unbounded_retry_configuration(self):
        with self.assertRaises(ValueError):
            decide(NOW, payload(), stale_after_minutes=1)


if __name__ == "__main__":
    unittest.main()
