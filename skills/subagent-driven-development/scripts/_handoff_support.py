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
    if not isinstance(total_tasks, int) or isinstance(total_tasks, bool) or total_tasks <= 0:
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
    if (isinstance(tr, (list, tuple)) and len(tr) == 2
            and all(isinstance(x, int) and not isinstance(x, bool) for x in tr)
            and tr[0] <= tr[1]):
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


def _frontmatter(text):
    import yaml   # ImportError PROPAGATES: a venv-less python3 must not fake "0 done"
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
    done = set()
    patterns = [os.path.join(reports_dir, _REPORT_GLOB),
                os.path.join(reports_dir, "archive-*", _REPORT_GLOB)]
    for pat in patterns:
        for path in glob.glob(pat):
            try:
                fm = _frontmatter(open(path, encoding="utf-8").read())
            except OSError:
                continue
            if not fm:
                continue
            tid = fm.get("task_id")
            if (isinstance(tid, int) and not isinstance(tid, bool)
                    and fm.get("status") in _DONE_STATUSES):
                done.add(tid)
    return len(done)


_OUTCOME_RE = re.compile(r"^\S+ \S+ outcome ")


def stall_streak(spawn_log_path, current_tasks_done):
    """Trailing consecutive outcome records whose tasks_done == current count. 0 = progress or
    first hop. 'indeterminate' = newest outcome missing/malformed on tasks_done; caller SKIPs."""
    try:
        lines = open(spawn_log_path, encoding="utf-8").read().splitlines()
    except OSError:
        return 0                                  # no log yet: first hop
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
            print("unknown")   # missing PyYAML degrades observably — a fake 0 manufactures stalls
        return 0
    if a.cmd == "stall-streak":
        print(stall_streak(a.spawn_log, a.tasks_done))
        return 0
    try:
        manifest = json.load(open(a.manifest, encoding="utf-8"))
    except Exception:
        manifest = None                    # unreadable: consent must not default OPEN
    if not isinstance(manifest, dict):
        manifest = None                    # valid JSON that isn't an object
    if a.cmd == "expected-hops":
        eh = derive_expected_hops(manifest or {})
        print("unknown" if eh is None else eh)
        return 0
    h = (manifest or {}).get("handoff")
    pol = h.get("spawn_policy") if isinstance(h, dict) else None   # unreadable -> "ask"
    print(pol if pol in ("auto", "ask", "off") else ("auto" if manifest is not None else "ask"))
    return 0


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))
