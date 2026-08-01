"""Hop-budget support for the SDD auto-spawn handoff (cmux-spawn-v2).

SSOT for the Decision 9 formula, derivation precedence, tasks_done counting
and stall streaks. Consumers: materialize-manifest.py (import) and
spawn-handoff-session.sh (CLI via $PYTHON — see Task 7). Follows the
_midpoint.py precedent: one home for a formula two callers would otherwise
duplicate. Stdlib-only at import time; PyYAML is imported lazily where needed."""

import glob
import json
import math
import os
import re
import sys

HOP_DIVISOR = 2.5
CEILING_FLOOR = 6
CEILING_FACTOR = 2


def expected_hops(total_tasks, tier):
    """Decision 9: ceil(total/2.5) standard; 1 micro. Raises on garbage —
    callers that must degrade catch ValueError (never divide by garbage)."""
    if tier == "micro":
        return 1
    if (
        not isinstance(total_tasks, int)
        or isinstance(total_tasks, bool)
        or total_tasks <= 0
    ):
        raise ValueError(f"total_tasks must be a positive int, got {total_tasks!r}")
    return math.ceil(total_tasks / HOP_DIVISOR)


def derive_total_tasks(manifest):
    """Pinned input precedence (spec Contract Facts): (1) validated manifest
    total_tasks; (2) union of unique module task IDs; (3) inclusive active
    task_range. Returns None when nothing is derivable (absent-with-warning)."""
    t = manifest.get("total_tasks")
    if isinstance(t, int) and not isinstance(t, bool) and t > 0:
        return t
    ids = set()
    for m in manifest.get("modules") or []:
        if isinstance(m, dict):
            for tid in m.get("task_ids") or []:
                if isinstance(tid, int) and not isinstance(tid, bool):
                    ids.add(tid)
    if ids:
        return len(ids)
    tr = manifest.get("task_range")
    if (
        isinstance(tr, (list, tuple))
        and len(tr) == 2
        and all(isinstance(x, int) and not isinstance(x, bool) for x in tr)
        and tr[0] <= tr[1]
    ):
        return tr[1] - tr[0] + 1
    return None


def derive_expected_hops(manifest):
    """Manifest handoff.expected_hops when valid; else re-derive; else None."""
    h = manifest.get("handoff") or {}
    eh = h.get("expected_hops") if isinstance(h, dict) else None
    if isinstance(eh, int) and not isinstance(eh, bool) and eh >= 1:
        return eh
    total = derive_total_tasks(manifest)
    if total is None:
        return None
    return expected_hops(total, manifest.get("tier") or "standard")


def hop_ceiling(exp):
    """Derived ceiling default: max(6, 2 x expected). None -> floor."""
    if exp is None:
        return CEILING_FLOOR
    return max(CEILING_FLOOR, CEILING_FACTOR * exp)


_REPORT_GLOB = "task-*-implementer-report*.md"
_DONE_STATUSES = ("DONE", "DONE_WITH_CONCERNS")


def _require_yaml():
    """Import PyYAML, letting ImportError PROPAGATE: a yaml-less python3 must not
    fake "0 done". The import stays FUNCTION-LOCAL on purpose — hoisting it to
    module scope breaks the stdlib-only-at-import property this module's docstring
    promises (P7-9(B); pinned by test_yaml_import_stays_lazy_*)."""
    import yaml

    return yaml


def _frontmatter(text, yaml_mod=None):
    yaml = yaml_mod if yaml_mod is not None else _require_yaml()
    if not text.startswith("---"):
        return None
    end = text.find("---", 3)
    if end == -1:
        return None
    try:
        fm = yaml.safe_load(text[3:end])
    except Exception:
        return None
    return fm if isinstance(fm, dict) else None


def count_tasks_done(reports_dir):
    """Unique task IDs across reports/ + archive-*/ with parsing frontmatter AND
    completed status. Filenames/BLOCKED/malformed/dupes never inflate progress."""
    # P7-3: probe the import ONCE, BEFORE the glob. Reached only inside the loop,
    # a zero-match reports/ never fires the ImportError and the CLI prints a FAKE
    # `0` — and a fake 0 fed to the stall gate makes every hop look like zero
    # progress, MANUFACTURING a stall. Degradation must not depend on the glob.
    yaml_mod = _require_yaml()
    done = set()
    patterns = [
        os.path.join(reports_dir, _REPORT_GLOB),
        os.path.join(reports_dir, "archive-*", _REPORT_GLOB),
    ]
    for pat in patterns:
        for path in glob.glob(pat):
            try:
                fm = _frontmatter(open(path, encoding="utf-8").read(), yaml_mod)
            except (OSError, UnicodeDecodeError):
                # P7-6: UnicodeDecodeError subclasses ValueError, NOT OSError, so
                # one non-UTF-8 byte in any report used to escape this `continue`
                # and exit 1 with empty stdout — neither a value nor exit 0.
                # SKIPPING (rather than errors="replace") is the fail-closed
                # direction: an undercount biases toward a spurious stall refusal,
                # while a decoded-garbage count biases toward disabling the guard.
                continue
            if not fm:
                continue
            tid = fm.get("task_id")
            if (
                isinstance(tid, int)
                and not isinstance(tid, bool)
                and fm.get("status") in _DONE_STATUSES
            ):
                done.add(tid)
    return len(done)


_OUTCOME_RE = re.compile(r"^\S+ \S+ outcome ")


def stall_streak(spawn_log_path, current_tasks_done):
    """Trailing consecutive outcome records whose tasks_done == current count. 0 = progress or
    first hop. 'indeterminate' = newest outcome missing/malformed on tasks_done; caller SKIPs."""
    try:
        lines = open(spawn_log_path, encoding="utf-8").read().splitlines()
    except FileNotFoundError:
        return 0  # no log yet: first hop
    except (OSError, UnicodeDecodeError):
        # P7-8: an unreadable/corrupt log is NOT "no stall". Returning 0 here
        # silently DISABLED the runaway-stall guard, and 0 is invisible because it
        # is also the legitimate first-hop/progress answer. The FileNotFoundError
        # arm above MUST stay first — it subclasses OSError, and reversing the two
        # turns every legitimate first hop into `indeterminate`.
        return "indeterminate"
    outcomes = [l for l in lines if _OUTCOME_RE.match(l)]
    if not outcomes:
        return 0
    streak = 0
    for line in reversed(outcomes):
        m = re.search(r"\btasks_done=(\d+)\b", line)
        if m is None:
            return "indeterminate" if streak == 0 else streak
        if int(m.group(1)) == current_tasks_done:
            streak += 1
        else:
            break
    return streak


def _cli(argv):
    """CLI for spawn-handoff-session.sh: ONE value on stdout; exit 0 with a value
    ('unknown'/'indeterminate' count), exit 2 = usage. Spec pins only READABLE-but-
    absent-block -> 'auto'; unreadable fails CLOSED to 'ask' (sole consent gate)."""
    import argparse

    p = argparse.ArgumentParser(prog="_handoff_support.py")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("tasks-done").add_argument("--reports-dir", required=True)
    sub.add_parser("expected-hops").add_argument("--manifest", required=True)
    s3 = sub.add_parser("stall-streak")
    s3.add_argument("--spawn-log", required=True)
    s3.add_argument("--tasks-done", required=True, type=int)
    sub.add_parser("spawn-policy").add_argument("--manifest", required=True)
    a = p.parse_args(argv)
    if a.cmd == "tasks-done":
        try:
            print(count_tasks_done(a.reports_dir))
        except ImportError:
            print(
                "unknown"
            )  # missing PyYAML degrades observably — a fake 0 manufactures stalls
        return 0
    if a.cmd == "stall-streak":
        print(stall_streak(a.spawn_log, a.tasks_done))
        return 0
    try:
        manifest = json.load(open(a.manifest, encoding="utf-8"))
    except Exception:
        manifest = None  # unreadable: consent must not default OPEN
    if not isinstance(manifest, dict):
        manifest = None  # valid JSON that isn't an object
    if a.cmd == "expected-hops":
        eh = derive_expected_hops(manifest or {})
        print("unknown" if eh is None else eh)
        return 0
    # spawn-policy — the SOLE consent gate for automated spawning. P7-1(ii): a
    # PRESENT but invalid declaration ("OFF", "Off", false, null, a non-dict
    # handoff) used to print `auto`, so a refusal expressed in the wrong case was
    # silently inverted into CONSENT. Fail CLOSED to `ask` (retryable, and the
    # shell consumes it pre-reservation, so no hop is consumed).
    #
    # Key PRESENCE, not `.get()`, is the discriminator: an absent `handoff` key
    # and `handoff: null` both yield None through `.get()`, yet they must resolve
    # differently. Absent key == a pre-v2 manifest, the ONE permissive case — every
    # legacy handoff ships without a handoff block and must still spawn.
    if manifest is None:
        print("ask")  # unreadable / valid-JSON-non-object
        return 0
    if "handoff" not in manifest:
        print("auto")  # pre-v2 manifest: legacy must still spawn
        return 0
    h = manifest["handoff"]
    pol = h.get("spawn_policy") if isinstance(h, dict) else None
    print(pol if pol in ("auto", "ask", "off") else "ask")
    return 0


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))
