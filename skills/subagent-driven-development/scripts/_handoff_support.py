"""Hop-budget support for the SDD auto-spawn handoff (cmux-spawn-v2).

SSOT for the Decision 9 formula, derivation precedence, tasks_done counting
and stall streaks. Consumers: materialize-manifest.py (import) and
spawn-handoff-session.sh (CLI via $PYTHON — see Task 7). Follows the
_midpoint.py precedent: one home for a formula two callers would otherwise
duplicate. Stdlib-only at import time; PyYAML is imported lazily where needed."""
import math

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
