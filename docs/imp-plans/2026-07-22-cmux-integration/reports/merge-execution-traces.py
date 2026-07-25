#!/usr/bin/env python3
"""Merge per-session execution traces into one feature-wide trace.

WHY THIS EXISTS
---------------
`extract-execution-trace.py` takes ONE `--session-file`, and the SDD skill's documented
discovery command is `ls -t … | head -1`. A feature that spans many sessions (this one spanned
15) therefore gets audited against its MOST RECENT session only — the auditor sees the last task,
finds nothing, and returns "no anomalies". That is a hollow check: it cannot fail for any task
that happened in an earlier session.

This wrapper extracts every session file and merges the results, recording COVERAGE explicitly so
a reader can see which tasks were actually observed and which were not.

It lives in the feature dir rather than `skills/subagent-driven-development/scripts/` deliberately:
that directory's inventory count is asserted by the customization manifest's
"## Deterministic Scripts (N active)" heading, and this is a one-off audit aid, not a pipeline script.
If multi-session support is ever added natively (see the BACKLOG follow-up), this should be deleted
rather than promoted.

USAGE
-----
    python3 merge-execution-traces.py \
        --session-dir ~/.claude/projects/<encoded-worktree-path> \
        --feature-dir docs/imp-plans/<feature> \
        --output <feature-dir>/reports/execution-trace.json

CAVEAT — READ BEFORE TRUSTING THE OUTPUT
----------------------------------------
As of 2026-07-25 the upstream extractor's six anomaly detectors are INERT: every rule gates on
`subagent_return.found` / `.status`, which the extractor does not populate (verified: `found` is
False and `status` is None for 13/13 task records). So `anomaly_summary_totals` here will read all
zeros REGARDLESS of what happened. Zero anomalies from this file is NOT evidence of a clean run.
Audit against `.dispatch-log`, the report files, and `deviations.md` instead.
"""

import argparse
import glob
import json
import os
import subprocess
import sys

EXTRACTOR = os.path.expanduser(
    "~/.claude/skills/superpowers/subagent-driven-development/scripts/extract-execution-trace.py"
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--session-dir", required=True, help="Directory holding the project's .jsonl session files.")
    ap.add_argument("--feature-dir", required=True, help="Feature directory (for deviations.md / reports/).")
    ap.add_argument("--output", required=True, help="Where to write the merged trace JSON.")
    ap.add_argument("--extractor", default=EXTRACTOR, help="Path to extract-execution-trace.py.")
    ap.add_argument("--expected-tasks", default="0-11", help="Inclusive task range to report coverage against, e.g. 0-11.")
    args = ap.parse_args()

    lo, _, hi = args.expected_tasks.partition("-")
    expected = list(range(int(lo), int(hi) + 1))

    sessions = sorted(glob.glob(os.path.join(os.path.expanduser(args.session_dir), "*.jsonl")))
    if not sessions:
        print(f"ERROR: no .jsonl files under {args.session_dir}", file=sys.stderr)
        return 2

    merged = {
        "coverage": {"session_files_found": len(sessions), "session_files_extracted": 0, "files": []},
        "tasks": [], "skills_invoked": {}, "scripts_run": {},
        "anomaly_summary_totals": {}, "anomaly_details": [],
        "caveat": "Upstream anomaly detectors are inert (subagent_return unpopulated); "
                  "zero anomalies here is NOT evidence of a clean run.",
    }
    failures = []

    for path in sessions:
        base = os.path.basename(path)[:-6]
        # NOTE: the extractor takes --deviations-file/--reports-dir. It does NOT take --feature-dir,
        # despite what SKILL.md's Pre-Completion Gate step 8 shows.
        proc = subprocess.run(
            [sys.executable, args.extractor, "--session-file", path,
             "--deviations-file", os.path.join(args.feature_dir, "deviations.md"),
             "--reports-dir", os.path.join(args.feature_dir, "reports")],
            capture_output=True, text=True,
        )
        if proc.returncode != 0:
            failures.append((base, proc.stderr.strip().splitlines()[-1:] or ["(no stderr)"]))
            continue
        data = json.loads(proc.stdout)
        merged["coverage"]["session_files_extracted"] += 1

        nums = sorted({t.get("task_number") for t in data.get("tasks", []) if t.get("task_number") is not None})
        merged["coverage"]["files"].append({
            "session": base, "messages": data.get("total_messages", 0), "task_numbers": nums,
            "anomalies": (data.get("anomaly_summary") or {}).get("total_anomalies", 0),
        })
        for task in data.get("tasks", []):
            task["_session"] = base
            merged["tasks"].append(task)
        for skill in data.get("skills_invoked", []):
            key = skill if isinstance(skill, str) else json.dumps(skill)
            merged["skills_invoked"][key] = merged["skills_invoked"].get(key, 0) + 1
        for script in data.get("scripts_run", []):
            if isinstance(script, dict):
                key = f"{script.get('script', '?')}:{script.get('phase', '')}"
                merged["scripts_run"][key] = merged["scripts_run"].get(key, 0) + script.get("count", 1)
        for key, val in (data.get("anomaly_summary") or {}).items():
            if isinstance(val, int):
                merged["anomaly_summary_totals"][key] = merged["anomaly_summary_totals"].get(key, 0) + val
        for detail in data.get("anomaly_details", []):
            detail["_session"] = base
            merged["anomaly_details"].append(detail)

    seen = sorted({t.get("task_number") for t in merged["tasks"] if t.get("task_number") is not None})
    merged["coverage"]["distinct_task_numbers_attributed"] = seen
    merged["coverage"]["expected_task_numbers"] = expected
    merged["coverage"]["not_attributed_by_extractor"] = sorted(set(expected) - set(seen))
    merged["coverage"]["extraction_failures"] = failures

    with open(args.output, "w") as handle:
        json.dump(merged, handle, indent=1)

    cov = merged["coverage"]
    print(f"extracted {cov['session_files_extracted']}/{cov['session_files_found']} sessions "
          f"-> {len(merged['tasks'])} task records")
    print(f"task numbers attributed: {seen}")
    if cov["not_attributed_by_extractor"]:
        # Not necessarily a process gap — the extractor's per-session builder can drop a task that a
        # session genuinely contains. Investigate against .dispatch-log before reporting it as one.
        print(f"NOT attributed (investigate, do not assume a gap): {cov['not_attributed_by_extractor']}")
    if failures:
        print(f"EXTRACTION FAILURES: {failures}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
