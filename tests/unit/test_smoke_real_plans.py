"""Pre-ship smoke test: validate real plans against Pydantic schema.

Auto-discovers fixtures in tests/fixtures/_smoke-test-plans/.
Skipped if the directory is empty or missing (post-merge state).
"""

import subprocess

import pytest
from pathlib import Path

VALIDATORS_PATH = str(
    Path(__file__).resolve().parent.parent.parent
    / "skills"
    / "scripts"
    / "models"
    / "validators.py"
)

SMOKE_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "_smoke-test-plans"


def _get_smoke_plans() -> list[Path]:
    if not SMOKE_DIR.is_dir():
        return []
    return sorted(SMOKE_DIR.glob("*.md"))


smoke_plans = _get_smoke_plans()


@pytest.mark.skipif(
    not smoke_plans, reason="No smoke test fixtures (expected post-merge)"
)
@pytest.mark.parametrize("plan_path", smoke_plans, ids=[p.name for p in smoke_plans])
def test_real_plan_validates(plan_path: Path):
    """Each smoke test plan should pass Pydantic validation."""
    result = subprocess.run(
        [".venv/bin/python3", VALIDATORS_PATH, "plan", str(plan_path)],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, (
        f"Plan {plan_path.name} failed validation:\n{result.stderr}"
    )
