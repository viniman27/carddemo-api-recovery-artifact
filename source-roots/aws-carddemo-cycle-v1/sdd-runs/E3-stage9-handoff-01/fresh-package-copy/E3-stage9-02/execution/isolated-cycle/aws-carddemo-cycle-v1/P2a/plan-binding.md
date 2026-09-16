# P2a plan-binding — documentary binding plan only

Scope: derive binding duties from Stage 7 r2 for all three tracks without implementing, executing, compiling COBOL, reading support expected outputs, or asserting runtime behavior.

## Common duties

- INV: associate run `E3-01`, capability `unselected-stage-1-scope-only`, called operation, request-shape evidence, source/runtime binding reference, resource links, observation scope, capture channels, and response association. Internal invocation identity is not a receipt or idempotency key.
- RES: record actual resource instance identity or unresolved status, owner, origin/version, validity window, prerequisites, reuse/shared-state attribution, and missing dependencies. Never infer readiness from an empty request.
- CAP: record attributable observations, raw evidence/digest when available, capture scope/freshness/framing, represented positions, empty-observation basis, exclusions, uncertainty and destination. Zero-byte evidence is not automatically positive empty.
- CONV: for every represented field, record source span/path/pin/line, declaration, encoding/sign/framing basis, observed padding/width, mapped value, loss, and unresolved conflicts. No regex/range/rounding/calendar/coercion defaults.
- FAIL: record actual event/diagnostic, invocation attribution, meaning authority, known/unestablished boundary, retained observations, and selected existing category. Internal 109 is not public failure.
- STATE: distinguish local versus persistent resources, preparation/reuse evidence, attempted/observed/durable effects, reset/isolation evidence and repetition limits. No reset/durability/retry promise.
- RESP: bind contract version, INV, CAP/CONV/FAIL/STATE disposition, exact envelope/error fields, status rationale, occurrence-to-array index mapping, and unresolved gaps.

## Track duties

### posting
- INV/RES: bind daily candidate sequence and posting transaction/reject/xref/account/category resources; HTTP `{}` is only request representation.
- CAP: separate transaction, rejection, and progress observations; justify ordered arrays and duplicates per channel.
- CONV: map `PostingTransaction`, `PostingRejection.candidate`, `reason` enum 100-103 only, `description`, and progress counts from actual attributable sources.
- FAIL/RESP: 200 if outputs/rejections/progress available absent known failure; progress-only 200 remains progress only; all unavailable with no known failure is 503; known failure is 500 with optional availableContent.
- STATE: no account/category/output durability, rollback, or repetition guarantee; reason 109 remains internal.

### interest
- INV/RES: bind category sequence, identifier parameter, account/xref/disclosure/generated-output resources; do not use job literal as default.
- CAP: generated output only from actual generated transaction observations, including positive empty observation where justified.
- CONV: map generated transaction fields; preserve zero/negative quantities when observed; no fee/suffix/fallback public field.
- FAIL/RESP: available outputs including `items: []` supports 200 absent known failure; unavailable/no failure is 503; known failure is 500.
- STATE: no final flush insertion, no account-update receipt, no suffix uniqueness or repeat-safety claim.

### reporting
- INV/RES: bind transaction sequence, separate date resource, upstream selection provenance, lookup and report resources independently.
- CAP: acquire mixed report output; identify header/detail/total occurrences and excluded presentation mechanics without collapsing order/multiplicity.
- CONV: map receiver fields exactly as observed; do not restore descriptions, totals, dates, ranges, or arithmetic.
- FAIL/RESP: available records including empty observed sequence supports 200 absent known failure; unavailable/no failure is 503; known failure preserves available earlier content under 500.
- STATE: no complete empty report, full-range processing, reconciled totals, final account total, EOF storage, or executed job-flow claim.

## Still-pending deployment choices (not implemented here)

1. Adapter topology: per-call CLI wrapper, server facade, or offline harness.
2. Actual resource provisioning policy, legal data origin, encoding/framing/sign decoding, and file-instance identity.
3. Invocation isolation: new directories/resources per call versus controlled stateful sequence.
4. Capture channels and freshness/digest mechanisms for indexed, sequential, progress/display, and report outputs.
5. Failure-event taxonomy sufficient for known-failure boundary without exposing file status/internal telemetry.
6. Positive-empty evidence rule per channel, distinct from zero-byte/stale/truncated/failed capture.
7. Reset/isolation/durability evidence standard before any runtime claim.
8. Smoke fixtures allowed for development versus official T1/T2/T3/T4 oracle separation.
9. Minimum COBOL reach evidence per operation before operational claims.
10. Human gate for P2/P3 before implementation, COBOL execution, official cells, or E1/E2 comparison.
