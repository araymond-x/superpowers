#!/usr/bin/env python3
"""
extract-execution-trace.py

Parses a Claude Code .jsonl session file and extracts a structured execution
trace focused on subagent dispatches, reviews, status reports, and anomaly
detection. Designed for post-session analysis of subagent-driven development
(SDD) sessions.

Usage:
    python extract-execution-trace.py --session-file /path/to/session.jsonl
    python extract-execution-trace.py --session-file /path/to/session.jsonl \\
        --output trace.json \\
        --deviations-file deviations.md \\
        --reports-dir reports/
"""

import argparse
import glob
import json
import os
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Import shared status patterns from _report_utils if available.
# Fall back to inline definitions for portability.
# ---------------------------------------------------------------------------
try:
    import importlib.util

    _utils_path = os.path.join(os.path.dirname(__file__), "_report_utils.py")
    _spec = importlib.util.spec_from_file_location("_report_utils", _utils_path)
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    STATUS_VALUE_PATTERN = _mod.STATUS_VALUE_PATTERN
    VALID_STATUSES = _mod.VALID_STATUSES
except Exception:
    STATUS_VALUE_PATTERN = re.compile(
        r"\b(DONE_WITH_CONCERNS|DONE|BLOCKED|NEEDS_CONTEXT)\b"
    )
    VALID_STATUSES = {"DONE", "DONE_WITH_CONCERNS", "BLOCKED", "NEEDS_CONTEXT"}


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Matches "Task N", "Task N:", "Implement Task N", "Contract Verification" etc.
TASK_NUMBER_PATTERN = re.compile(r"[Tt]ask\s+(\d+)", re.IGNORECASE)

# Skill name from Skill tool calls
SKILL_NAME_PATTERN = re.compile(r'"skill"\s*:\s*"([^"]+)"')

# Matches script names we care about in Bash commands
TRACKED_SCRIPTS = [
    "estimate-task-tokens",
    "controller-checkpoint",
    "validate-report",
    "validate-plan",
    "extract-execution-trace",
]

# Plan checkbox patterns (marking tasks done)
CHECKBOX_DONE_PATTERN = re.compile(r"-\s*\[x\]", re.IGNORECASE)

# Review dispatch indicators in Agent prompts
SPEC_REVIEW_PATTERNS = [
    re.compile(r"spec[\s_-]*compliance", re.IGNORECASE),
    re.compile(r"spec[\s_-]*reviewer", re.IGNORECASE),
    re.compile(r"review\s+spec", re.IGNORECASE),
]
CODE_QUALITY_PATTERNS = [
    re.compile(r"code[\s_-]*quality", re.IGNORECASE),
    re.compile(r"code[\s_-]*reviewer", re.IGNORECASE),
    re.compile(r"quality[\s_-]*reviewer", re.IGNORECASE),
]

# Review result patterns (PASS / FAIL / APPROVED / REJECTED in review returns)
REVIEW_RESULT_PATTERN = re.compile(
    r"\b(PASS|FAIL|APPROVED|REJECTED|APPROVED_WITH_NOTES)\b"
)


# ---------------------------------------------------------------------------
# Low-level message parsing helpers
# ---------------------------------------------------------------------------


def load_messages(session_file: str) -> List[Dict[str, Any]]:
    """
    Load all valid JSON lines from a .jsonl file.
    Returns a list of (line_index, parsed_object) tuples where line_index is
    0-based position in the file.
    """
    messages = []
    with open(session_file, "r", encoding="utf-8") as fh:
        for idx, line in enumerate(fh):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                messages.append((idx, obj))
            except json.JSONDecodeError:
                pass  # Skip malformed lines — partial/interrupted sessions
    return messages


def _get_tool_calls(msg: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract tool_use blocks from an assistant message.
    Returns list of dicts with keys: name, input, id.
    """
    if msg.get("type") != "assistant":
        return []
    message = msg.get("message", {})
    content = message.get("content", [])
    if isinstance(content, str):
        return []
    result = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "tool_use":
            result.append(
                {
                    "name": block.get("name", ""),
                    "input": block.get("input", {}),
                    "id": block.get("id", ""),
                }
            )
    return result


def _get_tool_result_text(msg: Dict[str, Any]) -> Optional[str]:
    """
    For a user message that is a tool_result (or toolUseResult), return the
    result text content if available.
    """
    # Format 1: top-level toolUseResult (subagent returns as seen in analyze-token-usage.py)
    if "toolUseResult" in msg:
        result = msg["toolUseResult"]
        # toolUseResult can be:
        #   - a raw string (error output from Bash / other tools)
        #   - a dict with agentId + content list (Agent subagent returns)
        #   - a dict with commandName + success (skill/command completions)
        # Guard against non-dict before calling .get().
        if isinstance(result, str):
            return result if result else None
        if not isinstance(result, dict):
            return None
        content = result.get("content", "")
        if isinstance(content, list):
            parts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    parts.append(block.get("text", ""))
            return "\n".join(parts)
        return str(content) if content else None

    # Format 2: user message with content list containing tool_result blocks
    if msg.get("type") == "user":
        content = msg.get("message", {}).get("content", [])
        if not isinstance(content, list):
            return None
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_result":
                inner = block.get("content", "")
                if isinstance(inner, list):
                    parts = []
                    for item in inner:
                        if isinstance(item, dict) and item.get("type") == "text":
                            parts.append(item.get("text", ""))
                    return "\n".join(parts)
                return str(inner) if inner else None
    return None


def _is_agent_dispatch(tool_call: Dict[str, Any]) -> bool:
    """Return True if this tool call is an Agent (subagent) dispatch."""
    return tool_call.get("name") == "Agent"


def _is_skill_call(tool_call: Dict[str, Any]) -> bool:
    """Return True if this tool call is a Skill invocation."""
    return tool_call.get("name") == "Skill"


def _get_agent_prompt(tool_call: Dict[str, Any]) -> str:
    """Extract the prompt/description text from an Agent tool call."""
    inp = tool_call.get("input", {})
    return inp.get("prompt", inp.get("description", inp.get("task", "")))


def _get_skill_name(tool_call: Dict[str, Any]) -> str:
    """Extract the skill name from a Skill tool call."""
    inp = tool_call.get("input", {})
    return inp.get("skill", inp.get("name", ""))


def _get_file_path(tool_call: Dict[str, Any]) -> str:
    """Extract file_path from Edit or Write tool calls."""
    inp = tool_call.get("input", {})
    return inp.get("file_path", inp.get("path", ""))


def _get_bash_command(tool_call: Dict[str, Any]) -> str:
    """Extract the command from a Bash tool call."""
    inp = tool_call.get("input", {})
    return inp.get("command", "")


# ---------------------------------------------------------------------------
# Classification helpers
# ---------------------------------------------------------------------------


def classify_agent_dispatch(prompt: str) -> Dict[str, Any]:
    """
    Classify an Agent dispatch as: implementer, spec_review, code_quality, or unknown.
    Returns dict with keys: dispatch_type, task_number, description_snippet.
    """
    task_match = TASK_NUMBER_PATTERN.search(prompt)
    task_number = int(task_match.group(1)) if task_match else None

    snippet = prompt[:120].replace("\n", " ").strip()

    # Spec compliance review
    if any(p.search(prompt) for p in SPEC_REVIEW_PATTERNS):
        return {
            "dispatch_type": "spec_review",
            "task_number": task_number,
            "description_snippet": snippet,
        }

    # Code quality review
    if any(p.search(prompt) for p in CODE_QUALITY_PATTERNS):
        return {
            "dispatch_type": "code_quality",
            "task_number": task_number,
            "description_snippet": snippet,
        }

    # Implementation dispatch — "Task N" or "Implement"
    if task_number is not None or re.search(r"\bimplement\b", prompt, re.IGNORECASE):
        return {
            "dispatch_type": "implementer",
            "task_number": task_number,
            "description_snippet": snippet,
        }

    return {
        "dispatch_type": "unknown",
        "task_number": task_number,
        "description_snippet": snippet,
    }


def extract_review_result(result_text: str) -> Optional[str]:
    """Extract PASS/FAIL/etc. from a review result text."""
    if not result_text:
        return None
    m = REVIEW_RESULT_PATTERN.search(result_text)
    return m.group(1) if m else None


def extract_status(result_text: str) -> str:
    """Extract implementer status from a subagent return."""
    if not result_text:
        return "UNKNOWN"
    m = STATUS_VALUE_PATTERN.search(result_text)
    return m.group(1) if m else "UNKNOWN"


# ---------------------------------------------------------------------------
# Phase 1: Flatten the session into a linear event stream
# ---------------------------------------------------------------------------

Event = Dict[str, Any]


def build_event_stream(messages: List[Tuple[int, Dict[str, Any]]]) -> List[Event]:
    """
    Walk all messages and produce a flat ordered list of typed events.

    Event types:
        agent_dispatch   — Agent tool_use (implementer / spec_review / code_quality / unknown)
        agent_return     — tool_result from a previous Agent call
        skill_invoke     — Skill tool_use
        file_edit        — Edit or Write tool_use
        bash_run         — Bash tool_use
    """
    events: List[Event] = []

    # Map from tool_use id → dispatch event so we can match returns
    pending_agent_dispatches: Dict[str, Event] = {}

    for msg_idx, (line_idx, msg) in enumerate(messages):
        # --- Tool calls from assistant messages ---
        tool_calls = _get_tool_calls(msg)
        for tc in tool_calls:
            name = tc.get("name", "")

            if name == "Agent":
                prompt = _get_agent_prompt(tc)
                classification = classify_agent_dispatch(prompt)
                event: Event = {
                    "event_type": "agent_dispatch",
                    "msg_index": msg_idx,
                    "line_index": line_idx,
                    "tool_id": tc.get("id", ""),
                    "dispatch_type": classification["dispatch_type"],
                    "task_number": classification["task_number"],
                    "description_snippet": classification["description_snippet"],
                    "prompt": prompt,
                }
                events.append(event)
                if tc.get("id"):
                    pending_agent_dispatches[tc["id"]] = event

            elif name == "Skill":
                events.append(
                    {
                        "event_type": "skill_invoke",
                        "msg_index": msg_idx,
                        "line_index": line_idx,
                        "skill_name": _get_skill_name(tc),
                    }
                )

            elif name in ("Edit", "Write"):
                events.append(
                    {
                        "event_type": "file_edit",
                        "msg_index": msg_idx,
                        "line_index": line_idx,
                        "tool_name": name,
                        "file_path": _get_file_path(tc),
                        "tool_id": tc.get("id", ""),
                    }
                )

            elif name == "Bash":
                cmd = _get_bash_command(tc)
                script = _detect_tracked_script(cmd)
                events.append(
                    {
                        "event_type": "bash_run",
                        "msg_index": msg_idx,
                        "line_index": line_idx,
                        "command": cmd,
                        "tracked_script": script,
                    }
                )

        # --- Tool results from user messages ---
        # Format 1: top-level toolUseResult with agentId (subagent SDK format)
        if "toolUseResult" in msg:
            result_obj = msg["toolUseResult"]
            # Skip non-dict results (raw strings, etc.) — they aren't Agent returns
            if not isinstance(result_obj, dict):
                result_obj = {}
            result_text = _get_tool_result_text(msg)
            tool_id = result_obj.get("toolUseId", "")

            if tool_id in pending_agent_dispatches:
                dispatch_event = pending_agent_dispatches[tool_id]
                status = extract_status(result_text or "")
                review_result = extract_review_result(result_text or "")
                events.append(
                    {
                        "event_type": "agent_return",
                        "msg_index": msg_idx,
                        "line_index": line_idx,
                        "tool_id": tool_id,
                        "dispatch_type": dispatch_event["dispatch_type"],
                        "task_number": dispatch_event["task_number"],
                        "status": status,
                        "review_result": review_result,
                        "result_text": result_text or "",
                    }
                )
                del pending_agent_dispatches[tool_id]

        # Format 2: user message content list with tool_result blocks
        elif msg.get("type") == "user":
            content = msg.get("message", {}).get("content", [])
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        tool_id = block.get("tool_use_id", "")
                        if tool_id in pending_agent_dispatches:
                            inner = block.get("content", "")
                            if isinstance(inner, list):
                                parts = [
                                    i.get("text", "")
                                    for i in inner
                                    if isinstance(i, dict) and i.get("type") == "text"
                                ]
                                result_text = "\n".join(parts)
                            else:
                                result_text = str(inner) if inner else ""

                            dispatch_event = pending_agent_dispatches[tool_id]
                            status = extract_status(result_text)
                            review_result = extract_review_result(result_text)
                            events.append(
                                {
                                    "event_type": "agent_return",
                                    "msg_index": msg_idx,
                                    "line_index": line_idx,
                                    "tool_id": tool_id,
                                    "dispatch_type": dispatch_event["dispatch_type"],
                                    "task_number": dispatch_event["task_number"],
                                    "status": status,
                                    "review_result": review_result,
                                    "result_text": result_text,
                                }
                            )
                            del pending_agent_dispatches[tool_id]

    return events


def _detect_tracked_script(command: str) -> Optional[str]:
    """Return the tracked script name if the Bash command runs one, else None."""
    for script in TRACKED_SCRIPTS:
        if script in command:
            return script
    return None


# ---------------------------------------------------------------------------
# Phase 2: Aggregate events into per-task records
# ---------------------------------------------------------------------------


def aggregate_tasks(
    events: List[Event],
    reports_dir: Optional[str],
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Walk the event stream and build per-task records.
    Also returns a list of skill names invoked.

    Task numbers are sourced from implementer dispatch events. If the session
    has no numbered implementer dispatches, returns an empty task list.
    """
    skills_invoked: List[str] = []
    task_map: Dict[int, Dict[str, Any]] = {}
    ordered_task_numbers: List[int] = []

    # ---- Collect skill invocations ----
    for ev in events:
        if ev["event_type"] == "skill_invoke" and ev.get("skill_name"):
            name = ev["skill_name"]
            if name not in skills_invoked:
                skills_invoked.append(name)

    # ---- First pass: create task stubs from implementer dispatches ----
    for ev in events:
        if (
            ev["event_type"] == "agent_dispatch"
            and ev["dispatch_type"] == "implementer"
        ):
            tn = ev.get("task_number")
            if tn is not None and tn not in task_map:
                task_map[tn] = _new_task_record(tn)
                ordered_task_numbers.append(tn)

    # Handle sessions where task number could not be extracted (task_number=None)
    none_tasks: List[Dict[str, Any]] = []
    none_task_counter = 0

    # ---- Second pass: fill task fields from events in order ----
    # We track "current task context" — the last implementer dispatch seen
    current_impl_task: Optional[int] = None
    current_impl_dispatch_idx: Optional[int] = None

    for ev_idx, ev in enumerate(events):
        etype = ev["event_type"]

        # ----- Implementer dispatch -----
        if etype == "agent_dispatch" and ev["dispatch_type"] == "implementer":
            tn = ev.get("task_number")
            if tn is None:
                # Synthetic task number for unnumbered dispatches
                tn = -1000 - none_task_counter
                none_task_counter += 1
                task_map[tn] = _new_task_record(tn)
                none_tasks.append(task_map[tn])

            current_impl_task = tn
            current_impl_dispatch_idx = ev_idx
            task_map[tn]["dispatch"]["found"] = True
            task_map[tn]["dispatch"]["description_snippet"] = ev["description_snippet"]
            task_map[tn]["dispatch"]["message_index"] = ev["msg_index"]

        # ----- Agent return -----
        elif etype == "agent_return":
            tn_ev = ev.get("task_number")
            dt = ev.get("dispatch_type", "unknown")
            result_text = ev.get("result_text", "")

            if dt == "implementer":
                # Match to task by task_number or fall back to current_impl_task
                tn = (
                    tn_ev
                    if (tn_ev is not None and tn_ev in task_map)
                    else current_impl_task
                )
                if tn is not None and tn in task_map:
                    ret = task_map[tn]["subagent_return"]
                    ret["found"] = True
                    ret["status"] = ev["status"]
                    ret["had_concerns"] = "DONE_WITH_CONCERNS" == ev["status"]
                    ret["had_deviations"] = bool(
                        re.search(r"\bdeviation", result_text, re.IGNORECASE)
                        and not re.search(r"no deviation", result_text, re.IGNORECASE)
                    )
                    ret["message_index"] = ev["msg_index"]

                    # Extract concern snippet if present
                    if ret["had_concerns"]:
                        concern_match = re.search(
                            r"(?:Concerns?|CONCERNS?)[:\s]*(.{10,200})", result_text
                        )
                        ret["concern_text"] = (
                            concern_match.group(1).strip()
                            if concern_match
                            else "(see result)"
                        )
                    else:
                        ret["concern_text"] = None

                    ret["deviation_text"] = None
                    if ret["had_deviations"]:
                        dev_match = re.search(
                            r"(?:Deviations?|DEVIATIONS?)[:\s]*(.{10,200})", result_text
                        )
                        ret["deviation_text"] = (
                            dev_match.group(1).strip() if dev_match else "(see result)"
                        )

            elif dt == "spec_review":
                tn = (
                    tn_ev
                    if (tn_ev is not None and tn_ev in task_map)
                    else current_impl_task
                )
                if tn is not None and tn in task_map:
                    task_map[tn]["reviews"]["spec_compliance"]["result"] = ev.get(
                        "review_result"
                    )
                    task_map[tn]["reviews"]["spec_compliance"]["message_index"] = ev[
                        "msg_index"
                    ]

            elif dt == "code_quality":
                tn = (
                    tn_ev
                    if (tn_ev is not None and tn_ev in task_map)
                    else current_impl_task
                )
                if tn is not None and tn in task_map:
                    task_map[tn]["reviews"]["code_quality"]["result"] = ev.get(
                        "review_result"
                    )
                    task_map[tn]["reviews"]["code_quality"]["message_index"] = ev[
                        "msg_index"
                    ]

        # ----- Review dispatch -----
        elif etype == "agent_dispatch" and ev["dispatch_type"] == "spec_review":
            tn = ev.get("task_number")
            if tn is None:
                tn = current_impl_task
            if tn is not None and tn in task_map:
                task_map[tn]["reviews"]["spec_compliance"]["dispatched"] = True
                task_map[tn]["reviews"]["spec_compliance"]["message_index"] = ev[
                    "msg_index"
                ]

        elif etype == "agent_dispatch" and ev["dispatch_type"] == "code_quality":
            tn = ev.get("task_number")
            if tn is None:
                tn = current_impl_task
            if tn is not None and tn in task_map:
                task_map[tn]["reviews"]["code_quality"]["dispatched"] = True
                task_map[tn]["reviews"]["code_quality"]["message_index"] = ev[
                    "msg_index"
                ]

        # ----- File edits -----
        elif etype == "file_edit":
            fp = ev.get("file_path", "")
            tn = current_impl_task

            # deviations.md update
            if "DEVIATION" in fp.upper() and tn is not None and tn in task_map:
                task_map[tn]["deviations_logged"] = True

            # Plan checkbox update: any edit containing checkbox syntax to a plan file
            # We detect this by looking at the edit's new_string for checkbox patterns
            # (tool input may contain new_string for Edit; for Write we check content)

            # Report file: reports/task-N-...
            if "reports" in fp.lower() and re.search(
                r"task[_\-]?\d+", fp, re.IGNORECASE
            ):
                extracted_tn = _extract_task_number_from_path(fp)
                target_tn = extracted_tn if extracted_tn is not None else tn
                if target_tn is not None and target_tn in task_map:
                    task_map[target_tn]["report_file_exists"] = True

        # ----- Bash runs -----
        elif etype == "bash_run":
            pass  # Handled in scripts_run aggregation separately

    # ---- Check report files on disk if reports_dir provided ----
    if reports_dir and os.path.isdir(reports_dir):
        _verify_report_files(task_map, reports_dir)

    tasks = [task_map[tn] for tn in sorted(task_map.keys()) if tn >= 0]
    # Append unnumbered tasks at the end
    tasks.extend(none_tasks)
    return tasks, skills_invoked


def _new_task_record(task_number: int) -> Dict[str, Any]:
    """Return a fresh task record with all fields defaulted."""
    return {
        "task_number": task_number,
        "task_name": None,
        "dispatch": {
            "found": False,
            "description_snippet": None,
            "message_index": None,
        },
        "subagent_return": {
            "found": False,
            "status": None,
            "had_concerns": False,
            "concern_text": None,
            "had_deviations": False,
            "deviation_text": None,
            "message_index": None,
        },
        "reviews": {
            "spec_compliance": {
                "dispatched": False,
                "result": None,
                "message_index": None,
            },
            "code_quality": {
                "dispatched": False,
                "result": None,
                "message_index": None,
            },
        },
        "deviations_logged": False,
        "report_file_exists": False,
        "plan_checkbox_updated": False,
        "anomalies": [],
    }


def _extract_task_number_from_path(path: str) -> Optional[int]:
    """Try to extract a task number from a file path like reports/task-3-foo.md."""
    m = re.search(r"task[_\-](\d+)", path, re.IGNORECASE)
    return int(m.group(1)) if m else None


def _verify_report_files(task_map: Dict[int, Dict[str, Any]], reports_dir: str) -> None:
    """
    Check the reports directory for task-N-* files and mark tasks accordingly.
    Only updates tasks that haven't already been marked via Edit/Write events.
    """
    pattern = os.path.join(reports_dir, "task*")
    for fpath in glob.glob(pattern):
        tn = _extract_task_number_from_path(os.path.basename(fpath))
        if tn is not None and tn in task_map:
            task_map[tn]["report_file_exists"] = True


# ---------------------------------------------------------------------------
# Phase 3: Aggregate scripts_run
# ---------------------------------------------------------------------------


def aggregate_scripts(events: List[Event]) -> List[Dict[str, Any]]:
    """
    Count runs of each tracked script. Infer phase for controller-checkpoint
    based on position in event stream relative to first implementer dispatch.
    """
    counts: Dict[str, Dict[str, Any]] = {}
    first_impl_idx: Optional[int] = None

    for ev in events:
        if (
            ev["event_type"] == "agent_dispatch"
            and ev["dispatch_type"] == "implementer"
        ):
            if first_impl_idx is None:
                first_impl_idx = ev["msg_index"]
        if ev["event_type"] == "bash_run" and ev.get("tracked_script"):
            script = ev["tracked_script"]
            if script not in counts:
                counts[script] = {"script": script, "count": 0, "phases": []}
            counts[script]["count"] += 1

            if script == "controller-checkpoint":
                phase = (
                    "pre-execution"
                    if (first_impl_idx is None or ev["msg_index"] < first_impl_idx)
                    else "mid-execution"
                )
                counts[script]["phases"].append(phase)

    result = []
    for script, info in sorted(counts.items()):
        entry: Dict[str, Any] = {"script": script, "count": info["count"]}
        if script == "controller-checkpoint" and info["phases"]:
            # Report the predominant phase
            from collections import Counter

            most_common = Counter(info["phases"]).most_common(1)[0][0]
            entry["phase"] = most_common
        result.append(entry)
    return result


# ---------------------------------------------------------------------------
# Phase 4: Anomaly detection
# ---------------------------------------------------------------------------


def detect_anomalies(
    tasks: List[Dict[str, Any]],
    events: List[Event],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Detect anomaly patterns across the event stream.
    Annotates task records with per-task anomalies and returns a summary.
    """
    anomaly_details: List[Dict[str, Any]] = []

    counts = {
        "total_anomalies": 0,
        "reviews_skipped": 0,
        "concerns_not_logged": 0,
        "tasks_without_reports": 0,
        "blocked_retried_unchanged": 0,
        "done_with_concerns_not_routed": 0,
        "plan_checkboxes_not_updated": 0,
    }

    def add_anomaly(task_number: int, atype: str, description: str) -> None:
        anomaly_details.append(
            {
                "task": task_number,
                "type": atype,
                "description": description,
            }
        )
        counts["total_anomalies"] += 1
        if atype in counts:
            counts[atype] += 1
        # Also annotate the task record
        for t in tasks:
            if t["task_number"] == task_number:
                t["anomalies"].append({"type": atype, "description": description})
                break

    # Build ordered list of implementer dispatches (by msg_index) for sequence analysis
    impl_dispatches = [
        ev
        for ev in events
        if ev["event_type"] == "agent_dispatch" and ev["dispatch_type"] == "implementer"
    ]

    # Build a lookup: msg_index -> event index in events list
    event_by_msg: Dict[int, int] = {ev["msg_index"]: i for i, ev in enumerate(events)}

    for task in tasks:
        tn = task["task_number"]
        ret = task["subagent_return"]
        reviews = task["reviews"]

        # ---- Rule 1: reviews_skipped ----
        # Task was dispatched, returned successfully, but spec review was not dispatched.
        if (
            task["dispatch"]["found"]
            and ret["found"]
            and ret["status"] in ("DONE", "DONE_WITH_CONCERNS")
            and not reviews["spec_compliance"]["dispatched"]
        ):
            add_anomaly(
                tn,
                "reviews_skipped",
                f"Task {tn} returned {ret['status']} but no spec compliance review was dispatched.",
            )

        # ---- Rule 2: concerns_not_logged ----
        # DONE_WITH_CONCERNS but no deviations.md edit detected before the next task dispatch.
        if ret["status"] == "DONE_WITH_CONCERNS" and not task["deviations_logged"]:
            add_anomaly(
                tn,
                "concerns_not_logged",
                f"Task {tn} subagent returned DONE_WITH_CONCERNS but no Edit to deviations.md "
                "was detected before the next task dispatch.",
            )

        # ---- Rule 3: tasks_without_reports ----
        # Task returned DONE but no report file found.
        if (
            ret["found"]
            and ret["status"] in ("DONE", "DONE_WITH_CONCERNS")
            and not task["report_file_exists"]
        ):
            add_anomaly(
                tn,
                "tasks_without_reports",
                f"Task {tn} completed ({ret['status']}) but no report file was detected "
                "via Edit/Write events or in the reports directory.",
            )

        # ---- Rule 4: blocked_retried_unchanged ----
        # BLOCKED return followed by another dispatch of the same task number.
        if ret["status"] == "BLOCKED":
            # Look for a subsequent dispatch with the same task number
            subsequent_same = [
                ev
                for ev in events
                if ev["event_type"] == "agent_dispatch"
                and ev["dispatch_type"] == "implementer"
                and ev.get("task_number") == tn
                and ev["msg_index"] > (ret["message_index"] or 0)
            ]
            if subsequent_same:
                add_anomaly(
                    tn,
                    "blocked_retried_unchanged",
                    f"Task {tn} returned BLOCKED and was re-dispatched — verify that additional "
                    "context was provided before the retry.",
                )

        # ---- Rule 5: done_with_concerns_not_routed ----
        # DONE_WITH_CONCERNS followed immediately by spec review with no intermediate
        # controller messages addressing concerns.
        if (
            ret["status"] == "DONE_WITH_CONCERNS"
            and reviews["spec_compliance"]["dispatched"]
        ):
            ret_idx = ret["message_index"] or 0
            review_idx = reviews["spec_compliance"]["message_index"] or 0
            if review_idx > ret_idx:
                # Count non-tool-call messages between them (indicates controller deliberation)
                interstitial = [
                    ev
                    for ev in events
                    if ret_idx < ev["msg_index"] < review_idx
                    and ev["event_type"] not in ("agent_dispatch", "agent_return")
                ]
                if len(interstitial) == 0:
                    add_anomaly(
                        tn,
                        "done_with_concerns_not_routed",
                        f"Task {tn} returned DONE_WITH_CONCERNS but controller dispatched spec "
                        "review immediately without any intermediate concern-handling steps.",
                    )

        # ---- Rule 6: plan_checkboxes_not_updated ----
        # Task completed but no plan checkbox update detected.
        # (Skipped if we have no plan file information — best-effort only.)
        if (
            ret["found"]
            and ret["status"] in ("DONE", "DONE_WITH_CONCERNS")
            and not task["plan_checkbox_updated"]
        ):
            add_anomaly(
                tn,
                "plan_checkboxes_not_updated",
                f"Task {tn} completed but no Edit with checkbox syntax was detected in a plan file.",
            )

    # Update totals
    counts["total_anomalies"] = len(anomaly_details)

    return anomaly_details, counts


# ---------------------------------------------------------------------------
# Phase 5: Detect plan checkbox updates via event stream
# ---------------------------------------------------------------------------


def annotate_plan_checkbox_updates(
    tasks: List[Dict[str, Any]], events: List[Event]
) -> None:
    """
    Walk file_edit events and mark tasks as plan_checkbox_updated if an Edit
    to a plan-like file contains checkbox syntax near or after the task completes.
    """
    plan_file_pattern = re.compile(
        r"(plan|PLAN|task[s_-]|TASK[S_-]|implementation)", re.IGNORECASE
    )

    for ev in events:
        if ev["event_type"] != "file_edit":
            continue
        fp = ev.get("file_path", "")
        if not plan_file_pattern.search(fp):
            continue
        # The Edit tool's input may have new_string; we can't always introspect it
        # without re-reading the raw message. Best effort: just flag that a plan
        # file was edited. The anomaly rule will filter further.
        # We mark all currently-in-progress tasks at this message index.
        for task in tasks:
            ret_idx = task["subagent_return"].get("message_index")
            if ret_idx is not None and ev["msg_index"] >= ret_idx:
                if task["subagent_return"]["status"] in ("DONE", "DONE_WITH_CONCERNS"):
                    task["plan_checkbox_updated"] = True
                    break  # Only mark one task per edit to avoid false positives


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------


def extract_trace(
    session_file: str,
    deviations_file: Optional[str],
    reports_dir: Optional[str],
) -> Dict[str, Any]:
    """
    Full pipeline: load -> event stream -> tasks -> scripts -> anomalies -> output.
    """
    messages = load_messages(session_file)
    events = build_event_stream(messages)
    tasks, skills_invoked = aggregate_tasks(events, reports_dir)

    # Annotate plan checkbox updates before anomaly detection
    annotate_plan_checkbox_updates(tasks, events)

    scripts_run = aggregate_scripts(events)
    anomaly_details, anomaly_summary = detect_anomalies(tasks, events)

    # Cross-reference deviations.md if provided
    if deviations_file and os.path.isfile(deviations_file):
        _cross_reference_deviations(tasks, deviations_file)

    return {
        "session_file": os.path.abspath(session_file),
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "total_messages": len(messages),
        "skills_invoked": skills_invoked,
        "scripts_run": scripts_run,
        "tasks": tasks,
        "anomaly_summary": anomaly_summary,
        "anomaly_details": anomaly_details,
    }


def _cross_reference_deviations(
    tasks: List[Dict[str, Any]], deviations_file: str
) -> None:
    """
    Read deviations.md and mark tasks as deviations_logged if their task number
    appears in the file content.
    """
    try:
        with open(deviations_file, "r", encoding="utf-8") as fh:
            content = fh.read()
        for task in tasks:
            tn = task["task_number"]
            if re.search(rf"\b[Tt]ask\s*{tn}\b", content):
                task["deviations_logged"] = True
    except OSError:
        pass  # Non-fatal — file may not exist yet


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Extract a structured execution trace from a Claude Code .jsonl session file. "
            "Identifies subagent dispatches, reviews, status reports, and anomalies."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python extract-execution-trace.py --session-file session.jsonl\n"
            "  python extract-execution-trace.py --session-file session.jsonl \\\n"
            "      --output trace.json --reports-dir reports/\n"
        ),
    )
    parser.add_argument(
        "--session-file",
        required=True,
        metavar="PATH",
        help="Path to the Claude Code .jsonl session file.",
    )
    parser.add_argument(
        "--output",
        default=None,
        metavar="PATH",
        help="Write JSON output to this file (default: stdout).",
    )
    parser.add_argument(
        "--deviations-file",
        default=None,
        metavar="PATH",
        help="Optional deviations.md path for cross-reference.",
    )
    parser.add_argument(
        "--reports-dir",
        default=None,
        metavar="PATH",
        help="Optional reports directory to verify report files exist.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not os.path.isfile(args.session_file):
        print(
            f"Error: session file not found: {args.session_file}",
            file=sys.stderr,
        )
        return 1

    try:
        trace = extract_trace(
            session_file=args.session_file,
            deviations_file=args.deviations_file,
            reports_dir=args.reports_dir,
        )
    except Exception as exc:
        print(f"Error extracting trace: {exc}", file=sys.stderr)
        return 1

    output_json = json.dumps(trace, indent=2)

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as fh:
                fh.write(output_json)
                fh.write("\n")
            print(f"Trace written to {args.output}", file=sys.stderr)
        except OSError as exc:
            print(f"Error writing output file: {exc}", file=sys.stderr)
            return 1
    else:
        print(output_json)

    return 0


if __name__ == "__main__":
    sys.exit(main())
