# Controller Health Checkpoints

The controller runs a deterministic checkpoint script at three critical moments. These are not optional — they replace self-assessment with mechanical verification.

**Before execution begins** (after Plan Ingestion):
```bash
python ~/.claude/skills/superpowers/subagent-driven-development/scripts/controller-checkpoint.py --phase pre-execution --manifest <feature-dir>/.sdd-session.json --deviations-file <feature-dir>/deviations.md --reports-dir <feature-dir>/reports
```
Verify: plan readable, `<feature-dir>/deviations.md` exists, `<feature-dir>/reports/` exists, Task 0 present if needed. If FAIL, fix before proceeding.

**Before each task dispatch** — the pre-dispatch hook enforces this automatically (Check 5c needs the checkpoint, Check 6b a context summary past the midpoint); running it first is optional:
```bash
python ~/.claude/skills/superpowers/subagent-driven-development/scripts/controller-checkpoint.py --phase pre-dispatch --task-number N --manifest <feature-dir>/.sdd-session.json --deviations-file <feature-dir>/deviations.md --reports-dir <feature-dir>/reports
```
Verify: previous task complete, report filed.

**Before declaring completion**:
```bash
python ~/.claude/skills/superpowers/subagent-driven-development/scripts/controller-checkpoint.py --phase pre-completion --manifest <feature-dir>/.sdd-session.json --deviations-file <feature-dir>/deviations.md --reports-dir <feature-dir>/reports
```
Verify: all checkboxes, all reports, no pending deviations. This is the mechanical equivalent of the Pre-Completion Gate — the script checks what the Gate describes.
