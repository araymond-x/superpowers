"""
Tests for brainstorming/scripts/check-distillation.sh.

Two behavior groups:
- One-arg mode (pre-2026-07-07 contract, pinned): exploration-artifact grep only.
- Two-arg mode (scope-fence preservation, 2026-07-07): when the full spec
  declares an out-of-scope/non-goals HEADING, the distilled spec must carry a
  counterpart heading or the check FAILs. Fence matching is heading-level —
  body-prose mentions of "out of scope" do not count.

Incident: telemetry-exp stable-fact-store distillation dropped the spec's
§1.2 out-of-scope fence; the checker had no positive check to catch it.
"""

import json
import os
import subprocess

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCRIPT = os.path.join(
    ROOT, "skills", "brainstorming", "scripts", "check-distillation.sh"
)

CLEAN_DISTILLED = """# Feature — Distilled Implementation Spec

> **For**: Plan writer and implementation agents ONLY. For full rationale, see source.

## Contract Facts

- Key: `(id: str, seq: int)`.

## Component Specifications

### Writer
Writes segments, seals via manifest.
"""

FENCED_DISTILLED = """# Feature — Distilled Implementation Spec

## Out of scope — do not build

- Dashboard read model → Phase 3.
- Eviction daemon → Phase 4.

## Contract Facts

- Key: `(id: str, seq: int)`.
"""

FENCED_FULL_SPEC = """# Feature — Design Spec

## 1. Scope

### 1.1 In scope

1. A writer.

### 1.2 Out of scope (deferred — do not let convenience pull these in)

- Dashboard read model → Phase 3.
- Eviction daemon → Phase 4.

## 2. Components

The writer writes.
"""

UNFENCED_FULL_SPEC = """# Feature — Design Spec

## 1. Components

The writer writes. Anything else is out of scope for now, informally speaking.
"""

ARTIFACT_DISTILLED = """# Feature — Distilled Implementation Spec

We considered several options. Rationale: speed.
"""


def run_check(*args):
    """Run the checker; return (exit_code, parsed_json_dict, stderr).

    The dict is empty when the script printed nothing to stdout (usage
    errors go to stderr) — key assertions then fail loudly.
    """
    result = subprocess.run(["bash", SCRIPT, *args], capture_output=True, text=True)
    parsed = {}
    if result.stdout.strip():
        parsed = json.loads(result.stdout)
    return result.returncode, parsed, result.stderr


def write(tmp_path, name, content):
    path = tmp_path / name
    path.write_text(content)
    return str(path)


class TestOneArgMode:
    """Pins the pre-existing single-argument contract."""

    def test_clean_distilled_passes(self, tmp_path):
        distilled = write(tmp_path, "distilled.md", CLEAN_DISTILLED)
        code, out, _ = run_check(distilled)
        assert code == 0
        assert out["status"] == "PASS"
        assert out["fence"] == "NOT_CHECKED"

    def test_artifacts_fail(self, tmp_path):
        distilled = write(tmp_path, "distilled.md", ARTIFACT_DISTILLED)
        code, out, _ = run_check(distilled)
        assert code == 1
        assert out["status"] == "FAIL"
        assert out["artifact_count"] == 1

    def test_blockquote_boilerplate_excluded(self, tmp_path):
        # The template's "> For full rationale, see source" line contains
        # "rationale" but must not fire the artifact grep.
        distilled = write(tmp_path, "distilled.md", CLEAN_DISTILLED)
        code, _, _ = run_check(distilled)
        assert code == 0

    def test_missing_fence_not_checked_one_arg(self, tmp_path):
        # Backwards compatibility: without the full spec, a fence-less
        # distilled spec still passes (writing-plans direct entry may only
        # have the distilled spec).
        distilled = write(tmp_path, "distilled.md", CLEAN_DISTILLED)
        code, out, _ = run_check(distilled)
        assert code == 0
        assert out["fence"] == "NOT_CHECKED"


class TestTwoArgFenceCheck:
    def test_fence_dropped_fails(self, tmp_path):
        distilled = write(tmp_path, "distilled.md", CLEAN_DISTILLED)
        full = write(tmp_path, "spec.md", FENCED_FULL_SPEC)
        code, out, _ = run_check(distilled, full)
        assert code == 1
        assert out["status"] == "FAIL"
        assert out["fence"] == "MISSING"
        assert "fence_detail" in out

    def test_fence_present_passes(self, tmp_path):
        distilled = write(tmp_path, "distilled.md", FENCED_DISTILLED)
        full = write(tmp_path, "spec.md", FENCED_FULL_SPEC)
        code, out, _ = run_check(distilled, full)
        assert code == 0
        assert out["status"] == "PASS"
        assert out["fence"] == "PRESENT"

    def test_source_without_fence_not_required(self, tmp_path):
        # "out of scope" in body prose is not a heading-level fence.
        distilled = write(tmp_path, "distilled.md", CLEAN_DISTILLED)
        full = write(tmp_path, "spec.md", UNFENCED_FULL_SPEC)
        code, out, _ = run_check(distilled, full)
        assert code == 0
        assert out["fence"] == "NOT_REQUIRED"

    def test_artifacts_and_fence_both_reported(self, tmp_path):
        distilled = write(tmp_path, "distilled.md", ARTIFACT_DISTILLED)
        full = write(tmp_path, "spec.md", FENCED_FULL_SPEC)
        code, out, _ = run_check(distilled, full)
        assert code == 1
        assert out["artifact_count"] == 1
        assert out["fence"] == "MISSING"

    def test_non_goals_heading_counts_as_fence(self, tmp_path):
        distilled = write(tmp_path, "distilled.md", CLEAN_DISTILLED)
        full = write(
            tmp_path,
            "spec.md",
            "# Spec\n\n## Non-goals\n\n- Replication → Phase 4.\n",
        )
        code, out, _ = run_check(distilled, full)
        assert code == 1
        assert out["fence"] == "MISSING"


class TestUsageErrors:
    def test_no_args(self):
        code, _, stderr = run_check()
        assert code == 2
        assert "Usage" in stderr

    def test_missing_distilled_path(self, tmp_path):
        code, _, _ = run_check(str(tmp_path / "nope.md"))
        assert code == 2

    def test_missing_full_spec_path(self, tmp_path):
        distilled = write(tmp_path, "distilled.md", CLEAN_DISTILLED)
        code, _, stderr = run_check(distilled, str(tmp_path / "nope.md"))
        assert code == 2
        assert "full-spec path not found" in stderr
