"""_handoff_support.py — formula, precedence, degradation."""
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent.parent / "skills" / "subagent-driven-development" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from _handoff_support import (  # noqa: E402
    HOP_DIVISOR, CEILING_FLOOR, CEILING_FACTOR,
    expected_hops, derive_total_tasks, derive_expected_hops, hop_ceiling,
)

import subprocess

VENV_PY = str(Path(__file__).resolve().parent.parent.parent / ".venv" / "bin" / "python3")
SUPPORT = str(SCRIPTS / "_handoff_support.py")


def _write_report(d, task_id, status, task_type="implementation", name=None,
                  files_changed="[{path: x, description: y}]"):
    # files_changed defaults NON-EMPTY: ImplementerReport rejects DONE /
    # DONE_WITH_CONCERNS with an empty list. Pass files_changed="[]" to
    # exercise the task_type=="verification" exemption.
    d.mkdir(parents=True, exist_ok=True)
    body = (f"---\nschema_version: 1\ntask_id: {task_id}\nstatus: {status}\n"
            f"task_type: {task_type}\nfiles_changed: {files_changed}\n"
            "tests: {written: 0, passing: 0, command: x, result: PASS}\n---\nbody\n")
    (d / (name or f"task-{task_id:03d}-implementer-report.md")).write_text(body)


def _log(lines):
    return "".join(l + "\n" for l in lines)


class TestExpectedHops:
    def test_formula_standard(self):
        assert expected_hops(1, "standard") == 1
        assert expected_hops(5, "standard") == 2      # ceil(5/2.5)
        assert expected_hops(19, "standard") == 8     # ceil(19/2.5)
        assert expected_hops(6, "standard") == 3      # ceil(2.4)=3; round() would give 2

    def test_micro_is_one(self):
        assert expected_hops(19, "micro") == 1

    def test_unknown_tier_behaves_as_standard(self):
        # only "micro" short-circuits; a `tier != "standard"` test would give 1, not 8
        assert expected_hops(19, "weird") == 8      # unknown tier behaves as standard

    def test_invalid_total_raises(self):
        import pytest
        for bad in (0, -3, "7", None, True):
            with pytest.raises(ValueError):
                expected_hops(bad, "standard")


class TestDeriveTotalTasks:
    def test_precedence_1_manifest_total(self):
        assert derive_total_tasks({"total_tasks": 12, "modules": [{"task_ids": [1]}]}) == 12

    def test_precedence_2_module_union_dedupes(self):
        m = {"total_tasks": 0,
             "modules": [{"task_ids": [0, 1, 2]}, {"task_ids": [2, 3]}]}
        assert derive_total_tasks(m) == 4

    def test_precedence_3_task_range_inclusive(self):
        assert derive_total_tasks({"total_tasks": None, "modules": [], "task_range": [3, 7]}) == 5

    def test_all_invalid_returns_none(self):
        assert derive_total_tasks({"total_tasks": 0, "modules": [], "task_range": [7, 3]}) is None

    def test_module_union_beats_task_range(self):
        m = {"total_tasks": 0, "modules": [{"task_ids": [0, 1, 2]}], "task_range": [0, 20]}
        assert derive_total_tasks(m) == 3

    def test_bool_never_counts_as_a_total_or_a_task_id(self):
        assert derive_total_tasks({"total_tasks": True, "modules": [], "task_range": [1, 4]}) == 4
        assert derive_total_tasks({"total_tasks": 0, "modules": [{"task_ids": [True, 2]}]}) == 1

    def test_bool_in_task_range_is_not_derivable(self):
        # 4th bool guard: dropping it derives 4 - True + 1 == 4 instead of None
        assert derive_total_tasks({"total_tasks": 0, "modules": [], "task_range": [True, 4]}) is None

    def test_wrong_length_task_range_is_not_derivable(self):
        assert derive_total_tasks({"total_tasks": 0, "modules": [], "task_range": [1, 2, 3]}) is None

    def test_single_task_range_is_inclusive(self):
        assert derive_total_tasks({"total_tasks": 0, "modules": [], "task_range": [5, 5]}) == 1


class TestDeriveExpectedHops:
    def test_valid_block_wins(self):
        assert derive_expected_hops({"handoff": {"expected_hops": 9}, "total_tasks": 5}) == 9

    def test_absent_block_derives(self):
        assert derive_expected_hops({"total_tasks": 5, "tier": "standard"}) == 2

    def test_tier_propagates_from_manifest(self):
        # tier reaches expected_hops from the manifest; hardcoding "standard" gives 8, not 1
        assert derive_expected_hops({"total_tasks": 19, "tier": "micro"}) == 1

    def test_underivable_returns_none(self):
        assert derive_expected_hops({"total_tasks": 0}) is None

    def test_invalid_block_values_are_rederived_not_trusted(self):
        assert derive_expected_hops({"handoff": {"expected_hops": 0}, "total_tasks": 5}) == 2
        assert derive_expected_hops({"handoff": {"expected_hops": True}, "total_tasks": 5}) == 2


class TestHopCeiling:
    def test_floor_factor_and_none(self):
        assert hop_ceiling(2) == 6                    # max(6, 4)
        assert hop_ceiling(8) == 16
        assert hop_ceiling(None) == CEILING_FLOOR


class TestTasksDone:
    def test_done_and_concerns_count_blocked_and_malformed_do_not(self, tmp_path):
        from _handoff_support import count_tasks_done
        r = tmp_path / "reports"
        _write_report(r, 1, "DONE", task_type="verification", files_changed="[]")
        _write_report(r, 2, "DONE_WITH_CONCERNS")
        _write_report(r, 3, "BLOCKED")
        (r / "task-005-implementer-report.md").write_text("no frontmatter at all")
        assert count_tasks_done(str(r)) == 2                    # filename alone never counts

    def test_archives_counted_and_duplicates_deduped(self, tmp_path):
        from _handoff_support import count_tasks_done
        r = tmp_path / "reports"
        _write_report(r, 4, "DONE")
        _write_report(r / "archive-module-1", 1, "DONE")
        _write_report(r / "archive-module-1", 4, "DONE")        # dupe of live task 4
        assert count_tasks_done(str(r)) == 2                    # {1, 4}


class TestStallStreak:
    OUT = "2026-07-30T00:00:0{i}Z u{i} outcome hop={i} workspace=w surface=s launch=auto bundle=b quota=ok tasks_done={td} handshake=ok"

    def _streak(self, tmp_path, rows, current):
        f = tmp_path / "handoff-spawn.log"
        f.write_text(_log(rows))
        from _handoff_support import stall_streak
        return stall_streak(str(f), current)

    def test_first_hop_and_progress_are_zero(self, tmp_path):
        assert self._streak(tmp_path, [], 0) == 0
        rows = [self.OUT.format(i=1, td=2), self.OUT.format(i=2, td=4)]
        assert self._streak(tmp_path, rows, 5) == 0

    def test_one_stall_then_two_consecutive(self, tmp_path):
        rows = [self.OUT.format(i=1, td=2), self.OUT.format(i=2, td=4)]
        assert self._streak(tmp_path, rows, 4) == 1
        rows = [self.OUT.format(i=1, td=4), self.OUT.format(i=2, td=4)]
        assert self._streak(tmp_path, rows, 4) == 2

    def test_malformed_last_outcome_is_indeterminate(self, tmp_path):
        rows = ["2026-07-30T00:00:01Z u1 outcome hop=1 workspace=w launch=auto"]  # no tasks_done=
        assert self._streak(tmp_path, rows, 3) == "indeterminate"


class TestCli:
    def _run(self, *args):
        return subprocess.run([VENV_PY, SUPPORT, *args], capture_output=True, text=True)

    def test_tasks_done_cli(self, tmp_path):
        r = tmp_path / "reports"
        _write_report(r, 1, "DONE")
        out = self._run("tasks-done", "--reports-dir", str(r))
        assert out.returncode == 0 and out.stdout.strip() == "1"

    def test_expected_hops_and_policy_cli_on_legacy_and_garbage(self, tmp_path):
        m = tmp_path / "m.json"
        m.write_text('{"total_tasks": 5, "tier": "standard"}')   # pre-v2: no handoff block
        assert self._run("expected-hops", "--manifest", str(m)).stdout.strip() == "2"
        assert self._run("spawn-policy", "--manifest", str(m)).stdout.strip() == "auto"
        m.write_text('{"total_tasks": 0}')
        assert self._run("expected-hops", "--manifest", str(m)).stdout.strip() == "unknown"
        assert self._run("spawn-policy", "--manifest", str(tmp_path / "no.json")).stdout.strip() == "ask"   # fails CLOSED
