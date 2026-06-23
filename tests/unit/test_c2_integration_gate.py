"""C2: Integration-test gate — model, validate-plan WARNING, Check 10.
Run: .venv/bin/python3 -m pytest tests/unit/test_c2_integration_gate.py -v
"""

import json
import os
import subprocess
import sys

import pytest

from plan import IntegrationTest, Plan
from sdd_test_helpers import ROOT, _load_script

_vp = _load_script("validate_plan_c2", "validate-plan.py")
_vp_ckpt = _load_script("controller_checkpoint_n25", "controller-checkpoint.py")

# SELF-HOSTING GUARD: _H avoids plan-validator false match on task headers in fixtures.
_H = "##" + "# Task"

RISK_PLAN = (
    "---\nschema_version: 1\nfeature_archetype: extension\n"
    "tasks:\n  - id: 1\n    title: Add auth middleware\n---\n"
    f"# Plan\n\n**Source Contracts:** None\n\n**Feature Archetype:** Extension\n\n"
    f"{_H} 1: Add auth middleware\n- [ ] Do it\n"
)

SAFE_PLAN_WITH_INTEGRATION = (
    "---\nschema_version: 1\nfeature_archetype: extension\n"
    "integration_test:\n  path: tests/e2e.sh\n"
    "tasks:\n  - id: 1\n    title: Add auth middleware\n---\n"
    f"# Plan\n\n**Source Contracts:** None\n\n**Feature Archetype:** Extension\n\n"
    f"{_H} 1: Add auth middleware\n- [ ] Do it\n"
)


class TestIntegrationTestModel:
    def test_valid_relative_path(self):
        it = IntegrationTest(path="tests/integration/sdd-e2e-test.sh")
        assert it.path == "tests/integration/sdd-e2e-test.sh"

    def test_absolute_path_rejected(self):
        with pytest.raises(ValueError, match="absolute"):
            IntegrationTest(path="/absolute/path/test.sh")

    def test_dotdot_path_rejected(self):
        with pytest.raises(ValueError, match="\\.\\."):
            IntegrationTest(path="tests/../../../etc/passwd")

    def test_empty_path_rejected(self):
        with pytest.raises(ValueError, match="empty"):
            IntegrationTest(path="")

    def test_bare_dotdot_rejected(self):
        with pytest.raises(ValueError, match="\\.\\."):
            IntegrationTest(path="..")

    def test_plan_integration_test_optional(self):
        p = Plan(
            schema_version=1,
            feature_archetype="extension",
            tasks=[{"id": 1, "title": "T"}],
        )
        assert p.integration_test is None

    def test_plan_integration_test_present(self):
        p = Plan(
            schema_version=1,
            feature_archetype="extension",
            tasks=[{"id": 1, "title": "T"}],
            integration_test={"path": "tests/e2e.sh"},
        )
        assert p.integration_test.path == "tests/e2e.sh"


class TestC2RiskSurfaceWarning:
    def test_risk_pattern_no_integration_test_warns(self):
        result = _vp.validate_plan(RISK_PLAN)
        assert any(
            "integration" in w.lower() or "risk" in w.lower()
            for w in result["warnings"]
        )

    def test_risk_pattern_with_integration_test_no_warn(self):
        result = _vp.validate_plan(SAFE_PLAN_WITH_INTEGRATION)
        risk_warns = [
            w
            for w in result["warnings"]
            if "integration" in w.lower() and "risk" in w.lower()
        ]
        assert len(risk_warns) == 0

    def test_no_risk_pattern_no_warn(self):
        no_risk = (
            "---\nschema_version: 1\nfeature_archetype: extension\n"
            "tasks:\n  - id: 1\n    title: Add utility\n---\n"
            f"# Plan\n\n**Source Contracts:** None\n\n**Feature Archetype:** Extension\n\n"
            f"{_H} 1: Add utility\n- [ ] Do it\n"
        )
        result = _vp.validate_plan(no_risk)
        risk_warns = [
            w
            for w in result["warnings"]
            if "integration" in w.lower() and "risk" in w.lower()
        ]
        assert len(risk_warns) == 0

    def test_frontmatterless_plan_with_risk_warns(self):
        """No YAML frontmatter at all → frontmatter is None → still warns."""
        plan = (
            f"# Plan\n\n**Source Contracts:** None\n\n"
            f"{_H} 1: Add auth middleware\n- [ ] Do it\n"
        )
        result = _vp.validate_plan(plan)
        assert any(
            w.startswith("integration_test_risk_surface") for w in result["warnings"]
        )
        section = result["sections"].get("integration_test_risk", {})
        assert section.get("status") == "WARNING"

    def test_explicit_null_integration_test_still_warns(self):
        """integration_test: null in frontmatter is not a declaration → still warns."""
        plan = (
            "---\nschema_version: 1\nfeature_archetype: extension\n"
            "integration_test: null\n"
            "tasks:\n  - id: 1\n    title: Add auth middleware\n---\n"
            f"# Plan\n\n**Source Contracts:** None\n\n**Feature Archetype:** Extension\n\n"
            f"{_H} 1: Add auth middleware\n- [ ] Do it\n"
        )
        result = _vp.validate_plan(plan)
        assert any(
            w.startswith("integration_test_risk_surface") for w in result["warnings"]
        )
        section = result["sections"].get("integration_test_risk", {})
        assert section.get("status") == "WARNING"


def _warns_risk(content):
    """True if validate-plan emits the integration_test_risk_surface WARNING."""
    return any(
        "integration_test_risk_surface" in w
        for w in _vp.check_integration_test_risk(content, {})
    )


class TestRiskSurfaceStemming:
    def test_inflected_forms_match(self):
        # Words the spec's stem patterns (D8) must match. NOTE: "security" matches
        # securit\w* but "securing" does NOT (stem is securit, not secur) — keep
        # test words aligned to the spec's chosen stems.
        for kw in ("migrations", "caches", "routers", "authentication", "security"):
            body = f"---\nschema_version: 1\n---\n# Plan\nThis touches {kw} logic.\n"
            assert _warns_risk(body), f"{kw} should trigger the risk WARNING"

    def test_fenced_only_keyword_does_not_warn(self):
        body = "---\nschema_version: 1\n---\n# Plan\n```\nauth migration router\n```\nNo risk prose.\n"
        assert not _warns_risk(body), "fence-only keywords must not warn"

    def test_declared_integration_test_suppresses(self):
        body = "# Plan\nTouches authentication.\n"
        assert _vp.check_integration_test_risk(body, {"integration_test": {"path": "x"}}) == []


# ---------------------------------------------------------------------------
# Check 10: pre-completion integration-test gate (controller-checkpoint.py)
# ---------------------------------------------------------------------------

CHECKPOINT_SCRIPT = os.path.join(
    ROOT, "skills", "subagent-driven-development", "scripts", "controller-checkpoint.py"
)

IT_PATH = "tests/integration/e2e.sh"

# Null host git config so fixtures are independent of the machine's
# ~/.gitconfig and system config (e.g. init.defaultBranch, commit.gpgsign).
_GIT_ENV = {
    **os.environ,
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_CONFIG_SYSTEM": "/dev/null",
}


def _c2_plan(integration_path=None):
    """Minimal valid plan; optionally declares a top-level integration_test."""
    it = (
        "integration_test:\n  path: {}\n".format(integration_path)
        if integration_path
        else ""
    )
    return (
        "---\nschema_version: 1\nfeature_archetype: extension\n"
        + it
        + "tasks:\n  - id: 1\n    title: T\n---\n"
        + f"# Plan\n\n**Source Contracts:** None\n\n{_H} 1: T\n- [x] done\n"
    )


class TestC2Check10:
    """Pre-completion Check 10: a declared integration_test path must exist on
    disk AND be part of the feature changeset (untracked file or tracked diff
    vs merge-base with the base branch).

    Other pre-completion checks (honesty, trace audit, reports) legitimately
    FAIL in these minimal fixtures — assertions target ONLY the
    integration_test_present check entry and the integration_test_present
    blocker.
    """

    def _git(self, repo, *args, date=None):
        env = _GIT_ENV
        if date is not None:
            env = {**_GIT_ENV, "GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date}
        return subprocess.run(
            ["git", "-C", str(repo)] + list(args),
            capture_output=True,
            text=True,
            check=True,
            env=env,
        )

    def _setup_repo(self, tmp_path, plan_content, module_content=None):
        """Write plan/deviations/reports into tmp_path; git init -b main; commit all."""
        (tmp_path / "plan.md").write_text(plan_content)
        if module_content is not None:
            (tmp_path / "mod-b.md").write_text(module_content)
        (tmp_path / "DEVIATIONS.md").write_text("")
        (tmp_path / "reports").mkdir()
        subprocess.run(
            ["git", "init", "-q", "-b", "main", str(tmp_path)],
            capture_output=True,
            text=True,
            check=True,
            env=_GIT_ENV,
        )
        self._git(tmp_path, "config", "user.email", "test@example.com")
        self._git(tmp_path, "config", "user.name", "Test")
        self._git(tmp_path, "config", "commit.gpgsign", "false")
        self._git(tmp_path, "add", ".")
        self._git(tmp_path, "commit", "-q", "-m", "base")

    def _run_checkpoint(self, tmp_path, additional_plan_files=None):
        cmd = [
            sys.executable,
            CHECKPOINT_SCRIPT,
            "--phase",
            "pre-completion",
            "--plan-file",
            str(tmp_path / "plan.md"),
            "--deviations-file",
            str(tmp_path / "DEVIATIONS.md"),
            "--reports-dir",
            str(tmp_path / "reports"),
        ]
        if additional_plan_files:
            cmd += ["--additional-plan-files"] + additional_plan_files
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        assert result.stdout.strip(), f"checkpoint produced no output: {result.stderr}"
        return json.loads(result.stdout)

    def test_no_declaration_passes(self, tmp_path):
        """No integration_test in any frontmatter → PASS with skipped detail."""
        self._setup_repo(tmp_path, _c2_plan())
        out = self._run_checkpoint(tmp_path)
        check = out.get("checks", {}).get("integration_test_present", {})
        assert check.get("status") == "PASS", check
        assert "skip" in check.get("detail", "").lower(), check
        assert "integration_test_present" not in out.get("blockers", [])

    def test_path_missing_fails(self, tmp_path):
        """Declared but no file on disk → FAIL + blocker."""
        self._setup_repo(tmp_path, _c2_plan(IT_PATH))
        out = self._run_checkpoint(tmp_path)
        check = out.get("checks", {}).get("integration_test_present", {})
        assert check.get("status") == "FAIL", check
        assert "missing" in check.get("detail", "").lower(), check
        assert "integration_test_present" in out.get("blockers", [])

    def test_untracked_new_passes(self, tmp_path):
        """Declared file created AFTER the base commit (untracked) → PASS."""
        self._setup_repo(tmp_path, _c2_plan(IT_PATH))
        it_file = tmp_path / IT_PATH
        it_file.parent.mkdir(parents=True)
        it_file.write_text("#!/bin/bash\necho e2e\n")
        out = self._run_checkpoint(tmp_path)
        check = out.get("checks", {}).get("integration_test_present", {})
        assert check.get("status") == "PASS", check
        assert "integration_test_present" not in out.get("blockers", [])

    def test_exists_but_unchanged_fails(self, tmp_path):
        """Declared file pre-committed and untouched (no feature change) → FAIL."""
        it_file = tmp_path / IT_PATH
        it_file.parent.mkdir(parents=True)
        it_file.write_text("#!/bin/bash\necho e2e\n")
        self._setup_repo(tmp_path, _c2_plan(IT_PATH))
        out = self._run_checkpoint(tmp_path)
        check = out.get("checks", {}).get("integration_test_present", {})
        assert check.get("status") == "FAIL", check
        assert "changeset" in check.get("detail", "").lower(), check
        assert "integration_test_present" in out.get("blockers", [])

    def test_modified_tracked_passes(self, tmp_path):
        """Declared file tracked in base commit then MODIFIED in working tree → PASS."""
        it_file = tmp_path / IT_PATH
        it_file.parent.mkdir(parents=True)
        it_file.write_text("#!/bin/bash\necho e2e\n")
        self._setup_repo(tmp_path, _c2_plan(IT_PATH))
        it_file.write_text("#!/bin/bash\necho e2e extended for feature\n")
        out = self._run_checkpoint(tmp_path)
        check = out.get("checks", {}).get("integration_test_present", {})
        assert check.get("status") == "PASS", check
        assert "integration_test_present" not in out.get("blockers", [])

    def test_parent_only_declaration_seen(self, tmp_path):
        """Modular plan where only the PARENT declares integration_test —
        the declared path is still checked (FAIL: missing on disk)."""
        module = (
            "---\nschema_version: 1\nfeature_archetype: extension\n"
            "tasks:\n  - id: 2\n    title: M\n---\n"
            + f"# Module B\n\n{_H} 2: M\n- [x] done\n"
        )
        self._setup_repo(tmp_path, _c2_plan(IT_PATH), module_content=module)
        out = self._run_checkpoint(
            tmp_path, additional_plan_files=[str(tmp_path / "mod-b.md")]
        )
        check = out.get("checks", {}).get("integration_test_present", {})
        assert check.get("status") == "FAIL", check
        assert IT_PATH in check.get("detail", ""), check
        assert "integration_test_present" in out.get("blockers", [])

    def test_stale_origin_head_does_not_widen_changeset(self, tmp_path):
        """Stale origin/HEAD must NOT win base-ref selection (fail-open guard).

        origin/HEAD is fabricated as a symbolic ref pinned at the BASE commit
        (simulating local-only merges never pushed). Local main then advances
        with an intermediate commit that modifies the declared integration
        test path (a PRIOR feature's work); the feature branch (current HEAD)
        does NOT touch it; clean tree. First-resolvable selection picks the
        stale origin/HEAD, whose merge-base window covers the prior feature's
        change → PASS (fail-open). Newest-merge-base selection picks main →
        the declared test is NOT in this feature's changeset → FAIL.
        """
        self._setup_repo(tmp_path, _c2_plan(IT_PATH))  # base commit on main
        base_sha = self._git(tmp_path, "rev-parse", "HEAD").stdout.strip()
        # Fabricate a stale origin: origin/main pinned at the base commit,
        # origin/HEAD as a symbolic ref pointing at it.
        self._git(tmp_path, "update-ref", "refs/remotes/origin/main", base_sha)
        self._git(
            tmp_path,
            "symbolic-ref",
            "refs/remotes/origin/HEAD",
            "refs/remotes/origin/main",
        )
        # Prior feature (stale window): advance main, modifying the declared
        # IT path. Explicit later dates make merge-base recency deterministic.
        it_file = tmp_path / IT_PATH
        it_file.parent.mkdir(parents=True)
        it_file.write_text("#!/bin/bash\necho e2e from a PRIOR feature\n")
        self._git(tmp_path, "add", IT_PATH)
        self._git(
            tmp_path,
            "commit",
            "-q",
            "-m",
            "prior feature adds e2e",
            date="2030-01-01T00:00:00 +0000",
        )
        # This feature's branch: does NOT touch the IT path; clean tree.
        self._git(tmp_path, "checkout", "-q", "-b", "feature")
        (tmp_path / "feature.txt").write_text("feature work\n")
        self._git(tmp_path, "add", "feature.txt")
        self._git(
            tmp_path,
            "commit",
            "-q",
            "-m",
            "feature work",
            date="2030-01-02T00:00:00 +0000",
        )
        status = self._git(tmp_path, "status", "--porcelain")
        assert status.stdout.strip() == "", "fixture requires a clean working tree"
        out = self._run_checkpoint(tmp_path)
        check = out.get("checks", {}).get("integration_test_present", {})
        assert check.get("status") == "FAIL", check
        assert "changeset" in check.get("detail", "").lower(), check
        assert "integration_test_present" in out.get("blockers", [])

    def test_flat_string_declaration_fails(self, tmp_path):
        """integration_test: <bare string> (the natural authoring mistake) —
        present-but-malformed must FAIL with the expected shape named, not
        silently report PASS skipped (fail-open guard)."""
        plan = (
            "---\nschema_version: 1\nfeature_archetype: extension\n"
            "integration_test: {}\n".format(IT_PATH)
            + "tasks:\n  - id: 1\n    title: T\n---\n"
            + f"# Plan\n\n**Source Contracts:** None\n\n{_H} 1: T\n- [x] done\n"
        )
        self._setup_repo(tmp_path, plan)
        out = self._run_checkpoint(tmp_path)
        check = out.get("checks", {}).get("integration_test_present", {})
        assert check.get("status") == "FAIL", check
        detail = check.get("detail", "").lower()
        assert "malformed" in detail, check
        # Detail must name the expected shape: a mapping with a 'path' key.
        assert "mapping" in detail and "path" in detail, check
        assert "integration_test_present" in out.get("blockers", [])

    def test_empty_path_declaration_fails(self, tmp_path):
        """integration_test: {path: ""} — declared but empty path must FAIL."""
        plan = (
            "---\nschema_version: 1\nfeature_archetype: extension\n"
            'integration_test:\n  path: ""\n'
            "tasks:\n  - id: 1\n    title: T\n---\n"
            + f"# Plan\n\n**Source Contracts:** None\n\n{_H} 1: T\n- [x] done\n"
        )
        self._setup_repo(tmp_path, plan)
        out = self._run_checkpoint(tmp_path)
        check = out.get("checks", {}).get("integration_test_present", {})
        assert check.get("status") == "FAIL", check
        assert "empty" in check.get("detail", "").lower(), check
        assert "integration_test_present" in out.get("blockers", [])

    def test_merge_base_committed_on_branch_clean_tree_passes(self, tmp_path):
        """Audit Order 1 (7th fixture): PRIMARY merge-base diff path.

        Base commit on main; integration test file committed ON a feature
        branch; working tree CLEAN. merge-base(main, HEAD) != HEAD, so only
        the merge-base diff sees the file — the fallback (diff vs HEAD) and
        the untracked scan both see nothing. PASS proves the primary path ran.
        This is the exact shape this feature itself hits at its own
        pre-completion.
        """
        self._setup_repo(tmp_path, _c2_plan(IT_PATH))
        self._git(tmp_path, "checkout", "-q", "-b", "feature")
        it_file = tmp_path / IT_PATH
        it_file.parent.mkdir(parents=True)
        it_file.write_text("#!/bin/bash\necho e2e\n")
        self._git(tmp_path, "add", IT_PATH)
        self._git(tmp_path, "commit", "-q", "-m", "add integration test")
        status = self._git(tmp_path, "status", "--porcelain")
        assert status.stdout.strip() == "", "fixture requires a clean working tree"
        out = self._run_checkpoint(tmp_path)
        check = out.get("checks", {}).get("integration_test_present", {})
        assert check.get("status") == "PASS", check
        assert "integration_test_present" not in out.get("blockers", [])


class TestGitRunSSOT:
    """N25(c): module-level _git_run swallows failures, returns CompletedProcess|None."""

    def test_git_run_handles_failure(self):
        # A failing git invocation (bad cwd) returns CompletedProcess(rc!=0) —
        # git execs fine and exits 128 without raising, so subprocess.run does
        # not throw. Callers gate on returncode. _git_run returns None ONLY on
        # TimeoutExpired / OSError (the except branch).
        result = _vp_ckpt._git_run(["status"], cwd="/no/such/dir/xyz")
        assert result is None or result.returncode != 0

    def test_git_run_returns_completed_process(self, tmp_path):
        import subprocess
        repo = str(tmp_path)
        subprocess.run(["git", "-C", repo, "init", "-q"], check=True)
        result = _vp_ckpt._git_run(["rev-parse", "--is-inside-work-tree"], cwd=repo)
        assert result is not None and result.returncode == 0


# N25(a): feature dir is a REAL subdir (not ".") so _feature_window_base's
# `git log -- <feature_dir>` distinguishes the feature-dir commit from a
# pre-window commit; "." would make every root commit the feature window.
_FEATURE_DIR = "docs/imp-plans/feat"


class TestFeatureWindowBase:
    """N25(a): _merge_base_is_head, _feature_window_base, and on-main Check 10.

    When SDD runs ON the base branch in a remoteless repo, _resolve_base_ref
    picks "main" and merge-base(main, HEAD) == HEAD, so the diff window vs
    merge-base is empty and committed feature files are invisible to
    _in_changeset. N25(a) recomputes an effective base = parent of the first
    commit touching the feature dir (root-commit edge → empty tree). Fail-closed
    is preserved: a file committed BEFORE the feature window still FAILs.

    Assertions target ONLY the integration_test_present check entry and blocker
    (other pre-completion checks legitimately FAIL in these minimal fixtures).
    """

    def _git(self, repo, *args):
        return subprocess.run(
            ["git", "-C", str(repo)] + list(args),
            capture_output=True,
            text=True,
            check=True,
            env=_GIT_ENV,
        )

    def _init_main_repo(self, tmp_path):
        """git init -b main, NO origin → _resolve_base_ref picks 'main' and
        merge-base(main, HEAD) == HEAD (the on-base-branch precondition)."""
        subprocess.run(
            ["git", "init", "-q", "-b", "main", str(tmp_path)],
            capture_output=True,
            text=True,
            check=True,
            env=_GIT_ENV,
        )
        self._git(tmp_path, "config", "user.email", "test@example.com")
        self._git(tmp_path, "config", "user.name", "Test")
        self._git(tmp_path, "config", "commit.gpgsign", "false")

    def _write_feat_manifest(self, tmp_path):
        """Author the manifest at <root>/<_FEATURE_DIR>/.sdd-session.json with
        feature_dir = _FEATURE_DIR and plan_file pointing at the committed
        plan.md (so _load_all_plan_contents succeeds and manifest_feature_dir is
        populated — pure file write, no git, so commit ordering stays ours)."""
        from sdd_test_helpers import _write_manifest

        _write_manifest(
            root=str(tmp_path),
            feature_dir=_FEATURE_DIR,
            reports_rel=os.path.join(_FEATURE_DIR, "reports"),
            deviations_rel=os.path.join(_FEATURE_DIR, "DEVIATIONS.md"),
            plan_rel=os.path.join(_FEATURE_DIR, "plan.md"),
            task_count=1,
        )
        # _write_manifest also drops a root-level .active-feature (hook input,
        # NOT read by controller-checkpoint.py — it loads the manifest by
        # explicit path). Remove it so the working tree stays clean for the
        # _in_changeset untracked short-circuit precondition.
        af = tmp_path / ".active-feature"
        if af.exists():
            af.unlink()

    def _run_manifest_checkpoint(self, tmp_path):
        manifest = os.path.join(tmp_path, _FEATURE_DIR, ".sdd-session.json")
        cmd = [
            sys.executable,
            CHECKPOINT_SCRIPT,
            "--phase",
            "pre-completion",
            "--manifest",
            manifest,
            "--plan-file",
            os.path.join(tmp_path, _FEATURE_DIR, "plan.md"),
            "--deviations-file",
            os.path.join(tmp_path, _FEATURE_DIR, "DEVIATIONS.md"),
            "--reports-dir",
            os.path.join(tmp_path, _FEATURE_DIR, "reports"),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        assert result.stdout.strip(), f"checkpoint produced no output: {result.stderr}"
        return json.loads(result.stdout)

    def test_feature_window_base_none_when_no_feature_commit(self, tmp_path):
        repo = str(tmp_path)
        subprocess.run(
            ["git", "-C", repo, "init", "-q", "-b", "main"],
            check=True,
            env=_GIT_ENV,
        )
        assert _vp_ckpt._feature_window_base(repo, _FEATURE_DIR) is None

    def test_on_main_committed_integration_test_passes(self, tmp_path):
        """Remoteless repo, work on main, integration test COMMITTED in the
        feature window → PASS (today FAILs — merge-base==HEAD hides it).

        Feature dir committed FIRST (repo ROOT) → _feature_window_base returns
        the empty-tree SHA; the IT committed as commit 2 → Step 3b's direct
        diff(empty-tree, worktree) sees it. The IT is committed AND the tree is
        clean, so _in_changeset's untracked short-circuit does NOT fire — the
        new empty-tree path is what makes this PASS.
        """
        self._init_main_repo(tmp_path)
        # Commit 1 (ROOT): the feature dir, including the plan.md that declares
        # the integration test → becomes _feature_window_base's empty-tree edge.
        feat = tmp_path / _FEATURE_DIR
        feat.mkdir(parents=True)
        (feat / "plan.md").write_text(_c2_plan(IT_PATH))
        (feat / "DEVIATIONS.md").write_text("")
        (feat / "reports").mkdir()
        (feat / "reports" / ".keep").write_text("")
        self._write_feat_manifest(tmp_path)
        self._git(tmp_path, "add", _FEATURE_DIR)
        self._git(tmp_path, "commit", "-q", "-m", "feature dir (root)")
        # Commit 2: the declared integration test, inside the feature window.
        it_file = tmp_path / IT_PATH
        it_file.parent.mkdir(parents=True)
        it_file.write_text("#!/bin/bash\necho e2e\n")
        self._git(tmp_path, "add", IT_PATH)
        self._git(tmp_path, "commit", "-q", "-m", "add integration test")
        status = self._git(tmp_path, "status", "--porcelain")
        assert status.stdout.strip() == "", "fixture requires a clean working tree"
        out = self._run_manifest_checkpoint(tmp_path)
        check = out.get("checks", {}).get("integration_test_present", {})
        assert check.get("status") == "PASS", check
        assert "integration_test_present" not in out.get("blockers", [])

    def test_on_main_prewindow_file_still_fails(self, tmp_path):
        """Counter-fixture (fail-closed): a file committed BEFORE the feature
        window still FAILs. The IT is committed as the ROOT (pre-window); the
        feature dir is committed as commit 2 → _feature_window_base returns a
        REAL parent (commit 1) → diff(commit1, HEAD) for the IT is empty → FAIL.
        """
        self._init_main_repo(tmp_path)
        # Commit 1 (ROOT, PRE-WINDOW): the integration test, BEFORE the feature.
        it_file = tmp_path / IT_PATH
        it_file.parent.mkdir(parents=True)
        it_file.write_text("#!/bin/bash\necho e2e\n")
        self._git(tmp_path, "add", IT_PATH)
        self._git(tmp_path, "commit", "-q", "-m", "pre-window integration test")
        # Commit 2: the feature dir opens the window AFTER the IT already exists.
        feat = tmp_path / _FEATURE_DIR
        feat.mkdir(parents=True)
        (feat / "plan.md").write_text(_c2_plan(IT_PATH))
        (feat / "DEVIATIONS.md").write_text("")
        (feat / "reports").mkdir()
        (feat / "reports" / ".keep").write_text("")
        self._write_feat_manifest(tmp_path)
        self._git(tmp_path, "add", _FEATURE_DIR)
        self._git(tmp_path, "commit", "-q", "-m", "feature dir (post-window)")
        status = self._git(tmp_path, "status", "--porcelain")
        assert status.stdout.strip() == "", "fixture requires a clean working tree"
        out = self._run_manifest_checkpoint(tmp_path)
        check = out.get("checks", {}).get("integration_test_present", {})
        assert check.get("status") == "FAIL", check
        assert "changeset" in check.get("detail", "").lower(), check
        assert "integration_test_present" in out.get("blockers", [])

    def test_on_main_real_parent_window_passes(self, tmp_path):
        """Real-parent path (non-root feature window) → PASS. The feature dir is
        committed at commit 2 (a throwaway file is the pre-window ROOT), so
        _feature_window_base returns commit 1's SHA (a real parent, NOT the empty
        tree); the IT committed in-window (commit 3) is seen by
        diff(real_parent, HEAD). Exercises the effective_base = real-parent branch
        in the PASS direction (the most production-shaped on-base case).
        """
        self._init_main_repo(tmp_path)
        # Commit 1 (ROOT, pre-window): a throwaway file unrelated to the feature.
        (tmp_path / "README.md").write_text("pre-window\n")
        self._git(tmp_path, "add", "README.md")
        self._git(tmp_path, "commit", "-q", "-m", "pre-window root")
        # Commit 2: the feature dir opens the window at a NON-root commit.
        feat = tmp_path / _FEATURE_DIR
        feat.mkdir(parents=True)
        (feat / "plan.md").write_text(_c2_plan(IT_PATH))
        (feat / "DEVIATIONS.md").write_text("")
        (feat / "reports").mkdir()
        (feat / "reports" / ".keep").write_text("")
        self._write_feat_manifest(tmp_path)
        self._git(tmp_path, "add", _FEATURE_DIR)
        self._git(tmp_path, "commit", "-q", "-m", "feature dir (non-root)")
        # Commit 3: the declared integration test, inside the feature window.
        it_file = tmp_path / IT_PATH
        it_file.parent.mkdir(parents=True)
        it_file.write_text("#!/bin/bash\necho e2e\n")
        self._git(tmp_path, "add", IT_PATH)
        self._git(tmp_path, "commit", "-q", "-m", "add integration test")
        status = self._git(tmp_path, "status", "--porcelain")
        assert status.stdout.strip() == "", "fixture requires a clean working tree"
        out = self._run_manifest_checkpoint(tmp_path)
        check = out.get("checks", {}).get("integration_test_present", {})
        assert check.get("status") == "PASS", check
        assert "integration_test_present" not in out.get("blockers", [])
