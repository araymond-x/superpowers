"""Shared midpoint computation for SDD scripts.

This is the single source of truth for the midpoint formula used by
materialize-manifest.py (initial materialization) and transition-module.py
(module transition). Plan reference code in this repo has historically
shipped a buggy `range_size = end - start + 1` formula that produces
midpoints outside `task_range` for small ranges (failing the Pydantic
`midpoint_in_range` validator). That bug surfaced in three separate tasks
(deviations.md rows for Tasks 4, 11, 12) before this helper was extracted.

Do not duplicate this logic. Import it.
"""


def compute_midpoint(start: int, end: int) -> int:
    """Compute the midpoint of a task range.

    Formula: ``start + (range_size + 1) // 2``, where ``range_size = end - start``.
    This gives a ceiling-biased midpoint that stays inside ``[start, end]`` for
    all range sizes (including single-task and two-task ranges).

    Args:
        start: First task ID in the range (inclusive).
        end: Last task ID in the range (inclusive).

    Returns:
        A task ID in ``[start, end]`` representing the ceiling-biased midpoint.
        Satisfies the ``midpoint_in_range`` Pydantic validator on
        ``SddSession.midpoint`` for any valid ``task_range``.
    """
    range_size = end - start
    return start + (range_size + 1) // 2
