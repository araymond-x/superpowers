"""_handoff_support.py — formula, precedence, degradation."""

import sys
from pathlib import Path

SCRIPTS = (
    Path(__file__).resolve().parent.parent.parent
    / "skills"
    / "subagent-driven-development"
    / "scripts"
)
sys.path.insert(0, str(SCRIPTS))

from _handoff_support import (  # noqa: E402
    CEILING_FLOOR,
    expected_hops,
    derive_total_tasks,
    derive_expected_hops,
    hop_ceiling,
)

import subprocess

VENV_PY = str(
    Path(__file__).resolve().parent.parent.parent / ".venv" / "bin" / "python3"
)
SUPPORT = str(SCRIPTS / "_handoff_support.py")


def _write_report(
    d,
    task_id,
    status,
    task_type="implementation",
    name=None,
    files_changed="[{path: x, description: y}]",
):
    # files_changed defaults NON-EMPTY: ImplementerReport rejects DONE /
    # DONE_WITH_CONCERNS with an empty list. Pass files_changed="[]" to
    # exercise the task_type=="verification" exemption.
    d.mkdir(parents=True, exist_ok=True)
    body = (
        f"---\nschema_version: 1\ntask_id: {task_id}\nstatus: {status}\n"
        f"task_type: {task_type}\nfiles_changed: {files_changed}\n"
        "tests: {written: 0, passing: 0, command: x, result: PASS}\n---\nbody\n"
    )
    (d / (name or f"task-{task_id:03d}-implementer-report.md")).write_text(body)


def _log(lines):
    return "".join(l + "\n" for l in lines)


def _noyaml_env(tmp_path):
    """Environment whose `import yaml` raises ImportError.

    A bare/system interpreter is NOT a valid probe for the yaml-less path: both
    /usr/bin/python3 and this repo's .venv ship PyYAML, so the naive probe passes
    for the wrong reason. Shadow the module on PYTHONPATH instead. Every test
    using this carries its own positive control that the shadow really bites.
    """
    import os

    shadow = tmp_path / "noyaml"
    shadow.mkdir(exist_ok=True)
    (shadow / "yaml.py").write_text("raise ImportError('shadowed: no yaml here')\n")
    env = dict(os.environ)
    env["PYTHONPATH"] = str(shadow)
    return env


class TestExpectedHops:
    def test_formula_standard(self):
        assert expected_hops(1, "standard") == 1
        assert expected_hops(5, "standard") == 2  # ceil(5/2.5)
        assert expected_hops(19, "standard") == 8  # ceil(19/2.5)
        assert expected_hops(6, "standard") == 3  # ceil(2.4)=3; round() would give 2

    def test_micro_is_one(self):
        assert expected_hops(19, "micro") == 1

    def test_unknown_tier_behaves_as_standard(self):
        # only "micro" short-circuits; a `tier != "standard"` test would give 1, not 8
        assert expected_hops(19, "weird") == 8  # unknown tier behaves as standard

    def test_invalid_total_raises(self):
        import pytest

        for bad in (0, -3, "7", None, True):
            with pytest.raises(ValueError):
                expected_hops(bad, "standard")


class TestDeriveTotalTasks:
    def test_precedence_1_manifest_total(self):
        assert (
            derive_total_tasks({"total_tasks": 12, "modules": [{"task_ids": [1]}]})
            == 12
        )

    def test_precedence_2_module_union_dedupes(self):
        m = {
            "total_tasks": 0,
            "modules": [{"task_ids": [0, 1, 2]}, {"task_ids": [2, 3]}],
        }
        assert derive_total_tasks(m) == 4

    def test_precedence_3_task_range_inclusive(self):
        assert (
            derive_total_tasks(
                {"total_tasks": None, "modules": [], "task_range": [3, 7]}
            )
            == 5
        )

    def test_all_invalid_returns_none(self):
        assert (
            derive_total_tasks({"total_tasks": 0, "modules": [], "task_range": [7, 3]})
            is None
        )

    def test_module_union_beats_task_range(self):
        m = {
            "total_tasks": 0,
            "modules": [{"task_ids": [0, 1, 2]}],
            "task_range": [0, 20],
        }
        assert derive_total_tasks(m) == 3

    def test_bool_never_counts_as_a_total_or_a_task_id(self):
        assert (
            derive_total_tasks(
                {"total_tasks": True, "modules": [], "task_range": [1, 4]}
            )
            == 4
        )
        assert (
            derive_total_tasks({"total_tasks": 0, "modules": [{"task_ids": [True, 2]}]})
            == 1
        )

    def test_bool_in_task_range_is_not_derivable(self):
        # 4th bool guard: dropping it derives 4 - True + 1 == 4 instead of None
        assert (
            derive_total_tasks(
                {"total_tasks": 0, "modules": [], "task_range": [True, 4]}
            )
            is None
        )

    def test_wrong_length_task_range_is_not_derivable(self):
        assert (
            derive_total_tasks(
                {"total_tasks": 0, "modules": [], "task_range": [1, 2, 3]}
            )
            is None
        )

    def test_single_task_range_is_inclusive(self):
        assert (
            derive_total_tasks({"total_tasks": 0, "modules": [], "task_range": [5, 5]})
            == 1
        )


class TestDeriveExpectedHops:
    def test_valid_block_wins(self):
        assert (
            derive_expected_hops({"handoff": {"expected_hops": 9}, "total_tasks": 5})
            == 9
        )

    def test_absent_block_derives(self):
        assert derive_expected_hops({"total_tasks": 5, "tier": "standard"}) == 2

    def test_tier_propagates_from_manifest(self):
        # tier reaches expected_hops from the manifest; hardcoding "standard" gives 8, not 1
        assert derive_expected_hops({"total_tasks": 19, "tier": "micro"}) == 1

    def test_underivable_returns_none(self):
        assert derive_expected_hops({"total_tasks": 0}) is None

    def test_non_dict_handoff_block_is_rederived_not_crashed(self):
        # P7-9(D): the `isinstance(h, dict)` guard was unpinned here while its
        # _cli twin was pinned. Without it, `.get` on a list/str raises
        # AttributeError instead of falling through to re-derivation.
        assert derive_expected_hops({"handoff": [1, 2], "total_tasks": 5}) == 2
        assert derive_expected_hops({"handoff": "auto", "total_tasks": 5}) == 2

    def test_invalid_block_values_are_rederived_not_trusted(self):
        assert (
            derive_expected_hops({"handoff": {"expected_hops": 0}, "total_tasks": 5})
            == 2
        )
        assert (
            derive_expected_hops({"handoff": {"expected_hops": True}, "total_tasks": 5})
            == 2
        )


class TestHopCeiling:
    def test_floor_factor_and_none(self):
        assert hop_ceiling(2) == 6  # max(6, 4)
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
        # both task_id type guards: `no` is a YAML 1.1 boolean, "3" a string.
        # `no`/False (not `yes`/True) because hash(True) == hash(1) would dedupe
        # into the already-counted task 1 and let the bool mutation survive.
        _write_report(r, "no", "DONE", name="task-006-implementer-report.md")
        _write_report(r, '"3"', "DONE", name="task-007-implementer-report.md")
        assert count_tasks_done(str(r)) == 2  # filename alone never counts

    def test_archives_counted_and_duplicates_deduped(self, tmp_path):
        from _handoff_support import count_tasks_done

        r = tmp_path / "reports"
        _write_report(r, 4, "DONE")
        _write_report(r / "archive-module-1", 1, "DONE")
        _write_report(r / "archive-module-1", 4, "DONE")  # dupe of live task 4
        assert count_tasks_done(str(r)) == 2  # {1, 4}

    def test_non_mapping_and_invalid_yaml_frontmatter_are_skipped_not_raised(
        self, tmp_path
    ):
        from _handoff_support import count_tasks_done

        r = tmp_path / "reports"
        r.mkdir(parents=True)
        (r / "task-008-implementer-report.md").write_text("---\n- a\n- b\n---\nbody\n")
        (r / "task-009-implementer-report.md").write_text(
            "---\nkey: [unclosed\n---\nbody\n"
        )
        assert count_tasks_done(str(r)) == 0  # crash path, not a permissiveness path

    def test_non_utf8_report_is_skipped_not_raised(self, tmp_path):
        # P7-6: UnicodeDecodeError subclasses ValueError, not OSError, so one bad
        # byte in ANY report used to escape the `continue` and crash the CLI.
        from _handoff_support import count_tasks_done

        r = tmp_path / "reports"
        _write_report(r, 1, "DONE")
        (r / "task-002-implementer-report.md").write_bytes(
            b"---\nschema_version: 1\ntask_id: 2\nstatus: DONE\nnote: \xff\xfe\n---\nbody\n"
        )
        assert count_tasks_done(str(r)) == 1  # the good report still counts


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
        rows = [
            "2026-07-30T00:00:01Z u1 outcome hop=1 workspace=w launch=auto"
        ]  # no tasks_done=
        assert self._streak(tmp_path, rows, 3) == "indeterminate"

    def test_intent_rows_between_outcomes_do_not_break_the_streak(self, tmp_path):
        rows = [
            "2026-07-30T00:00:01Z u1 intent hop=1",
            self.OUT.format(i=2, td=4),
            "2026-07-30T00:00:03Z u2 intent hop=2",
            self.OUT.format(i=4, td=4),
        ]
        assert (
            self._streak(tmp_path, rows, 4) == 2
        )  # real logs ALWAYS interleave intent

    def test_malformed_older_outcome_truncates_rather_than_indeterminate(
        self, tmp_path
    ):
        # indeterminate is correct ONLY when the NEWEST record is malformed
        rows = [
            "2026-07-30T00:00:01Z u1 outcome hop=1 workspace=w launch=auto",  # no tasks_done=
            self.OUT.format(i=2, td=4),
            self.OUT.format(i=3, td=4),
        ]
        assert self._streak(tmp_path, rows, 4) == 2

    def test_unreadable_log_is_indeterminate_and_missing_log_is_still_zero(
        self, tmp_path
    ):
        # P7-8. The PAIR is the point: `indeterminate` alone passes even under a
        # blanket `except OSError: return "indeterminate"`, which would break the
        # legitimate first-hop 0. FileNotFoundError subclasses OSError, so only
        # this second assertion pins the handler ORDER.
        from _handoff_support import stall_streak

        unreadable = tmp_path / "log-is-a-directory"
        unreadable.mkdir()
        assert stall_streak(str(unreadable), 3) == "indeterminate"
        assert stall_streak(str(tmp_path / "never-written.log"), 3) == 0


class TestCli:
    def _run(self, *args, env=None):
        return subprocess.run(
            [VENV_PY, SUPPORT, *args], capture_output=True, text=True, env=env
        )

    def test_tasks_done_cli(self, tmp_path):
        r = tmp_path / "reports"
        _write_report(r, 1, "DONE")
        out = self._run("tasks-done", "--reports-dir", str(r))
        assert out.returncode == 0 and out.stdout.strip() == "1"

    def test_expected_hops_and_policy_cli_on_legacy_and_garbage(self, tmp_path):
        m = tmp_path / "m.json"
        m.write_text(
            '{"total_tasks": 5, "tier": "standard"}'
        )  # pre-v2: no handoff block
        assert self._run("expected-hops", "--manifest", str(m)).stdout.strip() == "2"
        assert self._run("spawn-policy", "--manifest", str(m)).stdout.strip() == "auto"
        m.write_text('{"total_tasks": 0}')
        assert (
            self._run("expected-hops", "--manifest", str(m)).stdout.strip() == "unknown"
        )
        assert (
            self._run(
                "spawn-policy", "--manifest", str(tmp_path / "no.json")
            ).stdout.strip()
            == "ask"
        )  # fails CLOSED
        m.write_text(
            '{"total_tasks": 5, "handoff": {"expected_hops": 2, "spawn_policy": "off"}}'
        )
        assert (
            self._run("spawn-policy", "--manifest", str(m)).stdout.strip() == "off"
        )  # declared refusal is HONORED
        m.write_text(
            '{"total_tasks": 5, "handoff": {"expected_hops": 2, "spawn_policy": "ask"}}'
        )
        assert self._run("spawn-policy", "--manifest", str(m)).stdout.strip() == "ask"

    # ── P7-2: stall-streak had ZERO CLI coverage — and it is the very subcommand
    # the Module 3 stall gate invokes. ──────────────────────────────────────────

    def test_stall_streak_cli_reports_the_streak(self, tmp_path):
        log = tmp_path / "handoff-spawn.log"
        rows = [
            TestStallStreak.OUT.format(i=1, td=4),
            TestStallStreak.OUT.format(i=2, td=4),
        ]
        log.write_text(_log(rows))
        out = self._run("stall-streak", "--spawn-log", str(log), "--tasks-done", "4")
        assert out.returncode == 0 and out.stdout.strip() == "2"
        out = self._run("stall-streak", "--spawn-log", str(log), "--tasks-done", "5")
        assert out.returncode == 0 and out.stdout.strip() == "0"  # progress

    def test_stall_streak_cli_degraded_returns_are_values_at_exit_0(self, tmp_path):
        # P7-2 x P7-8: the new degraded return must be OBSERVABLE through the CLI
        # (Module 2's acceptance: values, exit 0), and the missing-log positive
        # control must ride in the same battery or the pin is vacuous.
        unreadable = tmp_path / "log-is-a-directory"
        unreadable.mkdir()
        out = self._run(
            "stall-streak", "--spawn-log", str(unreadable), "--tasks-done", "3"
        )
        assert out.returncode == 0 and out.stdout.strip() == "indeterminate"
        out = self._run(
            "stall-streak",
            "--spawn-log",
            str(tmp_path / "absent.log"),
            "--tasks-done",
            "3",
        )
        assert out.returncode == 0 and out.stdout.strip() == "0"
        malformed = tmp_path / "malformed.log"
        malformed.write_text(
            "2026-07-30T00:00:01Z u1 outcome hop=1 workspace=w launch=auto\n"
        )
        out = self._run(
            "stall-streak", "--spawn-log", str(malformed), "--tasks-done", "3"
        )
        assert out.returncode == 0 and out.stdout.strip() == "indeterminate"

    def test_stall_streak_cli_rejects_the_unknown_sentinel(self, tmp_path):
        # P7-4, pinned as a CONTRACT rather than closed as a bug: --tasks-done is
        # type=int, so piping `tasks-done`'s legitimate `unknown` straight in is
        # argparse exit 2. The shell MUST branch on `unknown` BEFORE calling this
        # (spawn-handoff-session.sh step (e) does). If this ever starts returning
        # 0, the shell's branch is no longer load-bearing — revisit deliberately.
        out = self._run(
            "stall-streak",
            "--spawn-log",
            str(tmp_path / "x.log"),
            "--tasks-done",
            "unknown",
        )
        assert out.returncode == 2

    # ── P7-1(ii) / P7-5: the SOLE consent gate fails CLOSED ────────────────────

    def test_spawn_policy_fails_closed_on_present_but_invalid_declarations(
        self, tmp_path
    ):
        # P7-1(ii). Every one of these printed `auto` before the fix, so a refusal
        # expressed in the wrong CASE was silently inverted into consent. The
        # shell's `*) SPAWN_POLICY="ask"` arm CANNOT cover this: `auto` is a
        # recognized value and matches its own case arm.
        m = tmp_path / "m.json"
        for body in (
            '{"total_tasks":5,"handoff":{"spawn_policy":"OFF"}}',
            '{"total_tasks":5,"handoff":{"spawn_policy":"Off"}}',
            '{"total_tasks":5,"handoff":{"spawn_policy":false}}',
            '{"total_tasks":5,"handoff":{"spawn_policy":null}}',
            '{"total_tasks":5,"handoff":{"expected_hops":2}}',
            '{"total_tasks":5,"handoff":null}',
            '{"total_tasks":5,"handoff":5}',
            '{"total_tasks":5,"handoff":[{"spawn_policy":"auto"}]}',
        ):
            m.write_text(body)
            assert (
                self._run("spawn-policy", "--manifest", str(m)).stdout.strip() == "ask"
            ), body

    def test_spawn_policy_legacy_manifest_still_consents(self, tmp_path):
        # REQUIRED positive control for the fix above — this is what forbids a
        # blanket fail-closed. A pre-v2 manifest has NO `handoff` KEY at all
        # (distinct from `handoff: null`, which `.get()` cannot tell apart) and
        # must still spawn, or every legacy handoff stops working.
        m = tmp_path / "m.json"
        m.write_text('{"total_tasks":5,"tier":"standard"}')
        assert self._run("spawn-policy", "--manifest", str(m)).stdout.strip() == "auto"
        m.write_text(
            '{"total_tasks":5,"handoff":{"expected_hops":2,"spawn_policy":"auto"}}'
        )
        assert self._run("spawn-policy", "--manifest", str(m)).stdout.strip() == "auto"

    def test_spawn_policy_on_valid_json_that_is_not_an_object(self, tmp_path):
        # P7-5: unpinned until now, and precisely where register row R3-2's
        # prescribed `manifest = {}` would have silently flipped these to `auto`.
        m = tmp_path / "m.json"
        for body in ("5", "null", "[1,2]", '"auto"', "true"):
            m.write_text(body)
            assert (
                self._run("spawn-policy", "--manifest", str(m)).stdout.strip() == "ask"
            ), body

    def test_expected_hops_on_unreadable_manifest_is_unknown(self, tmp_path):
        # P7-9(A): contract-pinning. Module 3's shell guards this call with -f,
        # 2>/dev/null and a regex fallback, so this is the contract, not a live risk.
        d = tmp_path / "manifest-is-a-directory"
        d.mkdir()
        out = self._run("expected-hops", "--manifest", str(d))
        assert out.returncode == 0 and out.stdout.strip() == "unknown"

    # ── P7-3 / P7-7: yaml-less degradation. TWO fixtures, ONE battery: a
    # populated dir already printed `unknown` BEFORE the P7-3 fix, so a test
    # built on one cannot detect whether P7-3 was fixed at all. ────────────────

    def test_tasks_done_degrades_to_unknown_without_yaml_even_on_an_empty_dir(
        self, tmp_path
    ):
        # P7-3's pin. `count_tasks_done` reached its lazy import only INSIDE the
        # glob loop, so zero matches meant the ImportError never fired and the CLI
        # printed a FAKE `0` — which, fed to the stall gate, manufactures a stall.
        env = _noyaml_env(tmp_path)
        empty = tmp_path / "reports"
        empty.mkdir()
        out = self._run("tasks-done", "--reports-dir", str(empty), env=env)
        assert out.returncode == 0 and out.stdout.strip() == "unknown", out.stderr
        absent = tmp_path / "no-such-reports"
        out = self._run("tasks-done", "--reports-dir", str(absent), env=env)
        assert out.returncode == 0 and out.stdout.strip() == "unknown", out.stderr
        # Positive control 1: the shadow really does break `import yaml`.
        ctrl = subprocess.run(
            [VENV_PY, "-c", "import yaml"], capture_output=True, text=True, env=env
        )
        assert ctrl.returncode != 0, (
            "yaml shadow is inert — every assertion above is vacuous"
        )
        # Positive control 2: WITH yaml, the same empty dir is a real `0`, not
        # `unknown` — so this test discriminates degradation from emptiness.
        assert (
            self._run("tasks-done", "--reports-dir", str(empty)).stdout.strip() == "0"
        )

    def test_tasks_done_prints_unknown_not_zero_when_yaml_is_absent(self, tmp_path):
        # P7-7: the `except ImportError: print("unknown")` mitigation itself was
        # unpinned — the mutation print("unknown") -> print(0) SURVIVED. This is
        # the POPULATED-dir case, which was already correct before P7-3; it is
        # P7-3's positive control, not a substitute for its pin.
        env = _noyaml_env(tmp_path)
        r = tmp_path / "reports"
        _write_report(r, 1, "DONE")
        out = self._run("tasks-done", "--reports-dir", str(r), env=env)
        assert out.returncode == 0 and out.stdout.strip() == "unknown", out.stderr
        # Positive control: the SAME dir with yaml available counts normally.
        assert self._run("tasks-done", "--reports-dir", str(r)).stdout.strip() == "1"

    def test_tasks_done_cli_exits_0_on_a_non_utf8_report(self, tmp_path):
        # P7-6 through the CLI: "degradation is observable" means a VALUE at exit
        # 0, and this path used to be a traceback at exit 1 with empty stdout.
        r = tmp_path / "reports"
        _write_report(r, 1, "DONE")
        (r / "task-002-implementer-report.md").write_bytes(
            b"---\nschema_version: 1\ntask_id: 2\nstatus: DONE\nnote: \xff\xfe\n---\nbody\n"
        )
        out = self._run("tasks-done", "--reports-dir", str(r))
        assert out.returncode == 0, out.stderr
        assert out.stdout.strip() == "1"


def test_yaml_import_stays_lazy_so_the_module_is_stdlib_only_at_import(tmp_path):
    """P7-9(B). Hoisting `import yaml` to module scope passes every other test in
    this file, and P7-3 edits that exact function — so without this nothing would
    catch a hoist. materialize-manifest.py imports this module, and the plan-
    validation gate runs sibling scripts with a bare `python3`."""
    env = _noyaml_env(tmp_path)
    probe = "import _handoff_support as h; print(h.hop_ceiling(None))"
    out = subprocess.run(
        [VENV_PY, "-c", probe],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(SCRIPTS),
    )
    assert out.returncode == 0, (
        f"module is no longer stdlib-only at import: {out.stderr}"
    )
    assert out.stdout.strip() == str(CEILING_FLOOR)
    ctrl = subprocess.run(
        [VENV_PY, "-c", "import yaml"], capture_output=True, text=True, env=env
    )
    assert ctrl.returncode != 0, "yaml shadow is inert — the assertion above is vacuous"
