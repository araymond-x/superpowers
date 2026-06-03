"""N4: controller-checkpoint.py find_report_file/find_all_report_files recurse into archive-*/.
Run: .venv/bin/python3 -m pytest tests/unit/test_checkpoint_archive_aware.py -v
"""
import importlib.util
import os

_SPEC = importlib.util.spec_from_file_location(
    "controller_checkpoint",
    os.path.join(os.path.dirname(__file__), "..", "..",
                 "skills", "subagent-driven-development", "scripts", "controller-checkpoint.py"),
)
cc = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(cc)


def _impl(p):
    p.write_text("x" * 80)


def test_find_report_file_in_archive(tmp_path):
    reports = tmp_path / "reports"; reports.mkdir()
    arch = reports / "archive-Core"; arch.mkdir()
    _impl(arch / "task-000-implementer-report.md")
    assert cc.find_report_file(str(reports), 0).endswith("archive-Core/task-000-implementer-report.md")


def test_find_report_file_prefers_live_over_archive(tmp_path):
    reports = tmp_path / "reports"; reports.mkdir()
    arch = reports / "archive-Core"; arch.mkdir()
    _impl(arch / "task-000-implementer-report.md")
    _impl(reports / "task-000-implementer-report.md")
    # Live copy must win (sorts last).
    assert cc.find_report_file(str(reports), 0) == str(reports / "task-000-implementer-report.md")


def test_find_all_report_files_includes_archive(tmp_path):
    reports = tmp_path / "reports"; reports.mkdir()
    arch = reports / "archive-Core"; arch.mkdir()
    _impl(arch / "task-000-implementer-report.md")
    _impl(reports / "task-002-implementer-report.md")
    found = cc.find_all_report_files(str(reports))
    bases = sorted(os.path.basename(f) for f in found)
    assert bases == ["task-000-implementer-report.md", "task-002-implementer-report.md"]


def test_detect_stale_artifacts_stays_flat(tmp_path):
    # Regression: archived reports must NOT trip the pre-execution stale scan.
    reports = tmp_path / "reports"; reports.mkdir()
    arch = reports / "archive-Core"; arch.mkdir()
    _impl(arch / "task-000-implementer-report.md")
    dev = tmp_path / "deviations.md"; dev.write_text("")  # empty = no content
    result = cc.detect_stale_artifacts(str(dev), str(reports))
    assert result["status"] == "OK", result
