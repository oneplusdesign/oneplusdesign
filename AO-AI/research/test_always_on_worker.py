"""Always-on research infrastructure unit tests (no Docker or network needed)."""
from datetime import datetime, timedelta, timezone, date
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from always_on_worker import (
    START, END_EXCLUSIVE, append_audit, healthy, heartbeat, initialize,
    prune_archives, read_validated_champion, run_one_cycle, serve,
    write_json_atomic,
)


def no_champion():
    return {
        "status": "NO_QUALIFIED_CHAMPION",
        "research_only": True,
        "recipe": None,
        "generation": 0,
        "automatic_source_merge_allowed": False,
        "real_world_application_allowed": False,
    }


class AlwaysOnWorkerTests(unittest.TestCase):
    def test_untrusted_champion_cannot_be_used(self):
        with TemporaryDirectory() as d:
            file = Path(d) / "champion.json"
            file.write_text('{"recipe":"arbitrary code"}')
            with self.assertRaises(ValueError):
                read_validated_champion(file)

    def test_valid_no_champion_is_safe(self):
        with TemporaryDirectory() as d:
            p = Path(d) / "champion.json"
            write_json_atomic(p, no_champion())
            self.assertEqual(read_validated_champion(p), (None, 0))

    def test_heartbeat_rejects_stale_and_unsafe_state(self):
        with TemporaryDirectory() as d:
            state = Path(d)
            heartbeat(state, "running", 2)
            self.assertTrue(healthy(state))
            data = json.loads((state / "heartbeat.json").read_text())
            data["timestamp_utc"] = (datetime.now(timezone.utc) -
                                      timedelta(hours=2)).isoformat()
            write_json_atomic(state / "heartbeat.json", data)
            self.assertFalse(healthy(state))
            data["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
            data["real_world_actions_enabled"] = True
            write_json_atomic(state / "heartbeat.json", data)
            self.assertFalse(healthy(state))

    def test_cycle_keeps_old_champion_if_candidate_raises(self):
        with TemporaryDirectory() as d:
            state = Path(d)
            initialize(state)
            write_json_atomic(state / "champion.json", no_champion())
            original = (state / "champion.json").read_bytes()
            with patch("always_on_worker.self_improve", side_effect=RuntimeError("failed")):
                with self.assertRaises(RuntimeError):
                    run_one_cycle(state, run_key=44)
            self.assertEqual((state / "champion.json").read_bytes(), original)
            import sqlite3
            with sqlite3.connect(state / "audit.sqlite3") as c:
                self.assertEqual(c.execute(
                    "SELECT outcome FROM cycles WHERE run_key = 44").fetchone()[0],
                    "error")

    def test_success_persists_only_validated_research_data(self):
        with TemporaryDirectory() as d:
            state = Path(d)
            initialize(state)
            def verified(run_key, output, previous, **kwargs):
                output.mkdir(parents=True)
                write_json_atomic(output / "champion.json", no_champion())
                write_json_atomic(output / "training_seed.json", {
                    "schema": 1, "research_only": True, "training_seed_only": True,
                    "recipe": {"features": ["minimum"], "weights": [1],
                               "proposal": "local", "explorer": "steady",
                               "anchor": "best"},
                    "automatic_source_merge_allowed": False,
                    "real_world_application_allowed": False,
                })
                return {
                    "run_key": run_key,
                    "proposal_accepted_as_research_recipe": False,
                    "champion_generation": 0,
                    "real_world_actions": 0,
                    "code_merges_or_deployments": 0,
                }
            with patch("always_on_worker.self_improve", side_effect=verified):
                outcome = run_one_cycle(state, run_key=55)
            self.assertFalse(outcome["proposal_accepted_as_research_recipe"])
            self.assertEqual(read_validated_champion(state / "champion.json"),
                             (None, 0))
            self.assertTrue((state / "audit.sqlite3").is_file())
            self.assertTrue((state / "training_seed.json").is_file())
            self.assertFalse(read_validated_champion(state / "champion.json")[0])

    def test_worker_rejects_corrupt_persistent_training_state(self):
        with TemporaryDirectory() as d:
            state = Path(d)
            initialize(state)
            write_json_atomic(state / "training_seed.json", {
                "schema": 1, "research_only": True,
                "training_seed_only": True,
                "recipe": {"features": ["os.system"], "weights": [1],
                           "proposal": "local", "explorer": "steady",
                           "anchor": "best"},
                "automatic_source_merge_allowed": False,
                "real_world_application_allowed": False,
            })
            with self.assertRaises(ValueError):
                run_one_cycle(state, run_key=999)

    def test_cycle_rejects_false_promotion_claim(self):
        with TemporaryDirectory() as d:
            state = Path(d)
            initialize(state)
            def false_promotion(run_key, output, previous, **kwargs):
                output.mkdir(parents=True)
                write_json_atomic(output / "champion.json", no_champion())
                return {
                    "run_key": run_key,
                    "proposal_accepted_as_research_recipe": True,
                    "champion_generation": 1,
                    "real_world_actions": 0,
                    "code_merges_or_deployments": 0,
                }
            with patch("always_on_worker.self_improve", side_effect=false_promotion):
                with self.assertRaises(AssertionError):
                    run_one_cycle(state, run_key=56)
            self.assertFalse((state / "champion.json").exists())

    def test_archive_retention_is_bounded(self):
        with TemporaryDirectory() as d:
            archive = Path(d)
            for i in range(30):
                (archive / str(i)).mkdir()
            (archive / "important-not-ours").mkdir()
            prune_archives(archive)
            self.assertEqual(len([p for p in archive.iterdir()
                                  if p.name.isdecimal()]), 16)
            self.assertTrue((archive / "important-not-ours").exists())

    def test_actual_loop_can_run_one_cycle_and_stop(self):
        with TemporaryDirectory() as d:
            with patch("always_on_worker.run_one_cycle", return_value={
                "run_key": 19,
                "proposal_accepted_as_research_recipe": False,
                "champion_generation": 0,
            }) as mocked:
                serve(Path(d), limit=1, pause_seconds=0)
            self.assertEqual(mocked.call_count, 1)
            self.assertTrue(healthy(Path(d)))

    def test_untrusted_stop_date_cannot_extend_six_months(self):
        with TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                serve(Path(d), limit=1, stop_date=date(2028, 1, 1))


if __name__ == "__main__":
    unittest.main()
