# Task 11 Fix — Round-2 Focused Quality Re-Review

Scope: verify the `[task 11 fix]` (`c93f89d..532c7b6`) closes round-1 finding #1 (generalized ordering canonicalization), the two new tests are non-vacuous, the migrated third test keeps its invariants, and no new defects. Round-1 central question (test vacuity from default-on post-spawn) and findings #2/#3 are out of scope and not re-touched.

### Strengths

- **The landed code matches the amended Step 2 fence byte-for-byte** (`spawn-handoff-session.sh:905-911` vs `module-3-spawn-script.md` Task 11 fence). Comment block accurately records the round-1 measurement, the AC it violated, and the `{rename, rc}`-universe rationale.
- **The canonicalization is provably complete over the whole accepted-input universe.** The knob regex `^(rename|rc)(,(rename|rc))*$` (`:67`) admits exactly 8 forms; all 8 reasoned through against `[[ ",$POST_SPAWN," == *,rename,* ]]` / `*,rc,*` + `${canon:+$canon,}rc`:

  | input | canon | warn? | /rc last? |
  |---|---|---|---|
  | `rename` | `rename` | no | n/a (no rc) |
  | `rc` | `rc` | no | yes |
  | `rename,rc` | `rename,rc` | no | yes |
  | `rc,rename` | `rename,rc` | yes | yes |
  | `rename,rename` | `rename` | yes | n/a |
  | `rc,rc` | `rc` | yes | yes |
  | `rename,rc,rename` | `rename,rc` | yes | yes |
  | `rc,rename,rc` | `rename,rc` | yes | yes |

  `/rc` is last whenever present, duplicates collapse, and the warning fires **iff** `canon != input`, naming the actual `$POST_SPAWN` and `$canon` (not a hardcoded pair). The `case` loop (`:914-918`) consumes the *canonicalized* value, so `/rc`-last is genuinely guaranteed, not merely reordered in a string.
- **The two new tests are NON-VACUOUS (independently mutation-verified).** Reverted the block to the pre-fix single-literal form and ran the two tests scoped:
  - `test_knob_multitoken_forces_rc_last` (`rename,rc,rename`) → **RED**: `assert 4 == 3` — the mutant logged `send /rename`, `send /rc`, `send /rename` (a `/rename` after `/rc`, the exact AC violation).
  - `test_knob_duplicate_token_deduped` (`rename,rename`) → **RED**: `assert 3 == 2` — the mutant sent `/rename` twice.
  - Restored by file-copy; `diff -q` reported identical and `git diff --stat` clean.
- **Tests exercise real behavior** — assertions read the actual logged `cmux send` call lines (`_send_lines`), not mocks/stubbed returns.

### Issues

#### Critical — none
#### Important — none
#### Minor — none

Verified against each round-2 checklist item:
- **#3 (migrated third test keeps invariants):** `test_knob_order_rc_before_rename_is_reordered_with_warning` (`:1822-1838`) still pins `returncode==0`, `"post_spawn" not in _outcome` (no field on success), `send_lines[1]==/rename` and `send_lines[2]==/rc` (ordering), and the input in stderr. Only the warning substring migrated (`reordering to rename,rc` → `canonicalized to rename,rc (`). Not a deleted test wearing its name.
- **#4 (no new defects):** No unreachable arm introduced. Bash-3.2-safe: `[[ == *glob* ]]` and `${x:+..}` are both 3.2 constructs; LHS is quoted (`",$POST_SPAWN,"`) so no glob-injection, and `$POST_SPAWN` is post-validation so contains only `{rename, rc}` + commas. No `set -u/-e/pipefail` added; no producer piped into `grep -q`. The new WARNING is a plain `echo` interpolating only post-validation tokens — no terminal-control mangling possible.
- **Warning-anchoring nit (already handled):** the `532c7b6` follow-up correctly appends `(` to the `canonicalized to rename,rc (` assertions so the `rename,rc` result string cannot match inside the `rename,rc,rename` *input* substring. Good defensive discipline; no action needed.

### Recommendations

None. The fix is minimal, correct, and its tests fail for the right reason.

### Assessment

**Ready to merge?** Yes.

**Reasoning:** The generalized canonicalization closes finding #1 completely — `/rc`-last holds for all 8 accepted inputs with dedupe and an accurate input→result warning — and both new tests are empirically non-vacuous (revert → RED, restore → identical). Full unit suite re-measured at **805 passed, 0 failed** (398.56s), exactly the 803 baseline + 2 new tests. No new defects; Contract Constraints (bash ≥3.2, no `set -u/-e/pipefail`, no SIGPIPE fail-open) honored.

`git status` confirms the tree is as found: only the pre-existing uncommitted controller artifacts under `docs/imp-plans/2026-07-30-cmux-spawn-v2/` — no stray mutation of the script or test file.
