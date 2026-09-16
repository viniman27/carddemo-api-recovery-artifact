# Stage7 Counterexample Review — Adapter Behavior CardDemo

## Recommendation

Approve only as an unapproved documentary Stage7 requirements draft pending human review. Do not authorize implementation from it until binding/acquisition evidence is produced for G-25/G-26/G-29 and runtime obligations G-27/G-28/G-30 are resolved or explicitly carried.

## Findings

### HOW obtains legitimate observations

- Result: PASS as documentary; BLOCK for implementation
- Finding: Stage7 requires originating invocation/context, channel/resource, occurrence sequence and field mapping; all acquisitions are explicitly undemonstrated (G-25/G-26).

### invented telemetry/source counters

- Result: PASS
- Finding: It rejects source counters as runtime telemetry and forbids reconstructing outputs/counts from arrays/statements.

### resource identity/isolation/stale output

- Result: PASS with blocker
- Finding: State table says actual instance/lifetime/isolation/reset unavailable; OUTPUT open/local initialization not reset evidence (G-29).

### external input responsibility/no provisioning API

- Result: PASS
- Finding: Requests are empty closed objects; external setup actor/mechanism unresolved; no selectors/provisioning/readiness introduced.

### empty vs unavailable/no-output vs zero quantity

- Result: PASS
- Finding: Positive empty observation is required; unavailable omits items; zero rate/missing disclosure/zero quantity distinct.

### failure precedence/no-effects claims

- Result: PASS
- Finding: Known failure precedence over 200/503 retained; zero progress is not no-effects/durability/completion.

### EOF/last-account/report order/multiplicity

- Result: PASS with residual G-30
- Finding: Interest no final flush; reporting mixed record order/multiplicity and EOF uncertainty preserved; no repaired totals.

### 109 rejection separation

- Result: PASS
- Finding: Internal reason 109 is not preliminary rejection, reject count, public diagnostic or special HTTP mapping.

### numeric/date conversion domains

- Result: PARTIAL / runtime obligation
- Finding: Spec says no invented conversion and faithful conversion limits remain G-27; concrete parsers/domains are not executed here.

### OpenAPI validation

- Result: NOT CLAIMED
- Finding: No full OpenAPI artifact was inspected or validated in this task; Stage7 is Markdown requirements only.

## Traceability and scope audit

- Tracks present: {'posting': True, 'interest': True, 'reporting': True}.
- Stage6 clauses C-1..C-14 present: True ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]).
- Semantic rules R-1..R-20 mapped: True.
- Source anchors checked: 38; bad anchors: [].
- No full OpenAPI validation was claimed or performed.

## Blockers vs obligations

- G-25 — self-declared design blocker before implementation: no demonstrated invocation/resource binding, external input-instance association, setup owner, or mechanism for all three tracks
- G-26 — self-declared design blocker before implementation: no exercised acquisition channel, occurrence attribution, order/multiplicity evidence, or positive-empty observation mechanism
- G-27 — residual runtime obligation: field-level faithful conversion for required contract values remains to be demonstrated against actual observations
- G-28 — residual runtime obligation: technical failure detection/classification and partial-content retention mechanisms remain unimplemented
- G-29 — self-declared design blocker before implementation: no reset/isolation/durability/restart/safe-repetition evidence; resource identity is documentary only
- G-30 — residual runtime obligation/reporting-specific blocker for completion claims: reporting EOF/date/job-flow/final numeric output remain unresolved; no complete-empty-report claim
