# Adversarial Quality Re-Review (round 4) — Task 3 — **APPROVED**

**Reviewing:** fix commits `7437343` + `07ef5e0` (`git diff 00f54bb..HEAD -- docs/process-improvement-findings/`)
**Model:** opus
**Verdict:** **APPROVED** — round-3 IMPORTANT 1 and 2 both **CLOSED**; the two defects fix round 3 self-caught were repaired correctly. Four non-blocking observations, explicitly **not** grounds for a fourth fix round.

**Review trajectory:** 2 BLOCKING → 1 BLOCKING → 0 BLOCKING/2 IMPORTANT → **APPROVED**. Converged.

---

## Closure

| Round-3 finding | Verdict | Evidence run |
|---|---|---|
| **IMPORTANT 1** — axis contradiction; N81 carried the wrong side | **CLOSED** | Own **whitespace-normalized** sweep of both files (`tr '\n' ' ' \| tr -s ' '` then `/usr/bin/grep -oiE`), pattern positive-controlled against a known-present phrase first. 20 hits; **all four cross-product cells checked at every site.** Zero sites state anything false for any cell. |
| **IMPORTANT 2** — third flat lookup omitted | **CLOSED** | Section re-titled and re-counted; Check 4's globs added as the *first* bullet, to §Candidate A's must-skip list, and to N81's flat enumeration; the "Check 4c is the exception" sentence replaced and qualified. Underlying claims **verified at source, independently of round 3's fixture**. |

### The cross-product, with every asserting site verified

| cell | correct count | verified sites |
|---|---|---|
| interior + headered | **3** | SP4 §Placement interior bullet; §fork; §WCNBE placement bullet; N81 placement sentence |
| interior + manifest-only | **2** | §Placement interior bullet ("two when it is manifest-only"); §WCNBE placement + plan-shape bullets; N81 placement sentence |
| last-in-range + headered | **2** | §Placement last-in-range bullet ("*in the headered shape*"); §WCNBE; N81 |
| last-in-range + manifest-only | **1** | §Placement; §"Placement also interacts…"; §fork; §WCNBE ×2; N81 ×2 |
| range across cells | **1–3** | §WCNBE always-used bullet; N81 §Cost fork |

The **paired last-in-range bullets** fix round 3 conditioned on its own initiative are correct and did **not** over-reach. The fifth site the dispatch missed (N81's "caught by the latter alone") now reads "…**ONLY when it is also LAST-IN-RANGE**".

Three residual hits are **category claims, not per-cell counts**, and are correct as written (`Three gates bite` / `THREE gates bind` as enumeration headers, each followed by its three bullets; "rather than only the two terminal gates" naming a category in a prescription). The reviewer agreed with fix round 3's decision not to churn them. The four-column table's `applies when` column independently encodes the same cross-product, so table and prose agree.

### IMPORTANT 2 verified at source, by a second method

Round 3 proved this by hook fixture (X/Y/Z); fix round 3 by construct; round 4 re-derived it by construct **independently**. Two methods agreeing is the closure argument.

- `task_report_glob` body is literally `echo "${REPORTS_DIR}/task-${padded}-${report_type}*"` — **no `archive-*` term**.
- `IMPL_GLOB`, `SPEC_GLOB`, `QUAL_GLOB` all route through it.
- `/usr/bin/grep -n 'archive-'` over the hook → **exactly 2** (a comment + `T0_GLOB`), so "exactly one archive-aware lookup" survives the edit.
- Check 4's N-1 sub-block skips on `[ "$TASK_NUMBER" -eq "$MANIFEST_TASK_START" ]`; Check 4c on `[ "$PREV" -lt "$MANIFEST_TASK_START" ]`.
- `PREV=$((TASK_NUMBER - 1))` and the range guard precedes Check 4, so on the reachable domain `PREV < START ⟺ TASK_NUMBER = START`. **The equivalence claim is arithmetically exact.**
- The repaired must-skip sentence **parses correctly** — three coordinated verbs, one appositive list, "which fire first" attaching to Check 4's globs, the true referent.
- The **"lookup SITES" unit fix is coherent**: three gates, with three globs inside site 1; the word *sites* is what makes 3 correct.

The reviewer also verified the two keys the whole cross-product rests on — `all_tasks_have_reports` → `TASK_HEADER_PATTERN.findall(_unfenced_content(...))` (header-keyed) vs `validate_module_completion` → `for task_id in module.task_ids:` (manifest-keyed) — and that `get_task_type` reads plan **frontmatter**, defaulting to `implementation`, which is the structural reason interior+manifest-only is 2 and not 1.

**Checked for a fourth catcher** that would break the "one to three" range: `all_reports_complete` (iterates `find_all_report_files`; an unused slot contributes nothing), `all_checkboxes_checked` and Check 8 are header/plan-keyed. **None catches a manifest-only unused slot.** The enumeration of three is right.

---

## Non-blocking observations

**1. [MINOR — method, not claim] The instrument that proved "all three" could not have found a fourth.** Fix round 3 verified with `grep -nE '(IMPL_GLOB|SPEC_GLOB|QUAL_GLOB)=\$\(task_report_glob'` → "exactly the three." A **bare** `/usr/bin/grep -n 'task_report_glob'` returns **four** call sites — the three plus `QUAL_GLOB_MIN=$(task_report_glob "$PREV" "quality-review-minimum-tier")` inside Check 4c, also an N-1 lookup, also flat, also archive-blind. *A regex anchored on the variable names it expected cannot discover a name it did not expect.*

**The doc's claim survives** — it consistently scopes "Check 4's N-1 file-existence lookups" as distinct from Check 4c, and under Candidate A `QUAL_GLOB_MIN` is unreachable (4c skips on `PREV -lt START`), so nothing a designer must skip was omitted. **But this is failure mode 4 in its purest form, occurring inside the verification step that was closing a failure-mode-4 finding**, and it landed on an out-of-scope site by luck rather than design. Recorded as the round's durable lesson.

**2. [observation]** "three file-existence errors" is one unstated condition short of unconditional — `SPEC_GLOB`/`QUAL_GLOB` sit inside the `[ "$PREV_TASK_TYPE" = "verification" ]` else-branch, so for a verification predecessor only the implementer-report error fires. Immaterial to the prescription.

**3. [cosmetic]** Number disagreement introduced by `07ef5e0`: "Check 4's globs **are the one** a designer will miss."

**4. [cosmetic]** Directional cross-reference wobble — an interior bullet says "(below)" ~10 lines above a passage saying "above" about the same axis. Both resolve; different referents.

The reviewer deliberately did **not** file "the two skip conditions diverge only under Candidate A" as a finding: the sentence's subject is the two keyings, over which it is exact.

---

## What held up

**N81's density — measured, not judged.** Its description cell is **1036 words**; across all 104 ledger rows it is the **4th longest**, behind N56 (1082), N68 (1066) and N79 (1054), median **115**. It sits at the top of an established tier written by the same convention, not as an outlier. Read cold end to end: every claim resolves, no count is a bare number over a live artifact, and the three bold-caps "THREE" enumerations are each locally disambiguated. **No readability finding** — fix round 3's Concern 4 was accurately calibrated, not an understatement.

**Byte-identity, positive-controlled first** (appended one byte → `cmp` rc=1): live **IDENTICAL, 7295 bytes**, matching the controller's post-commit figure exactly.

**No regressions.** Zero `:NNN` citations in SP4 or N81 (pattern positive-controlled: 4 hits on `CLAUDE.md`). No `handoff-spawn.log` conflation. BACKLOG header/N80/N81 all `NF=9` (control: a mangled row → NF=5). SP4 pipe-lines 13×NF=5, 10×NF=6, 1×NF=9. BACKLOG numstat `00f54bb..HEAD` = **1/1**, only N81 changed; N54/N57 untouched. `verify-symlink-install.sh` → **104/0/0**.

**Every printed command ran as printed.** `grep -c 'type=fix'` live → **10** (9 at round 3, 8 at `00f54bb`, **7 at `0e4b420`** — the revision anchor checks out), so "7 at `0e4b420`, grown at each fix round since" is true across 7→8→9→10 and **the refusal to write a live number is vindicated a fourth time**. Anchored `grep -cE '^\| 0→'` → **4**; bare → **7** (up from 6) — anchoring vindicated again. SP4's two "grep that phrase" promises both resolve (negative control → 0); promise 1 now returns 2 hits because round 3's own commit added a row quoting it — **the self-invalidating-count thesis demonstrating itself once more**, not a defect, since the promise is "grep that phrase", not a count.

**What the reviewer attacked that held.** Expected the paired last-in-range conditioning to over-reach (the classic shape of a fix that strengthens one path and breaks another) — both members are exact. Expected a fourth catching gate to falsify "one to three" — checked three candidates at source, none catches a manifest-only unused slot. Expected the "three gates"/"three sites" collision to be a real unit error — the deliberate *sites* wording makes both correct. Expected the equivalence claim to be loose — it is arithmetically exact.

## What could not be established

- **Round 3's hook fixture (X/Y/Z) and the `all_tasks_have_reports` fixture were not rebuilt.** Round 4's verification of IMPORTANT 2 is by construct — decisive for the glob and the `-eq`/`-lt` arithmetic, but not an independent reproduction of the runtime results, which remain single-sourced from round 3 for the runtime half. Fix round 3's Concern 3 states this honestly.
- **`validate-plan.py` → `blockers: []` on a reserved-slot plan** — three prior measurements with a negative control agree; not rebuilt.
- **Whether a stale `type=implementer` row has perturbed a live Check 9 window** — mechanism proven, incidence unmeasured; the doc says so.
