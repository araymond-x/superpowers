# Dispatch Markers (provenance attribution)

The pre-dispatch hook attributes review-driven fix cycles to the dispatch log
when you prefix the Agent dispatch **description** with a marker:

| Marker | Hook behavior | Log line |
|--------|---------------|----------|
| `[task N fix]` | Implementer enforcement path (no gate relaxation); logs the fix WITHOUT a `type=implementer` line | `<ISO> DISPATCH fix task=N type=fix` |
| `[task N re-review:{spec\|quality\|partner}]` | Reviewer passthrough | `<ISO> DISPATCH reviewer task=N type={spec\|quality\|partner}-review` |

Check 9 (git-reality) opens a verification window only on `type=implementer`
lines, so a `[task N fix]` must NOT log `type=implementer` (it would move task
N's window). A markerless dispatch matching `\bfix\b|remediat` is recorded as
`DISPATCH adhoc type=fix-unattributed` (tamper-evidence) but is not attributed.
