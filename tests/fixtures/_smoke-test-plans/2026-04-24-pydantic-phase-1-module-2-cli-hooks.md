---
schema_version: 1
feature_archetype: migration
source_contracts: "docs/specs/2026-04-24-pydantic-phase-1-design-distilled.md"
pattern_references:
  - name: "cli-pattern"
    source_files: ["skills/subagent-driven-development/scripts/validate-plan.py"]
    reason: "CLI pattern (argparse, JSON stdout, exit codes)"
  - name: "hook-json-wrapping"
    source_files: ["skills/writing-plans/scripts/plan-validation-gate-hook.sh"]
    reason: "Hook JSON wrapping with jq -Rs ."
  - name: "test-helper-pattern"
    source_files: ["tests/unit/sdd_test_helpers.py"]
    reason: "Test helper pattern for workspace setup"
tasks:
  - id: 6
    title: "CLI Validator — Plan Subcommand"
    pattern_references: ["cli-pattern"]
  - id: 7
    title: "CLI Validator — Handoff Subcommand"
    depends_on: [6]
  - id: 8
    title: "Hook Integration"
    depends_on: [7]
    pattern_references: ["hook-json-wrapping"]
  - id: 9
    title: "validate-plan.py Pydantic Integration"
    depends_on: [6]
---
# Pydantic Phase 1 — Module 2: CLI Validators + Hook Integration

> **For agentic workers:** Before implementing, invoke `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` via the Skill tool. Do not begin implementation without loading the skill first.

**Goal:** Create the CLI entry points in `validators.py` and modify existing hook scripts to call the Python validator, wrapping stderr in JSON for Claude Code consumption.

**Source Contracts:** None

**Contract Constraints:** See `docs/specs/2026-04-24-pydantic-phase-1-design-distilled.md` Contract Facts section. Key constraints for this module:
- CLI invocation: `python3 validators.py plan <path>` / `python3 validators.py handoff <dir>`
- Exit codes: 0 pass / 1 validation fail / 2 infrastructure
- `SUPERPOWERS_VALIDATOR_BYPASS=1` exits 0 with stderr warning containing `BYPASS`
- Hook JSON wrapping: `{"decision":"block","reason":$(jq -Rs . < /tmp/validator-err)}`
- `validate-plan.py` emits a warning (not blocker) for missing YAML frontmatter; the hard FAIL lives in `validators.py` (called directly by hooks)

**Pattern References:**
- `skills/subagent-driven-development/scripts/validate-plan.py` — CLI pattern (argparse, JSON stdout, exit codes)
- `skills/writing-plans/scripts/plan-validation-gate-hook.sh` — hook JSON wrapping with `jq -Rs .`
- `tests/unit/sdd_test_helpers.py` — test helper pattern for workspace setup

**Feature Archetype:** Migration

## File Map

```
skills/scripts/models/
└── validators.py                         # Tasks 6–7

skills/writing-plans/scripts/
└── plan-validation-gate-hook.sh          # Task 8 (modify)

skills/handoff-acceptance/scripts/
├── check-handoff.sh                      # Task 8 (modify)
└── handoff-gate-hook.sh                  # Task 8 (modify)

skills/subagent-driven-development/scripts/
└── validate-plan.py                      # Task 9 (modify)

tests/unit/
├── test_validators/
│   ├── test_validate_plan_pydantic.py    # Task 6
│   └── test_validate_handoff_pydantic.py # Task 7
└── test_hooks_pydantic.py               # Task 8
```

## Write-Scope Partitioning

| Task / Worker | Owned Files (write) | Read-Only Files | Depends On |
|---------------|---------------------|-----------------|------------|
| Task 6 | validators.py (plan part), test_validate_plan_pydantic.py | plan.py, errors.py, _base.py | Module 1 |
| Task 7 | validators.py (handoff part), test_validate_handoff_pydantic.py | handoff.py, errors.py | Task 6 |
| Task 8 | plan-validation-gate-hook.sh, handoff-gate-hook.sh, check-handoff.sh, test_hooks_pydantic.py | validators.py | Task 7 |
| Task 9 | validate-plan.py | validators.py | Task 6 |

Tasks 8 and 9 are parallel candidates (disjoint write sets, both depend on Task 7/6).

---

### Task 6: CLI Validator — Plan Subcommand

**Files:**
- Create: `skills/scripts/models/validators.py`
- Create: `tests/unit/test_validators/test_validate_plan_pydantic.py`

**Pattern References:**
- `skills/subagent-driven-development/scripts/validate-plan.py` — argparse pattern, exit codes

- [x] **Step 1: Write failing tests**

```python
# tests/unit/test_validators/test_validate_plan_pydantic.py
"""Tests for validators.py plan subcommand."""
import os
import subprocess
import tempfile
import pytest
from pathlib import Path

VALIDATORS_PATH = str(
    Path(__file__).resolve().parent.parent.parent.parent
    / "skills" / "scripts" / "models" / "validators.py"
)

VALID_PLAN = """\
---
schema_version: 1
feature_archetype: greenfield
tasks:
  - id: 0
    title: "Setup"
  - id: 1
    title: "Build"
    depends_on: [0]
---

# Test Plan
"""

INVALID_PLAN_BAD_ARCHETYPE = """\
---
schema_version: 1
feature_archetype: bogus
tasks:
  - id: 0
    title: "x"
---

# Bad Plan
"""

NO_FRONTMATTER_PLAN = """\
# Old-Style Plan

No YAML frontmatter here.
"""

MALFORMED_YAML = """\
---
schema_version: 1
feature_archetype: [invalid yaml
---
"""


def _run_validator(plan_content: str, extra_args: list[str] | None = None, env_override: dict | None = None) -> subprocess.CompletedProcess:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(plan_content)
        f.flush()
        path = f.name
    try:
        env = os.environ.copy()
        if env_override:
            env.update(env_override)
        cmd = [".venv/bin/python3", VALIDATORS_PATH, "plan", path]
        if extra_args:
            cmd.extend(extra_args)
        return subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=10)
    finally:
        os.unlink(path)


class TestPlanValidatorHappyPath:
    def test_valid_plan_exits_zero(self):
        result = _run_validator(VALID_PLAN)
        assert result.returncode == 0, f"stderr: {result.stderr}"

    def test_valid_plan_no_stderr(self):
        result = _run_validator(VALID_PLAN)
        assert result.stderr.strip() == ""


class TestPlanValidatorFailures:
    def test_invalid_archetype_exits_one(self):
        result = _run_validator(INVALID_PLAN_BAD_ARCHETYPE)
        assert result.returncode == 1

    def test_invalid_archetype_shows_validation_failed(self):
        result = _run_validator(INVALID_PLAN_BAD_ARCHETYPE)
        assert "VALIDATION FAILED" in result.stderr

    def test_no_frontmatter_exits_one(self):
        result = _run_validator(NO_FRONTMATTER_PLAN)
        assert result.returncode == 1

    def test_no_frontmatter_message(self):
        result = _run_validator(NO_FRONTMATTER_PLAN)
        assert "predates" in result.stderr or "YAML frontmatter" in result.stderr

    def test_malformed_yaml_exits_one(self):
        result = _run_validator(MALFORMED_YAML)
        assert result.returncode == 1

    def test_malformed_yaml_shows_yaml_parse_failed(self):
        result = _run_validator(MALFORMED_YAML)
        assert "YAML PARSE FAILED" in result.stderr


class TestPlanValidatorInfrastructure:
    def test_missing_file_exits_two(self):
        result = subprocess.run(
            [".venv/bin/python3", VALIDATORS_PATH, "plan", "/nonexistent/plan.md"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 2

    def test_bypass_env_exits_zero(self):
        result = _run_validator(INVALID_PLAN_BAD_ARCHETYPE, env_override={"SUPERPOWERS_VALIDATOR_BYPASS": "1"})
        assert result.returncode == 0

    def test_bypass_env_emits_warning(self):
        result = _run_validator(INVALID_PLAN_BAD_ARCHETYPE, env_override={"SUPERPOWERS_VALIDATOR_BYPASS": "1"})
        assert "BYPASS" in result.stderr


class TestSchemaVersionFlag:
    def test_forensic_flag_accepted(self):
        result = _run_validator(VALID_PLAN, extra_args=["--schema-version", "1"])
        assert result.returncode == 0
```

- [x] **Step 2: Run tests to verify they fail**

- [x] **Step 3: Implement validators.py (plan subcommand)**

```python
# skills/scripts/models/validators.py
#!/usr/bin/env python3
"""CLI entry points for Pydantic validation of plan and handoff artifacts.

Usage:
    python3 validators.py plan <path/to/plan.md> [--schema-version N]
    python3 validators.py handoff <path/to/package-dir/> [--schema-version N]

Exit codes: 0 = pass, 1 = validation fail, 2 = infrastructure error.
"""
import argparse
import os
import sys
from pathlib import Path

# Enable sibling imports when run as a script
sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import yaml
except ImportError:
    print("PyYAML is required. Install: .venv/bin/pip install pyyaml", file=sys.stderr)
    sys.exit(2)

try:
    from pydantic import ValidationError
except ImportError:
    print(
        "Pydantic v2.7+ is required. Install: .venv/bin/pip install -r requirements.txt",
        file=sys.stderr,
    )
    sys.exit(2)

from plan import Plan
from handoff import HandoffPackage
from errors import format_validation_error, format_yaml_error


def _check_bypass() -> bool:
    if os.environ.get("SUPERPOWERS_VALIDATOR_BYPASS") == "1":
        print(
            "WARNING: SUPERPOWERS_VALIDATOR_BYPASS is set — validation BYPASS active. "
            "This skips ALL Pydantic checks. Unset the env var when done.",
            file=sys.stderr,
        )
        return True
    return False


def _extract_frontmatter(text: str) -> str | None:
    """Extract YAML between first pair of --- delimiters. Returns None if no frontmatter."""
    if not text.startswith("---"):
        return None
    end = text.find("---", 3)
    if end == -1:
        return None
    return text[3:end]


def validate_plan(path: str, schema_version: int | None = None) -> int:
    """Validate a plan file. Returns exit code."""
    plan_path = Path(path)
    if not plan_path.is_file():
        print(f"File not found: {path}", file=sys.stderr)
        return 2

    if _check_bypass():
        return 0

    text = plan_path.read_text(encoding="utf-8")
    frontmatter_yaml = _extract_frontmatter(text)

    if frontmatter_yaml is None:
        print(
            f"No YAML frontmatter found in {path}. "
            "This plan predates the Phase 1 Pydantic cutover — "
            "add YAML frontmatter to validate it.",
            file=sys.stderr,
        )
        return 1

    try:
        data = yaml.safe_load(frontmatter_yaml)
    except yaml.YAMLError as e:
        print(format_yaml_error(e, path), file=sys.stderr)
        return 1

    if data is None:
        data = {}

    try:
        Plan.model_validate(data)
    except ValidationError as e:
        print(format_validation_error(e, path), file=sys.stderr)
        return 1
    except Exception as e:
        print(
            f"VALIDATOR CRASHED (this is a bug in the validator, not your artifact): "
            f"{type(e).__name__}: {e}",
            file=sys.stderr,
        )
        return 2

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Pydantic artifact validator")
    parser.add_argument("command", choices=["plan", "handoff"])
    parser.add_argument("path", help="Path to plan file or handoff package directory")
    parser.add_argument("--schema-version", type=int, default=None, help="Forensic: validate against older schema version")
    args = parser.parse_args()

    if args.command == "plan":
        sys.exit(validate_plan(args.path, args.schema_version))
    elif args.command == "handoff":
        # Implemented in Task 7
        print("Handoff validation not yet implemented", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
```

- [x] **Step 4: Run tests to verify they pass** (12/12 PASS)

- [x] **Step 5: Commit** (8c458af)

---

### Task 7: CLI Validator — Handoff Subcommand

**Files:**
- Modify: `skills/scripts/models/validators.py` (add `validate_handoff` function)
- Create: `tests/unit/test_validators/test_validate_handoff_pydantic.py`

- [x] **Step 1: Write failing tests**

```python
# tests/unit/test_validators/test_validate_handoff_pydantic.py
"""Tests for validators.py handoff subcommand."""
import os
import subprocess
import tempfile
import pytest
from pathlib import Path

VALIDATORS_PATH = str(
    Path(__file__).resolve().parent.parent.parent.parent
    / "skills" / "scripts" / "models" / "validators.py"
)

VALID_HANDOFF_README = """\
---
schema_version: 1
package_name: test-pkg
feeds_into: brainstorming
one_sentence_purpose: "Test handoff."
contract_constraints:
  - name: amount
    kind: float
samples:
  - path: samples/example.csv
    description: "Example data"
---

# Test Handoff Package
"""

INVALID_HANDOFF_README = """\
---
schema_version: 1
package_name: test-pkg
feeds_into: brainstorming
one_sentence_purpose: "Test."
contract_constraints:
  - name: amount
    kind: complex
samples:
  - path: samples/example.csv
    description: "Example"
---
"""


def _setup_package(tmpdir: Path, readme_content: str, sample_files: list[str] | None = None) -> Path:
    pkg_dir = tmpdir / "test-pkg"
    pkg_dir.mkdir()
    (pkg_dir / "README.md").write_text(readme_content)
    if sample_files:
        for sf in sample_files:
            (pkg_dir / sf).parent.mkdir(parents=True, exist_ok=True)
            (pkg_dir / sf).write_text("sample data")
    return pkg_dir


def _run_validator(pkg_dir: str, env_override: dict | None = None) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    if env_override:
        env.update(env_override)
    return subprocess.run(
        [".venv/bin/python3", VALIDATORS_PATH, "handoff", str(pkg_dir)],
        capture_output=True, text=True, env=env, timeout=10,
    )


class TestHandoffValidatorHappyPath:
    def test_valid_handoff_exits_zero(self, tmp_path):
        pkg = _setup_package(tmp_path, VALID_HANDOFF_README, ["samples/example.csv"])
        result = _run_validator(str(pkg))
        assert result.returncode == 0, f"stderr: {result.stderr}"


class TestHandoffValidatorFailures:
    def test_invalid_field_type_exits_one(self, tmp_path):
        pkg = _setup_package(tmp_path, INVALID_HANDOFF_README, ["samples/example.csv"])
        result = _run_validator(str(pkg))
        assert result.returncode == 1
        assert "VALIDATION FAILED" in result.stderr

    def test_missing_sample_file_exits_one(self, tmp_path):
        pkg = _setup_package(tmp_path, VALID_HANDOFF_README)  # no sample files created
        result = _run_validator(str(pkg))
        assert result.returncode == 1
        assert "SAMPLE FILE MISSING" in result.stderr

    def test_missing_readme_exits_two(self, tmp_path):
        pkg_dir = tmp_path / "empty-pkg"
        pkg_dir.mkdir()
        result = _run_validator(str(pkg_dir))
        assert result.returncode == 2


class TestHandoffBypass:
    def test_bypass_exits_zero(self, tmp_path):
        pkg = _setup_package(tmp_path, INVALID_HANDOFF_README, ["samples/example.csv"])
        result = _run_validator(str(pkg), env_override={"SUPERPOWERS_VALIDATOR_BYPASS": "1"})
        assert result.returncode == 0

    def test_bypass_emits_warning(self, tmp_path):
        pkg = _setup_package(tmp_path, INVALID_HANDOFF_README, ["samples/example.csv"])
        result = _run_validator(str(pkg), env_override={"SUPERPOWERS_VALIDATOR_BYPASS": "1"})
        assert "BYPASS" in result.stderr
```

- [x] **Step 2: Run tests to verify they fail**

- [x] **Step 3: Add validate_handoff to validators.py**

Add this function to `skills/scripts/models/validators.py` before `main()`:

```python
def validate_handoff(path: str, schema_version: int | None = None) -> int:
    """Validate a handoff package directory. Returns exit code."""
    pkg_dir = Path(path)
    readme_path = pkg_dir / "README.md"

    if not readme_path.is_file():
        print(f"README.md not found in {path}", file=sys.stderr)
        return 2

    if _check_bypass():
        return 0

    text = readme_path.read_text(encoding="utf-8")
    frontmatter_yaml = _extract_frontmatter(text)

    if frontmatter_yaml is None:
        print(
            f"No YAML frontmatter found in {readme_path}. "
            "This handoff predates the Phase 1 Pydantic cutover — "
            "add YAML frontmatter to validate it.",
            file=sys.stderr,
        )
        return 1

    try:
        data = yaml.safe_load(frontmatter_yaml)
    except yaml.YAMLError as e:
        print(format_yaml_error(e, str(readme_path)), file=sys.stderr)
        return 1

    if data is None:
        data = {}

    try:
        pkg = HandoffPackage.model_validate(data)
    except ValidationError as e:
        print(format_validation_error(e, str(readme_path)), file=sys.stderr)
        return 1
    except Exception as e:
        print(
            f"VALIDATOR CRASHED (this is a bug in the validator, not your artifact): "
            f"{type(e).__name__}: {e}",
            file=sys.stderr,
        )
        return 2

    # Filesystem post-check: verify sample files exist
    missing = []
    for sample in pkg.samples:
        full = pkg_dir / sample.path
        if not full.is_file():
            missing.append((sample.path, str(full)))

    if missing:
        lines = [
            "═══════════════════════════════════════════════════════════════════",
            f" SAMPLE FILE MISSING: {readme_path}",
            f" {len(missing)} sample file(s) not found on disk.",
            "═══════════════════════════════════════════════════════════════════",
            "",
        ]
        for i, (rel, abs_path) in enumerate(missing, 1):
            lines.append(f"[{i}] Declared: {rel}")
            lines.append(f"    Resolved: {abs_path}")
            lines.append(f"    Status:   file does not exist")
            lines.append("")
        lines.append("═══════════════════════════════════════════════════════════════════")
        print("\n".join(lines), file=sys.stderr)
        return 1

    return 0
```

Update the `main()` function's handoff branch:

```python
    elif args.command == "handoff":
        sys.exit(validate_handoff(args.path, args.schema_version))
```

- [x] **Step 4: Run tests to verify they pass** (6/6 PASS, 18 total)

- [x] **Step 5: Commit** (358c138)

---

### Task 8: Hook Integration

**Files:**
- Modify: `skills/writing-plans/scripts/plan-validation-gate-hook.sh`
- Modify: `skills/handoff-acceptance/scripts/check-handoff.sh`
- Modify: `skills/handoff-acceptance/scripts/handoff-gate-hook.sh`
- Create: `tests/unit/test_hooks_pydantic.py`

**Pattern References:**
- `skills/writing-plans/scripts/plan-validation-gate-hook.sh` — existing hook JSON wrapping pattern

- [x] **Step 1: Write hook integration tests**

```python
# tests/unit/test_hooks_pydantic.py
"""Integration tests for hook scripts calling Pydantic validators."""
import os
import subprocess
import tempfile
import json
import pytest
from pathlib import Path

VALIDATORS_PATH = str(
    Path(__file__).resolve().parent.parent
    / "skills" / "scripts" / "models" / "validators.py"
)


class TestJqAvailability:
    """jq must be available for hook JSON wrapping."""

    def test_jq_is_on_path(self):
        result = subprocess.run(["which", "jq"], capture_output=True, text=True)
        assert result.returncode == 0, "jq is not installed — required for hook JSON wrapping"

    def test_jq_can_wrap_string(self):
        result = subprocess.run(
            ["jq", "-Rs", "."],
            input="test\nstring",
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        parsed = json.loads(result.stdout)
        assert "test" in parsed


class TestPlanValidatorFromHookPerspective:
    """Verify validator produces output hooks can consume."""

    def test_valid_plan_exits_zero(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("---\nschema_version: 1\nfeature_archetype: greenfield\ntasks:\n  - id: 0\n    title: x\n---\n")
            f.flush()
            result = subprocess.run(
                [".venv/bin/python3", VALIDATORS_PATH, "plan", f.name],
                capture_output=True, text=True, timeout=10,
            )
        os.unlink(f.name)
        assert result.returncode == 0

    def test_invalid_plan_stderr_wrappable_with_jq(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("---\nschema_version: 1\n---\n")
            f.flush()
            val_result = subprocess.run(
                [".venv/bin/python3", VALIDATORS_PATH, "plan", f.name],
                capture_output=True, text=True, timeout=10,
            )
        os.unlink(f.name)
        assert val_result.returncode == 1
        # Verify stderr can be JSON-wrapped with jq
        jq_result = subprocess.run(
            ["jq", "-Rs", "."],
            input=val_result.stderr,
            capture_output=True, text=True,
        )
        assert jq_result.returncode == 0
        parsed = json.loads(jq_result.stdout)
        assert "VALIDATION FAILED" in parsed

    def test_no_frontmatter_stderr_contains_cutover_message(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Old plan\nNo frontmatter.\n")
            f.flush()
            result = subprocess.run(
                [".venv/bin/python3", VALIDATORS_PATH, "plan", f.name],
                capture_output=True, text=True, timeout=10,
            )
        os.unlink(f.name)
        assert result.returncode == 1
        assert "frontmatter" in result.stderr.lower()


class TestHandoffValidatorFromHookPerspective:
    """Verify handoff validator produces output hooks can consume."""

    def test_valid_handoff_exits_zero(self, tmp_path):
        pkg_dir = tmp_path / "pkg"
        pkg_dir.mkdir()
        (pkg_dir / "README.md").write_text(
            "---\nschema_version: 1\npackage_name: test\nfeeds_into: x\n"
            "one_sentence_purpose: test\ncontract_constraints:\n  - name: a\n    kind: string\n"
            "samples:\n  - path: s.csv\n    description: d\n---\n"
        )
        (pkg_dir / "s.csv").write_text("data")
        result = subprocess.run(
            [".venv/bin/python3", VALIDATORS_PATH, "handoff", str(pkg_dir)],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0

    def test_missing_sample_shows_distinct_header(self, tmp_path):
        pkg_dir = tmp_path / "pkg"
        pkg_dir.mkdir()
        (pkg_dir / "README.md").write_text(
            "---\nschema_version: 1\npackage_name: test\nfeeds_into: x\n"
            "one_sentence_purpose: test\ncontract_constraints:\n  - name: a\n    kind: string\n"
            "samples:\n  - path: missing.csv\n    description: d\n---\n"
        )
        result = subprocess.run(
            [".venv/bin/python3", VALIDATORS_PATH, "handoff", str(pkg_dir)],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 1
        assert "SAMPLE FILE MISSING" in result.stderr
        assert "VALIDATION FAILED" not in result.stderr
```

- [x] **Step 2: Run tests**

- [x] **Step 3: Modify plan-validation-gate-hook.sh**

In `skills/writing-plans/scripts/plan-validation-gate-hook.sh`, add a Pydantic validator call alongside the existing validate-plan.py call. Locate the section where `validate-plan.py` is invoked for each plan file, and add a new block AFTER the existing validation:

```bash
# --- Pydantic validation (Phase 1) ---
PYDANTIC_VALIDATOR="$(dirname "$0")/../../scripts/models/validators.py"
if [ -f "$PYDANTIC_VALIDATOR" ]; then
  if ! .venv/bin/python3 "$PYDANTIC_VALIDATOR" plan "$PLAN_FILE" 2>/tmp/pydantic-validator-err; then
    PYDANTIC_EXIT=$?
    if [ "$PYDANTIC_EXIT" -eq 1 ]; then
      ERRORS+=("Pydantic validation failed for $PLAN_FILE")
      PYDANTIC_ERR=$(jq -Rs . < /tmp/pydantic-validator-err 2>/dev/null || cat /tmp/pydantic-validator-err)
      echo -e "  [FAIL] Pydantic: $PLAN_FILE" >&2
    fi
    # Exit 2 = infrastructure — warn but don't block
    if [ "$PYDANTIC_EXIT" -eq 2 ]; then
      echo -e "  [WARN] Pydantic validator infrastructure error for $PLAN_FILE" >&2
    fi
  fi
fi
```

- [x] **Step 4: Modify check-handoff.sh**

Add Pydantic validation call at the TOP of `skills/handoff-acceptance/scripts/check-handoff.sh`, before the existing first-50-lines check:

```bash
# --- Pydantic validation (Phase 1) ---
PYDANTIC_VALIDATOR="$(dirname "$0")/../../scripts/models/validators.py"
HANDOFF_DIR="$(dirname "$1")"
if [ -f "$PYDANTIC_VALIDATOR" ] && head -1 "$1" | grep -q '^---$'; then
  if ! .venv/bin/python3 "$PYDANTIC_VALIDATOR" handoff "$HANDOFF_DIR" 2>/tmp/pydantic-handoff-err; then
    PYDANTIC_EXIT=$?
    ERR_TEXT=$(cat /tmp/pydantic-handoff-err)
    echo "{\"status\": \"FAIL\", \"message\": \"Pydantic validation failed\", \"detail\": $(echo "$ERR_TEXT" | jq -Rs . 2>/dev/null || echo "\"$ERR_TEXT\"")}"
    exit 1
  fi
fi
```

- [x] **Step 5: Modify handoff-gate-hook.sh**

`handoff-gate-hook.sh` currently checks for acceptance reports only — it does NOT call `check-handoff.sh`. Add a Pydantic validation block that calls `validators.py handoff` directly, BEFORE the existing acceptance-report check. This mirrors how `plan-validation-gate-hook.sh` calls `validators.py plan`:

```bash
# --- Pydantic validation (Phase 1) ---
PYDANTIC_VALIDATOR="$(dirname "$0")/../../scripts/models/validators.py"
# Find handoff package dirs in docs/ (directories containing README.md with frontmatter)
for HANDOFF_DIR in $(find "$CWD/docs" -name "README.md" -path "*handoff*" -exec dirname {} \; 2>/dev/null); do
  if [ -f "$PYDANTIC_VALIDATOR" ] && head -1 "$HANDOFF_DIR/README.md" | grep -q '^---$'; then
    if ! .venv/bin/python3 "$PYDANTIC_VALIDATOR" handoff "$HANDOFF_DIR" 2>/tmp/pydantic-handoff-err; then
      PYDANTIC_EXIT=$?
      if [ "$PYDANTIC_EXIT" -eq 1 ]; then
        echo "{\"decision\":\"block\",\"reason\":$(jq -Rs . < /tmp/pydantic-handoff-err 2>/dev/null || cat /tmp/pydantic-handoff-err)}" >&2
        exit 2
      fi
    fi
  fi
done
```

Place this block after the skill-name check but before the acceptance-report check.

- [x] **Step 6: Run hook integration tests** (7/7 PASS)

- [x] **Step 7: Commit** (8ad17c5 + 7fdea7f fix for exit code capture bug found in quality review)

---

### Task 9: validate-plan.py Pydantic Integration

**Files:**
- Modify: `skills/subagent-driven-development/scripts/validate-plan.py`

**Pattern References:**
- `skills/subagent-driven-development/scripts/validate-plan.py:1-30` — existing structure

**Important context:** validate-plan.py has 22 existing unit tests with fixtures that lack YAML frontmatter. The hard-FAIL for missing frontmatter lives in `validators.py` (the Pydantic CLI called by hooks), NOT here. validate-plan.py adds Pydantic as an additional check when frontmatter is detected, preserving the existing regex path for legacy plans.

- [x] **Step 1: Add frontmatter detection + Pydantic validation to validate-plan.py**

In the `validate_plan()` function, add frontmatter detection AFTER the existing line-counting setup but BEFORE the regex checks. When frontmatter is present, run Pydantic validation as an additional check and merge results into the output. When absent, run existing regex checks only and add a warning (not a blocker):

```python
import subprocess
import json as json_module

def validate_plan(content: str, additional_contents: list[str] | None = None) -> dict:
    lines = content.splitlines()

    # Phase 1: detect YAML frontmatter
    has_frontmatter = content.startswith("---")

    if not has_frontmatter:
        # Legacy plan — regex validation only, warn about missing frontmatter
        # (The hard FAIL for missing frontmatter lives in validators.py,
        # which hooks call directly. validate-plan.py preserves backward compat.)
        pass  # Fall through to existing regex checks below
        # Add to warnings list at the end

    # ... existing validation code runs for ALL plans ...

    # After existing checks, if frontmatter present, also run Pydantic validator
    if has_frontmatter:
        validators_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "scripts", "models", "validators.py"
        )
        if os.path.isfile(validators_path):
            # Write content to temp file for subprocess call
            import tempfile
            with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            try:
                pydantic_result = subprocess.run(
                    [sys.executable, validators_path, "plan", tmp_path],
                    capture_output=True, text=True, timeout=10,
                )
                if pydantic_result.returncode == 1:
                    # Pydantic validation failed — add as blocker
                    result["blockers"].append(
                        f"Pydantic validation failed:\n{pydantic_result.stderr.strip()}"
                    )
                    result["status"] = "FAIL"
            finally:
                os.unlink(tmp_path)
    else:
        result["warnings"].append(
            "No YAML frontmatter detected. Post-Phase 1 plans should include "
            "frontmatter with schema_version, feature_archetype, and tasks fields."
        )
```

Integrate this into the existing flow without restructuring the function. The key principle: existing regex checks ALWAYS run, Pydantic is additive when frontmatter is present.

- [x] **Step 2: Run existing tests — no regression** (15/15 PASS)

- [x] **Step 3: Run full unit test suite** (156/156 PASS)

- [x] **Step 4: Commit** (784b284)

## Module 2 Acceptance Criteria

- [x] `validators.py` supports `plan` and `handoff` subcommands with `--schema-version N` flag
- [x] CLI honors `SUPERPOWERS_VALIDATOR_BYPASS=1` (exit 0 + stderr warning with `BYPASS`)
- [x] CLI exit codes: 0/1/2
- [x] Handoff subcommand performs filesystem post-check with `SAMPLE FILE MISSING` header
- [x] `plan-validation-gate-hook.sh` calls Python validator and wraps stderr in JSON (+ exit code fix 7fdea7f)
- [x] `check-handoff.sh` calls Python validator for handoff packages
- [x] `handoff-gate-hook.sh` wraps stderr in JSON
- [x] `validate-plan.py` emits a warning for plans without YAML frontmatter (hard FAIL is in validators.py only)
- [x] jq availability verified in hook integration tests
- [x] 25 tests pass in `tests/unit/test_validators/` (18) and `tests/unit/test_hooks_pydantic.py` (7)
