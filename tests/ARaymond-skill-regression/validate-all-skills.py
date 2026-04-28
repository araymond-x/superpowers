#!/usr/bin/env python3
"""
validate-all-skills.py

Regression test script that validates all structural requirements across the custom
skill files in the superpowers custom fork.

Checks every structural requirement established during the improvement session:
frontmatter compliance, size limits, script infrastructure, cross-references,
required sections, critical fix verification, prompt template checks, and
Python 3.9 compatibility.

Exit codes:
  0 - All checks pass (or only warnings)
  1 - One or more FAIL results
  2 - Only warnings (no fails) — same as 0 but indicates review recommended

Usage:
  python validate-all-skills.py
  python validate-all-skills.py --skills-dir /path/to/skills
"""

import argparse
import os
import re
import sys

# ---------------------------------------------------------------------------
# Result tracking
# ---------------------------------------------------------------------------

PASS = "PASS"
FAIL = "FAIL"
WARN = "WARNING"

_results = []  # List of (level, category, message)


def record(level, category, message):
    """Record a check result."""
    _results.append((level, category, message))


def check_pass(category, message):
    record(PASS, category, message)


def check_fail(category, message):
    record(FAIL, category, message)


def check_warn(category, message):
    record(WARN, category, message)


# ---------------------------------------------------------------------------
# File reading helpers
# ---------------------------------------------------------------------------


def read_file(path):
    """Read a file and return its contents, or None on error."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


def parse_frontmatter(content):
    """
    Parse YAML frontmatter between first two --- delimiters.
    Returns (frontmatter_text, body_text).
    frontmatter_text includes the delimiter lines.
    body_text is everything after the closing ---.
    Returns (None, content) if no frontmatter found.
    """
    lines = content.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return None, content

    # Find closing ---
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        return None, content

    fm_text = "".join(lines[: end_idx + 1])
    body_text = "".join(lines[end_idx + 1 :])
    return fm_text, body_text


def extract_frontmatter_field(frontmatter_text, field_name):
    """
    Extract a field value from frontmatter text.
    Handles both bare values and quoted strings.
    Returns None if not found.
    """
    pattern = re.compile(
        r"^" + re.escape(field_name) + r"\s*:\s*(.+)$",
        re.MULTILINE,
    )
    match = pattern.search(frontmatter_text)
    if not match:
        return None
    value = match.group(1).strip()
    # Strip surrounding quotes
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        value = value[1:-1]
    return value


def count_words(text):
    """Count whitespace-separated words in text."""
    return len(text.split())


# ---------------------------------------------------------------------------
# Category 1: Frontmatter Compliance
# ---------------------------------------------------------------------------

SKILL_V01_FILES = [
    ("brainstorming", "brainstorming/SKILL.md"),
    ("writing-plans", "writing-plans/SKILL.md"),
    ("subagent-driven-development", "subagent-driven-development/SKILL.md"),
    ("handoff-acceptance", "handoff-acceptance/SKILL.md"),
]

# Regex for kebab-case: lowercase letters, digits, hyphens only; no spaces or caps
KEBAB_CASE_RE = re.compile(r"^[a-z][a-z0-9\-]*$")

CATEGORY_1 = "Frontmatter Compliance"


def check_frontmatter_compliance(skills_dir):
    """Category 1: Validate frontmatter fields for each custom SKILL file."""
    for folder_name, rel_path in SKILL_V01_FILES:
        path = os.path.join(skills_dir, rel_path)
        label = rel_path

        content = read_file(path)
        if content is None:
            check_fail(CATEGORY_1, "{}: file not found at {}".format(label, path))
            continue

        fm_text, body_text = parse_frontmatter(content)
        if fm_text is None:
            check_fail(CATEGORY_1, "{}: no frontmatter found".format(label))
            continue

        # name field exists
        name_val = extract_frontmatter_field(fm_text, "name")
        if name_val is None:
            check_fail(
                CATEGORY_1, "{}: 'name' field missing from frontmatter".format(label)
            )
        else:
            # name is kebab-case
            if KEBAB_CASE_RE.match(name_val):
                check_pass(
                    CATEGORY_1, "{}: name '{}' is kebab-case".format(label, name_val)
                )
            else:
                check_fail(
                    CATEGORY_1,
                    "{}: name '{}' is not kebab-case (contains spaces, capitals, or version suffix)".format(
                        label, name_val
                    ),
                )

            # name matches folder
            if name_val == folder_name:
                check_pass(
                    CATEGORY_1,
                    "{}: name '{}' matches folder '{}'".format(
                        label, name_val, folder_name
                    ),
                )
            else:
                check_fail(
                    CATEGORY_1,
                    "{}: name '{}' does not match folder '{}'".format(
                        label, name_val, folder_name
                    ),
                )

            # no -v0.1 in name
            if "-v0." in name_val or name_val.endswith("-v0.1"):
                check_fail(
                    CATEGORY_1,
                    "{}: name '{}' contains a version suffix — version tags must not appear in frontmatter names".format(
                        label, name_val
                    ),
                )
            else:
                check_pass(CATEGORY_1, "{}: name has no version suffix".format(label))

        # description field exists
        desc_val = extract_frontmatter_field(fm_text, "description")
        if desc_val is None:
            check_fail(
                CATEGORY_1,
                "{}: 'description' field missing from frontmatter".format(label),
            )
        else:
            # description under 1024 chars
            if len(desc_val) <= 1024:
                check_pass(
                    CATEGORY_1,
                    "{}: description is {} chars (under 1024)".format(
                        label, len(desc_val)
                    ),
                )
            else:
                check_fail(
                    CATEGORY_1,
                    "{}: description is {} chars (over 1024 limit)".format(
                        label, len(desc_val)
                    ),
                )

            # description contains WHEN trigger phrase
            when_pattern = re.compile(
                r"(use when|when to use|use this when|before any|Use when)",
                re.IGNORECASE,
            )
            if when_pattern.search(desc_val):
                check_pass(
                    CATEGORY_1,
                    "{}: description contains WHEN trigger phrase".format(label),
                )
            else:
                check_warn(
                    CATEGORY_1,
                    "{}: description may lack WHEN trigger phrase (check for 'Use when' or similar)".format(
                        label
                    ),
                )

        # No XML angle brackets in frontmatter (between --- delimiters only)
        # Strip delimiter lines themselves, check the inner content
        fm_inner_lines = fm_text.splitlines()[1:-1]  # exclude opening and closing ---
        fm_inner = "\n".join(fm_inner_lines)
        if "<" in fm_inner or ">" in fm_inner:
            check_fail(
                CATEGORY_1,
                "{}: frontmatter contains XML angle brackets (< or >) — these break YAML parsing".format(
                    label
                ),
            )
        else:
            check_pass(
                CATEGORY_1, "{}: frontmatter has no XML angle brackets".format(label)
            )


# ---------------------------------------------------------------------------
# Category 2: Size Limits
# ---------------------------------------------------------------------------

WORD_LIMIT = 5000
WORD_WARNING = 4000

CATEGORY_2 = "Size Limits"

SIZE_CHECK_FILES = [
    ("brainstorming/SKILL.md", "brainstorming SKILL"),
    ("writing-plans/SKILL.md", "writing-plans SKILL"),
    ("subagent-driven-development/SKILL.md", "SDD SKILL"),
    ("handoff-acceptance/SKILL.md", "handoff-acceptance SKILL"),
]


def check_size_limits(skills_dir):
    """Category 2: Check that each SKILL.md body is under 5000 words."""
    for rel_path, label in SIZE_CHECK_FILES:
        path = os.path.join(skills_dir, rel_path)
        content = read_file(path)
        if content is None:
            check_fail(CATEGORY_2, "{}: file not found".format(label))
            continue

        _fm_text, body_text = parse_frontmatter(content)
        wc = count_words(body_text)

        if wc > WORD_LIMIT:
            check_fail(
                CATEGORY_2,
                "{}: {} words (over {} limit)".format(label, wc, WORD_LIMIT),
            )
        elif wc > WORD_WARNING:
            check_warn(
                CATEGORY_2,
                "{}: {} words (over {} warning threshold, under {} limit)".format(
                    label, wc, WORD_WARNING, WORD_LIMIT
                ),
            )
        else:
            check_pass(
                CATEGORY_2, "{}: {} words (under {})".format(label, wc, WORD_LIMIT)
            )


# ---------------------------------------------------------------------------
# Category 3: Script Infrastructure
# ---------------------------------------------------------------------------

CATEGORY_3 = "Script Infrastructure"

REQUIRED_SCRIPTS = [
    ("scripts/_report_utils.py", False),  # library — not required to be executable
    ("scripts/estimate-task-tokens.py", True),
    ("scripts/validate-report.py", True),
    ("scripts/controller-checkpoint.py", True),
    ("scripts/context-summary.py", True),
]


def check_script_infrastructure(skills_dir):
    """Category 3: Verify all expected scripts exist, have shebangs, and key imports."""
    sdd_dir = os.path.join(skills_dir, "subagent-driven-development")

    for rel_path, needs_shebang in REQUIRED_SCRIPTS:
        path = os.path.join(sdd_dir, rel_path)
        script_name = os.path.basename(path)

        content = read_file(path)
        if content is None:
            check_fail(CATEGORY_3, "{}: file not found at {}".format(script_name, path))
            continue

        check_pass(CATEGORY_3, "{}: exists".format(script_name))

        # Check shebang
        if needs_shebang:
            if content.startswith("#!/usr/bin/env python3"):
                check_pass(CATEGORY_3, "{}: has shebang line".format(script_name))
            else:
                check_fail(
                    CATEGORY_3,
                    "{}: missing shebang '#!/usr/bin/env python3'".format(script_name),
                )
        else:
            # Library file — shebang not required but check it has module-level docstring
            if '"""' in content[:200] or "'''" in content[:200]:
                check_pass(CATEGORY_3, "{}: has module docstring".format(script_name))
            else:
                check_warn(
                    CATEGORY_3, "{}: no module docstring found".format(script_name)
                )

    # validate-report.py imports from _report_utils (not duplicated logic)
    validate_report_path = os.path.join(sdd_dir, "scripts/validate-report.py")
    vr_content = read_file(validate_report_path)
    if vr_content is not None:
        if "from _report_utils import" in vr_content:
            check_pass(
                CATEGORY_3,
                "validate-report.py imports from _report_utils (no duplicated logic)",
            )
        else:
            check_fail(
                CATEGORY_3,
                "validate-report.py does not import from _report_utils — logic may be duplicated",
            )

    # estimate-task-tokens.py is executable (has +x bit)
    est_path = os.path.join(sdd_dir, "scripts/estimate-task-tokens.py")
    if os.path.isfile(est_path):
        if os.access(est_path, os.X_OK):
            check_pass(CATEGORY_3, "estimate-task-tokens.py is executable")
        else:
            check_warn(
                CATEGORY_3,
                "estimate-task-tokens.py is not executable (chmod +x may be needed for direct invocation)",
            )


# ---------------------------------------------------------------------------
# Category 4: Cross-References
# ---------------------------------------------------------------------------

CATEGORY_4 = "Cross-References"


def check_cross_references(skills_dir):
    """Category 4: Verify cross-references are correct in each SKILL file."""
    # SDD SKILL references script paths with ~/.claude/skills/superpowers/ prefix
    sdd_path = os.path.join(skills_dir, "subagent-driven-development/SKILL.md")
    sdd_content = read_file(sdd_path)

    if sdd_content is None:
        check_fail(CATEGORY_4, "SDD SKILL.md: file not found")
    else:
        # Script paths should use ~/.claude/skills/superpowers/ prefix
        if "~/.claude/skills/superpowers/" in sdd_content:
            check_pass(
                CATEGORY_4,
                "SDD SKILL: script paths use ~/.claude/skills/superpowers/ prefix",
            )
        else:
            check_fail(
                CATEGORY_4,
                "SDD SKILL: script paths do not use ~/.claude/skills/superpowers/ prefix (bare 'scripts/' paths would break outside install dir)",
            )

        # SDD SKILL has hooks frontmatter for process-level enforcement
        if "hooks:" in sdd_content and "PreToolUse" in sdd_content and 'matcher: "Agent"' in sdd_content:
            check_pass(
                CATEGORY_4,
                "SDD SKILL: has PreToolUse hook on Agent tool in frontmatter",
            )
        else:
            check_fail(
                CATEGORY_4,
                "SDD SKILL: missing hooks frontmatter (PreToolUse on Agent) — process-level enforcement not active",
            )

        # Hook script exists and is executable
        hook_script = os.path.join(
            skills_dir, "subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh"
        )
        if os.path.isfile(hook_script) and os.access(hook_script, os.X_OK):
            check_pass(
                CATEGORY_4,
                "SDD SKILL: sdd-pre-dispatch-hook.sh exists and is executable",
            )
        else:
            check_fail(
                CATEGORY_4,
                "SDD SKILL: sdd-pre-dispatch-hook.sh missing or not executable — hook will fail silently",
            )

        # Branch safety script exists
        branch_script = os.path.join(
            skills_dir, "subagent-driven-development/scripts/check-safe-branch.sh"
        )
        if os.path.isfile(branch_script) and os.access(branch_script, os.X_OK):
            check_pass(CATEGORY_4, "SDD SKILL: check-safe-branch.sh exists and is executable")
        else:
            check_fail(CATEGORY_4, "SDD SKILL: check-safe-branch.sh missing or not executable")

        # Hook scripts: sdd-stop-hook.sh
        stop_hook = os.path.join(
            skills_dir, "subagent-driven-development/scripts/sdd-stop-hook.sh"
        )
        if os.path.isfile(stop_hook) and os.access(stop_hook, os.X_OK):
            check_pass(CATEGORY_4, "SDD: sdd-stop-hook.sh exists and is executable")
        else:
            check_fail(CATEGORY_4, "SDD: sdd-stop-hook.sh missing or not executable")

        # Hook scripts: sdd-report-guard.sh
        report_guard = os.path.join(
            skills_dir, "subagent-driven-development/scripts/sdd-report-guard.sh"
        )
        if os.path.isfile(report_guard) and os.access(report_guard, os.X_OK):
            check_pass(CATEGORY_4, "SDD: sdd-report-guard.sh exists and is executable")
        else:
            check_fail(CATEGORY_4, "SDD: sdd-report-guard.sh missing or not executable")

        # Hook scripts: handoff-gate-hook.sh
        handoff_gate = os.path.join(
            skills_dir, "handoff-acceptance/scripts/handoff-gate-hook.sh"
        )
        if os.path.isfile(handoff_gate) and os.access(handoff_gate, os.X_OK):
            check_pass(CATEGORY_4, "handoff-acceptance: handoff-gate-hook.sh exists and is executable")
        else:
            check_fail(CATEGORY_4, "handoff-acceptance: handoff-gate-hook.sh missing or not executable")

        # Pre-execution audit prompt template
        audit_prompt = os.path.join(
            skills_dir, "subagent-driven-development/pre-execution-audit-prompt.md"
        )
        if os.path.isfile(audit_prompt):
            check_pass(CATEGORY_4, "SDD: pre-execution-audit-prompt.md exists")
        else:
            check_fail(CATEGORY_4, "SDD: pre-execution-audit-prompt.md missing — pre-execution audit gate broken")

        # SDD SKILL references implementer, spec-reviewer, code-quality-reviewer prompt templates
        for prompt_file in [
            "./implementer-prompt.md",
            "./spec-reviewer-prompt.md",
            "./code-quality-reviewer-prompt.md",
        ]:
            if prompt_file in sdd_content:
                check_pass(CATEGORY_4, "SDD SKILL: references {}".format(prompt_file))
            else:
                check_fail(
                    CATEGORY_4,
                    "SDD SKILL: missing reference to {}".format(prompt_file),
                )

    # Brainstorming SKILL references required prompt files
    brain_path = os.path.join(skills_dir, "brainstorming/SKILL.md")
    brain_content = read_file(brain_path)

    if brain_content is None:
        check_fail(CATEGORY_4, "brainstorming SKILL.md: file not found")
    else:
        for ref_file in [
            "spec-document-reviewer-prompt.md",
            "distillation-reviewer-prompt.md",
        ]:
            if ref_file in brain_content:
                check_pass(
                    CATEGORY_4,
                    "brainstorming SKILL: references {}".format(ref_file),
                )
            else:
                check_fail(
                    CATEGORY_4,
                    "brainstorming SKILL: missing reference to {}".format(ref_file),
                )

    # writing-plans SKILL references plan-document-reviewer-prompt.md
    wp_path = os.path.join(skills_dir, "writing-plans/SKILL.md")
    wp_content = read_file(wp_path)

    if wp_content is None:
        check_fail(CATEGORY_4, "writing-plans SKILL.md: file not found")
    else:
        if "plan-document-reviewer-prompt.md" in wp_content:
            check_pass(
                CATEGORY_4,
                "writing-plans SKILL: references plan-document-reviewer-prompt.md",
            )
        else:
            check_fail(
                CATEGORY_4,
                "writing-plans SKILL: missing reference to plan-document-reviewer-prompt.md",
            )

        # F1: validate-plan.py cross-reference from writing-plans
        if "validate-plan.py" in wp_content:
            check_pass(
                CATEGORY_4,
                "writing-plans SKILL: references validate-plan.py",
            )
        else:
            check_fail(
                CATEGORY_4,
                "writing-plans SKILL: missing reference to validate-plan.py — agents won't find the plan validator",
            )

        # F6: standalone invocation guidance
        if "skipping brainstorming" in wp_content or "invoked directly" in wp_content:
            check_pass(
                CATEGORY_4,
                "writing-plans SKILL: has standalone invocation guidance",
            )
        else:
            check_fail(
                CATEGORY_4,
                "writing-plans SKILL: missing standalone invocation guidance (F6)",
            )

    # F4: handoff-acceptance has ACCEPTED_WITH_REMEDIATION verdict
    ha_path = os.path.join(skills_dir, "handoff-acceptance/SKILL.md")
    ha_content = read_file(ha_path)

    if ha_content is None:
        check_fail(CATEGORY_4, "handoff-acceptance SKILL.md: file not found")
    else:
        if "ACCEPTED_WITH_REMEDIATION" in ha_content:
            check_pass(
                CATEGORY_4,
                "handoff-acceptance SKILL: has ACCEPTED_WITH_REMEDIATION verdict",
            )
        else:
            check_fail(
                CATEGORY_4,
                "handoff-acceptance SKILL: missing ACCEPTED_WITH_REMEDIATION verdict (F4)",
            )

        # F7: contextually illustrative snippet classification
        if (
            "contextually illustrative" in ha_content.lower()
            or "Contextually illustrative" in ha_content
        ):
            check_pass(
                CATEGORY_4,
                "handoff-acceptance SKILL: has contextually-illustrative snippet category",
            )
        else:
            check_fail(
                CATEGORY_4,
                "handoff-acceptance SKILL: missing contextually-illustrative snippet category (F7)",
            )

        # handoff-package-spec.md reference
        if "handoff-package-spec.md" in ha_content:
            check_pass(
                CATEGORY_4,
                "handoff-acceptance SKILL: references handoff-package-spec.md",
            )
        else:
            check_fail(
                CATEGORY_4,
                "handoff-acceptance SKILL: missing reference to handoff-package-spec.md",
            )


# ---------------------------------------------------------------------------
# Category 5: Required Sections
# ---------------------------------------------------------------------------

CATEGORY_5 = "Required Sections"


def has_section(content, header_text):
    """
    Return True if content contains a ## or ### level ATX header matching header_text.
    Matching is case-insensitive substring match.
    """
    pattern = re.compile(
        r"^#{2,4}\s+" + re.escape(header_text),
        re.MULTILINE | re.IGNORECASE,
    )
    return bool(pattern.search(content))


SDD_REQUIRED_SECTIONS = [
    "Plan Ingestion",
    "Task 0: Contract Verification",
    "Contract Constraints Passthrough",
    "Context Budget Management",
    "Controller Health Checkpoints",
    "Context Health Protocol",
    "Review Enforcement",
    "Deviation Tracking",
    "File-Based Report Persistence",
    "Plan Status Tracking",
    "Pre-Completion Gate",
    "Session Recovery",
    "Pre-Execution Audit",
]

WRITING_PLANS_REQUIRED_SECTIONS = [
    "Feature Footprint",
]

BRAINSTORMING_REQUIRED_SECTIONS = [
    "Spec Distillation",
]


def check_required_sections(skills_dir):
    """Category 5: Verify required section headers exist in relevant SKILL files."""
    # SDD sections
    sdd_path = os.path.join(skills_dir, "subagent-driven-development/SKILL.md")
    sdd_content = read_file(sdd_path)

    if sdd_content is None:
        check_fail(CATEGORY_5, "SDD SKILL.md: file not found — skipping section checks")
    else:
        for section in SDD_REQUIRED_SECTIONS:
            if has_section(sdd_content, section):
                check_pass(
                    CATEGORY_5, "SDD SKILL: section '{}' present".format(section)
                )
            else:
                check_fail(
                    CATEGORY_5, "SDD SKILL: section '{}' missing".format(section)
                )

    # writing-plans sections
    wp_path = os.path.join(skills_dir, "writing-plans/SKILL.md")
    wp_content = read_file(wp_path)

    if wp_content is None:
        check_fail(
            CATEGORY_5,
            "writing-plans SKILL.md: file not found — skipping section checks",
        )
    else:
        for section in WRITING_PLANS_REQUIRED_SECTIONS:
            if has_section(wp_content, section):
                check_pass(
                    CATEGORY_5,
                    "writing-plans SKILL: section '{}' present".format(section),
                )
            else:
                check_fail(
                    CATEGORY_5,
                    "writing-plans SKILL: section '{}' missing".format(section),
                )

    # brainstorming sections
    brain_path = os.path.join(skills_dir, "brainstorming/SKILL.md")
    brain_content = read_file(brain_path)

    if brain_content is None:
        check_fail(
            CATEGORY_5,
            "brainstorming SKILL.md: file not found — skipping section checks",
        )
    else:
        for section in BRAINSTORMING_REQUIRED_SECTIONS:
            if has_section(brain_content, section):
                check_pass(
                    CATEGORY_5,
                    "brainstorming SKILL: section '{}' present".format(section),
                )
            else:
                check_fail(
                    CATEGORY_5,
                    "brainstorming SKILL: section '{}' missing".format(section),
                )

    # Worktree SKILL has mandatory session handoff
    wt_path = os.path.join(skills_dir, "using-git-worktrees/SKILL.md")
    wt_content = read_file(wt_path)
    if wt_content:
        if "NEW SESSION REQUIRED" in wt_content:
            check_pass(CATEGORY_5, "worktree SKILL: has mandatory session handoff block")
        else:
            check_fail(CATEGORY_5, "worktree SKILL: missing 'NEW SESSION REQUIRED' handoff block")


# ---------------------------------------------------------------------------
# Category 6: Critical Fix Verification
# ---------------------------------------------------------------------------

CATEGORY_6 = "Critical Fix Verification"


def check_critical_fixes(skills_dir):
    """Category 6: Verify all critical fixes from the improvement session."""
    sdd_dir = os.path.join(skills_dir, "subagent-driven-development")

    # Check 1: No -v0.1 in any SKILL frontmatter name field
    all_skill_files = []
    for dirpath, _dirnames, filenames in os.walk(skills_dir):
        for fname in filenames:
            if fname.startswith("SKILL") and fname.endswith(".md"):
                all_skill_files.append(os.path.join(dirpath, fname))

    for skill_path in sorted(all_skill_files):
        content = read_file(skill_path)
        if content is None:
            continue
        fm_text, _ = parse_frontmatter(content)
        if fm_text is None:
            continue
        name_val = extract_frontmatter_field(fm_text, "name")
        if name_val and ("-v0." in name_val or re.search(r"-v\d+", name_val)):
            check_fail(
                CATEGORY_6,
                "{}: name field '{}' contains version suffix — must not".format(
                    os.path.relpath(skill_path, skills_dir), name_val
                ),
            )
        elif name_val:
            check_pass(
                CATEGORY_6,
                "{}: name '{}' has no version suffix".format(
                    os.path.relpath(skill_path, skills_dir), name_val
                ),
            )

    # Check 2: _report_utils.py exists (shared library created)
    report_utils_path = os.path.join(sdd_dir, "scripts/_report_utils.py")
    if os.path.isfile(report_utils_path):
        check_pass(CATEGORY_6, "_report_utils.py exists (shared library)")
    else:
        check_fail(CATEGORY_6, "_report_utils.py missing — shared library not created")

    # Check 3: validate-report.py imports from _report_utils (not duplicated logic)
    validate_report_path = os.path.join(sdd_dir, "scripts/validate-report.py")
    vr_content = read_file(validate_report_path)
    if vr_content is not None:
        if "from _report_utils import" in vr_content:
            check_pass(
                CATEGORY_6,
                "validate-report.py uses 'from _report_utils import' (no logic duplication)",
            )
        else:
            check_fail(
                CATEGORY_6,
                "validate-report.py does not use 'from _report_utils import' — may have duplicated logic",
            )

    # Check 4: "Tests" section removed from REQUIRED_SECTIONS (moved to YAML frontmatter in Phase 2)
    ru_content = read_file(report_utils_path)
    if ru_content is not None:
        # After Phase 2, "Tests" is in YAML frontmatter, not prose sections.
        # The \btests?\b pattern should no longer appear in REQUIRED_SECTIONS.
        has_tests_in_required = bool(re.search(r'REQUIRED_SECTIONS\s*=\s*\[.*?"Tests"', ru_content, re.DOTALL))
        if not has_tests_in_required:
            check_pass(
                CATEGORY_6,
                r"_report_utils.py: 'Tests' section not in REQUIRED_SECTIONS (moved to YAML frontmatter)",
            )
        else:
            check_fail(
                CATEGORY_6,
                r"_report_utils.py: 'Tests' section still in REQUIRED_SECTIONS — should be removed (Phase 2 moved it to YAML)",
            )

        # Check 5: section_contains_content handles ATX headers (^#{1,4} pattern)
        if "^#{1,4}" in ru_content:
            check_pass(
                CATEGORY_6,
                "_report_utils.py: section_contains_content handles ATX headers (^#{1,4} pattern present)",
            )
        else:
            check_fail(
                CATEGORY_6,
                "_report_utils.py: section_contains_content may not handle ATX headers (^#{1,4} pattern missing)",
            )

    # Check 6: SDD SKILL script paths use ~/.claude/skills/superpowers/
    sdd_skill_path = os.path.join(sdd_dir, "SKILL.md")
    sdd_content = read_file(sdd_skill_path)
    if sdd_content is not None:
        if "~/.claude/skills/superpowers/" in sdd_content:
            check_pass(
                CATEGORY_6,
                "SDD SKILL.md: script paths contain ~/.claude/skills/superpowers/",
            )
        else:
            check_fail(
                CATEGORY_6,
                "SDD SKILL.md: script paths do not contain ~/.claude/skills/superpowers/ — will break outside install dir",
            )

    # Check 7: Brainstorming SKILL contains distillation-reviewer-prompt.md reference
    brain_path = os.path.join(skills_dir, "brainstorming/SKILL.md")
    brain_content = read_file(brain_path)
    if brain_content is not None:
        if "distillation-reviewer-prompt.md" in brain_content:
            check_pass(
                CATEGORY_6,
                "brainstorming SKILL: references distillation-reviewer-prompt.md",
            )
        else:
            check_fail(
                CATEGORY_6,
                "brainstorming SKILL: missing distillation-reviewer-prompt.md reference — distillation review step not wired",
            )

        # Check 8: Brainstorming SKILL contains using-git-worktrees reference (worktree step)
        if "using-git-worktrees" in brain_content:
            check_pass(
                CATEGORY_6,
                "brainstorming SKILL: references using-git-worktrees (worktree creation step present)",
            )
        else:
            check_fail(
                CATEGORY_6,
                "brainstorming SKILL: missing using-git-worktrees reference — worktree step not wired",
            )

    # Pre-dispatch hook has audit report check
    hook_path = os.path.join(skills_dir, "subagent-driven-development/scripts/sdd-pre-dispatch-hook.sh")
    hook_content = read_file(hook_path)
    if hook_content:
        if "pre-execution-audit" in hook_content:
            check_pass(CATEGORY_6, "SDD hook: checks for pre-execution audit report")
        else:
            check_fail(CATEGORY_6, "SDD hook: missing pre-execution audit report check")

        if "MIN_REPORT_BYTES" in hook_content:
            check_pass(CATEGORY_6, "SDD hook: has content validation threshold (MIN_REPORT_BYTES)")
        else:
            check_fail(CATEGORY_6, "SDD hook: missing content validation — empty files would bypass gate")

        if "estimate-task-tokens" in hook_content or "estimate_task_tokens" in hook_content:
            check_pass(CATEGORY_6, "SDD hook: has token budget estimation check")
        else:
            check_fail(CATEGORY_6, "SDD hook: missing token budget estimation — oversized tasks not blocked")

        # Report naming: hook supports zero-padded task-NNN format
        if "task_report_glob" in hook_content or 'printf "%03d"' in hook_content:
            check_pass(CATEGORY_6, "SDD hook: supports task-NNN zero-padded naming")
        else:
            check_fail(CATEGORY_6, "SDD hook: missing task-NNN zero-padded naming support")

        # Report naming: zero-padded only (no backward compat with unpadded task-N)
        # Non-padded fallback was removed because it caused stale report files
        # from prior sessions to mask incomplete new reports.
        if "task-${task_num}" not in hook_content:
            check_pass(CATEGORY_6, "SDD hook: no non-padded fallback (zero-padded only)")
        else:
            check_fail(CATEGORY_6, "SDD hook: still has non-padded task-N fallback — should use zero-padded only")

    # SDD SKILL has report naming convention
    sdd_skill_path = os.path.join(skills_dir, "subagent-driven-development/SKILL.md")
    sdd_skill_content = read_file(sdd_skill_path)
    if sdd_skill_content:
        if "task-NNN" in sdd_skill_content or "task-000" in sdd_skill_content:
            check_pass(CATEGORY_6, "SDD SKILL: documents task-NNN naming convention")
        else:
            check_fail(CATEGORY_6, "SDD SKILL: missing task-NNN naming convention documentation")

        if "Do NOT use module-prefixed" in sdd_skill_content or "do NOT create symlinks" in sdd_skill_content.lower():
            check_pass(CATEGORY_6, "SDD SKILL: prohibits module-prefixed names and symlinks")
        else:
            check_fail(CATEGORY_6, "SDD SKILL: missing prohibition on module-prefixed names")

    # Skill enforcement hook exists (Write|Edit bypass detection)
    enforcement_hook = os.path.join(
        skills_dir, "subagent-driven-development/scripts/sdd-skill-enforcement-hook.sh"
    )
    if os.path.isfile(enforcement_hook) and os.access(enforcement_hook, os.X_OK):
        check_pass(CATEGORY_6, "SDD: sdd-skill-enforcement-hook.sh exists and is executable")
    else:
        check_fail(CATEGORY_6, "SDD: sdd-skill-enforcement-hook.sh missing — Write/Edit bypass detection not active")


# ---------------------------------------------------------------------------
# Category 7: Prompt Template Checks
# ---------------------------------------------------------------------------

CATEGORY_7 = "Prompt Template Checks"

PROMPT_TEMPLATES = [
    (
        "subagent-driven-development/implementer-prompt.md",
        "implementer-prompt",
    ),
    (
        "subagent-driven-development/spec-reviewer-prompt.md",
        "spec-reviewer-prompt",
    ),
    (
        "subagent-driven-development/code-quality-reviewer-prompt.md",
        "code-quality-reviewer-prompt",
    ),
]


def check_prompt_templates(skills_dir):
    """Category 7: Verify prompt templates have required placeholders and sections."""
    for rel_path, label in PROMPT_TEMPLATES:
        path = os.path.join(skills_dir, rel_path)
        content = read_file(path)

        if content is None:
            check_fail(CATEGORY_7, "{}: file not found at {}".format(label, path))
            continue

        # All templates: [CONTROLLER: placeholder guidance
        if "[CONTROLLER:" in content:
            check_pass(
                CATEGORY_7,
                "{}: contains [CONTROLLER: fill-in placeholder(s)".format(label),
            )
        else:
            check_fail(
                CATEGORY_7,
                "{}: missing [CONTROLLER: placeholder — controller fill-in guidance absent".format(
                    label
                ),
            )

    # spec-reviewer: Changed Files or BASE_SHA section
    spec_path = os.path.join(
        skills_dir, "subagent-driven-development/spec-reviewer-prompt.md"
    )
    spec_content = read_file(spec_path)
    if spec_content is not None:
        if "Changed Files" in spec_content or "BASE_SHA" in spec_content:
            check_pass(
                CATEGORY_7,
                "spec-reviewer-prompt: contains 'Changed Files' or 'BASE_SHA' section",
            )
        else:
            check_fail(
                CATEGORY_7,
                "spec-reviewer-prompt: missing 'Changed Files' / 'BASE_SHA' section — reviewer has no way to see diff",
            )

    # code-quality-reviewer: IMPLEMENTER_REPORT placeholder
    cqr_path = os.path.join(
        skills_dir, "subagent-driven-development/code-quality-reviewer-prompt.md"
    )
    cqr_content = read_file(cqr_path)
    if cqr_content is not None:
        if "IMPLEMENTER_REPORT" in cqr_content:
            check_pass(
                CATEGORY_7,
                "code-quality-reviewer-prompt: IMPLEMENTER_REPORT placeholder present",
            )
        else:
            check_fail(
                CATEGORY_7,
                "code-quality-reviewer-prompt: IMPLEMENTER_REPORT placeholder missing — reviewer won't receive implementer report",
            )

    # implementer-prompt: Contract Constraints section
    impl_path = os.path.join(
        skills_dir, "subagent-driven-development/implementer-prompt.md"
    )
    impl_content = read_file(impl_path)
    if impl_content is not None:
        if "Contract Constraints" in impl_content:
            check_pass(
                CATEGORY_7, "implementer-prompt: 'Contract Constraints' section present"
            )
        else:
            check_fail(
                CATEGORY_7,
                "implementer-prompt: 'Contract Constraints' section missing",
            )

        # implementer-prompt: Source Files section
        if "Source Files" in impl_content:
            check_pass(CATEGORY_7, "implementer-prompt: 'Source Files' section present")
        else:
            check_fail(
                CATEGORY_7,
                "implementer-prompt: 'Source Files' section missing",
            )

        # implementer-prompt report format: YAML frontmatter fields + 5 prose sections
        # Phase 2 moved Status, Files Changed, Tests, Contract Compliance to YAML frontmatter
        required_frontmatter_fields = [
            "schema_version",
            "task_id",
            "status",
            "files_changed",
            "tests",
            "contract_compliance",
        ]
        required_prose_sections = [
            "Implementation Summary",
            "Source Files Read",
            "Deviations from Plan",
            "Self-Review Findings",
            "Concerns",
        ]
        missing_fm = [f for f in required_frontmatter_fields if f not in impl_content]
        missing_prose = [s for s in required_prose_sections if s not in impl_content]
        all_missing = missing_fm + missing_prose
        if not all_missing:
            check_pass(
                CATEGORY_7,
                "implementer-prompt: YAML frontmatter fields + 5 prose sections in Report Format",
            )
        else:
            check_fail(
                CATEGORY_7,
                "implementer-prompt: Report Format is missing: {}".format(
                    ", ".join(all_missing)
                ),
            )


# ---------------------------------------------------------------------------
# Category 8: Python 3.9 Compatibility
# ---------------------------------------------------------------------------

CATEGORY_8 = "Python 3.9 Compatibility"

# Matches "X | Y" in a type annotation context.
# Looks for patterns like ": str | None", "-> int | str" outside of string literals.
UNION_SYNTAX_RE = re.compile(
    r"(?::\s*\w[\w\[\], ]*\s*\|\s*\w|->.*\w\s*\|\s*\w)",
)

# list[, dict[, tuple[ used as runtime type hints (not inside strings or comments)
BUILTIN_GENERIC_RE = re.compile(r"\b(list|dict|tuple|set|frozenset)\[")

# Matches string literals: single-quoted, double-quoted, and f-strings.
# Used to strip string content before testing annotation patterns.
STRING_LITERAL_RE = re.compile(
    r"""(?:"[^"\\]*(?:\\.[^"\\]*)*"|'[^'\\]*(?:\\.[^'\\]*)*')"""
)


def strip_string_literals(line):
    """
    Replace string literal content with placeholders so that pattern matching
    does not match content inside string literals.
    For example: 'line {}: X | Y union' -> 'line {}: STRLIT union'
    This is a single-line heuristic; does not handle multi-line strings.
    """
    return STRING_LITERAL_RE.sub("__STRLIT__", line)


def check_python39_compat(skills_dir):
    """Category 8: Check all .py scripts for Python 3.9 incompatibilities."""
    sdd_scripts_dir = os.path.join(skills_dir, "subagent-driven-development/scripts")

    py_files = []
    if os.path.isdir(sdd_scripts_dir):
        for fname in os.listdir(sdd_scripts_dir):
            if fname.endswith(".py"):
                py_files.append(os.path.join(sdd_scripts_dir, fname))

    if not py_files:
        check_warn(CATEGORY_8, "No .py files found in scripts/ directory")
        return

    for py_path in sorted(py_files):
        fname = os.path.basename(py_path)
        content = read_file(py_path)
        if content is None:
            check_fail(CATEGORY_8, "{}: could not read file".format(fname))
            continue

        issues = []

        for lineno, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()

            # Skip blank lines and full-line comments
            if not stripped or stripped.startswith("#"):
                continue

            # Strip string literal content to avoid false positives on message strings
            sanitized = strip_string_literals(stripped)

            # Skip lines that are entirely within a multi-line string (heuristic:
            # if the original stripped line starts with a quote, it's likely a docstring line)
            if stripped.startswith(('"""', "'''")):
                continue

            # Check for X | Y union syntax in annotations
            if UNION_SYNTAX_RE.search(sanitized):
                issues.append(
                    "line {}: X | Y union syntax in annotation (requires Python 3.10+)".format(
                        lineno
                    )
                )

            # Check for builtin generics in annotation contexts
            # Only flag when the line has an annotation marker (: or ->) after stripping strings
            if (":" in sanitized or "->" in sanitized) and BUILTIN_GENERIC_RE.search(
                sanitized
            ):
                match = BUILTIN_GENERIC_RE.search(sanitized)
                if match:
                    issues.append(
                        "line {}: builtin generic '{}[' in annotation context (requires Python 3.10+ for runtime use)".format(
                            lineno, match.group(1)
                        )
                    )

        if issues:
            for issue in issues:
                check_fail(CATEGORY_8, "{}: {}".format(fname, issue))
        else:
            check_pass(
                CATEGORY_8, "{}: no Python 3.9 compatibility issues found".format(fname)
            )


# ---------------------------------------------------------------------------
# Output and summary
# ---------------------------------------------------------------------------


def print_results():
    """Print all results grouped by category with a final summary."""
    # Gather categories in insertion order
    seen_categories = []
    by_category = {}
    for level, category, message in _results:
        if category not in by_category:
            by_category[category] = []
            seen_categories.append(category)
        by_category[category].append((level, message))

    fail_count = 0
    warn_count = 0
    pass_count = 0

    for category in seen_categories:
        print("\n=== {} ===".format(category))
        for level, message in by_category[category]:
            print("  [{}] {}".format(level, message))
            if level == FAIL:
                fail_count += 1
            elif level == WARN:
                warn_count += 1
            else:
                pass_count += 1

    print("\n=== SUMMARY ===")
    print(
        "  PASS: {}  FAIL: {}  WARNING: {}".format(pass_count, fail_count, warn_count)
    )

    if fail_count > 0:
        print("  Result: FAIL")
    elif warn_count > 0:
        print("  Result: PASS (with warnings)")
    else:
        print("  Result: PASS")


def exit_code():
    """Determine exit code from recorded results."""
    fail_count = sum(1 for level, _cat, _msg in _results if level == FAIL)
    warn_count = sum(1 for level, _cat, _msg in _results if level == WARN)
    if fail_count > 0:
        return 1
    if warn_count > 0:
        return 2
    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def default_skills_dir():
    """
    Default skills directory: up to repo root then into skills/.
    Script lives at: tests/ARaymond-skill-regression/validate-all-skills.py
    Skills dir is:   skills/
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(script_dir, "..", "..", "skills"))


def main():
    """Entry point."""
    parser = argparse.ArgumentParser(
        description=(
            "Regression test script for custom superpowers skill files. "
            "Validates frontmatter, size limits, script infrastructure, "
            "cross-references, required sections, critical fixes, prompt templates, "
            "and Python 3.9 compatibility. "
            "Exit code 0=all pass, 1=failures found, 2=warnings only."
        )
    )
    parser.add_argument(
        "--skills-dir",
        default=None,
        metavar="PATH",
        help=(
            "Path to the skills/ directory. "
            "Defaults to two levels up from this script's location."
        ),
    )
    args = parser.parse_args()

    if args.skills_dir is not None:
        skills_dir = args.skills_dir
    else:
        skills_dir = default_skills_dir()

    if not os.path.isdir(skills_dir):
        print(
            "ERROR: skills directory not found: {}".format(skills_dir), file=sys.stderr
        )
        sys.exit(1)

    print("Validating skills in: {}".format(skills_dir))

    check_frontmatter_compliance(skills_dir)
    check_size_limits(skills_dir)
    check_script_infrastructure(skills_dir)
    check_cross_references(skills_dir)
    check_required_sections(skills_dir)
    check_critical_fixes(skills_dir)
    check_prompt_templates(skills_dir)
    check_python39_compat(skills_dir)

    print_results()
    sys.exit(exit_code())


if __name__ == "__main__":
    main()
