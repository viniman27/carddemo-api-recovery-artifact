# Capability Semantics Specification

## Purpose

This Stage 4 specification derives source-grounded, conditional capability semantics for the AWS CardDemo public cycle in run `E3-01` from approved Stage 3-r2 documentary evidence.

**Posting, interest transaction generation, and transaction reporting are mandatory, separately traceable tracks.** Their inclusion does not establish a single combined business capability, a required cross-job schedule, or an executed cycle.

| Attribute | Value |
|---|---|
| Run ID | `E3-01` |
| Stage | `4` |
| Feature | `capability-semantics-carddemo` |
| Artifact | `specs/capability-semantics-carddemo/requirements.md` |
| Immutable operational chain identity | `unselected-stage-1-scope-only` |
| Mandatory tracks | `posting`, `interest`, `reporting` |
| Status | Draft for external human review |
| Human approval | `false` |
| Completeness gate passed | `false` |
| Ready for implementation | `false` |

The semantic statements below characterize the supplied legacy paths, not idealized accounting policy or desired replacement behavior. Assignment, accumulation, and write attempts are distinguished from durable outcomes.

This response supplies specification text only. It does not persist an artifact, modify metadata, approve a gate, or certify transport configuration.

## Semantic Integrity Discipline

- Every semantic claim cites its evidence (`E-n`) or is labeled as inference with rationale.
- Rules are named and numbered (`R-n`); downstream artifacts reference rules, not prose.
- Ambiguities are disposed explicitly, never absorbed silently into clean rules.
- No interface, transport, or implementation vocabulary in this artifact.
- Rule documentation is not a reimplementation mandate: rules documented here support boundary derivation, contract derivation, and test design (including test data setup); at runtime they remain enforced by the legacy core through the wrapper (`rules/legacy-code-policy.md`).

The preceding generic discipline is preserved verbatim from the supplied template. Its framework references are not application findings or authorization for additional work.

### Evidence and rule conventions

- `E-n` resolves to `E3-01/E-n` in approved `legacy-evidence-carddemo-r2`. Its defining entry supplies the full corpus-relative source path, original-file hash, and numbered line ranges.
- `R-1` through `R-20` are globally unique semantic rule definitions in this artifact, qualified by this run and operational chain identity.
- Every rule is an **evidence-grounded semantic interpretation**. Explicit static deductions retain their stated control-flow assumptions.
- “Accepted outcome” identifies the selected or satisfied source path, not human acceptance or guaranteed durable completion.
- “Rejected outcome” identifies a source rejection or alternative where one exists. A non-applicable outcome is explained rather than invented.
- No rule establishes a complete failure taxonomy, atomicity, safe repetition, or dependency closure.

## Section 1: Upstream Authority and Entry Condition

### 1.1 Upstream Authorities and Scope Inheritance

This specification derives from the approved Pipeline Scope Specification, revised Capability Selection Specification, and revised Legacy Evidence Specification.

| Authority, relative to `RUN_ROOT` | Supplied SHA-256 |
|---|---|
| `specs/pipeline-scope-carddemo/requirements.md` | `1362fab5d55b77ef6121328606ae974295cd5723849520e9a246f4bd45e64cc9` |
| `specs/capability-selection-carddemo-r2/requirements.md` | `abdb59180f379d9e14eb86dfa1d8226ec50c981346767e808fd382eb7462bbc4` |
| `specs/legacy-evidence-carddemo-r2/requirements.md` | `4566786600b60e9377c1e369e67765098d06b0153ba973361d2065614a6c9b7b` |
| `specs/legacy-evidence-carddemo-r2/spec.json` | `d34866601d0156c103dc850148e32748da75c0134dbb6b6f6d4b58324a7d61a7` |
| `reviews/stage-1-authorization.json` | `0ec9d89962c088507775523f266816b5c3c13f7631c7a6409b45bc13352542da` |
| `reviews/stage-2-r2-authorization.json` | `22294af2fb12235297e57e4b084a729695864af895d4047eb4a630d7286ec1c9` |
| `reviews/stage-3-r2-authorization.json` | `d8cdf343b5ed63cdd2e83e1627a50673acdb34930ae0c63e29be0e8fb122941e` |

The supplied Stage 3-r2 authorization records:

> Approve stage 3 revision 2 documentary evidence and authorize stage 4 capability semantics for posting, interest, reporting only. No stage 5 approval.

Its residual uncertainty disposition states:

> Carry runtime persistence, EOF buffer contents, missing configuration/external routines as unresolved constraints. Acceptance permits source-grounded conditional semantics, not invented runtime outcomes or blanket ambiguity closure.

The supplied approved metadata establishes subsequent upstream approval without rewriting historical draft-era statuses in the upstream documents. The supplied gate-check report is `current`; it is not a check performed by this response or a new approval.

The inherited entry basis is approval of the concrete Stage 3-r2 evidence version and explicit permission for conditional semantics across all three tracks.

### 1.2 Inherited Constraints

The generic exclusion policy from `settings/rules/run-integrity.md` is preserved verbatim:

> Support, synthetic fixtures, expected outcomes, prior specs/APIs and preparation reports are excluded from extraction by default. An approved exception is an exposure, not independent discovery. Record who already saw evaluation material, including an executor's conversation context; start a clean execution context when required by the protocol. A manifest does not erase prior exposure.

The authorized upstream specifications are used under the explicit stage authorization. References within them to excluded materials do not authorize access to those materials.

Additional binding limits:

- The operational chain identity remains unchanged; track labels do not replace it.
- Only the supplied approved upstream material, authorizations, generic v3 instructions, and allowlisted corpus text inform this artifact.
- The 19-file allowlist is not the full application or proven dependency closure.
- No source modification, compilation, execution, external retrieval, or corpus expansion occurs.
- Runtime persistence, failed-read storage, external routines, missing configuration, and intended policy remain unresolved where evidence does not establish them.
- Shared declarations and matching dataset literals do not establish shared deployed resource identity.
- No canonical data definitions, interface decisions, later-stage specifications, or measured outcomes are produced.

### 1.3 Version and Representation Basis

The governing template is `settings/templates/pipeline/capability-semantics-spec.md`, SHA-256 `6916270efc734a6f56e3a330bc0c8e431991628a749c47ede9c2e10188e30f8b`.

The source package pin is SHA-256 `63ba5c47ecb21349549744b912af3b150654e7e435724dba499e3c88369f15a2`. The supplied `input_pins.source_bodies` identifies each original corpus file separately from its derived numbered representation.

Source references use the supplied stable, 1-based numbered text. Original-file hashes and derived-representation hashes are not interchangeable. No checksum was recomputed, and no deployed encoding or filesystem integrity claim follows.

## Section 2: Operation Semantic Model

### 2.1 Posting

| Element | Source-grounded meaning |
|---|---|
| Purpose | Process daily transaction records through preliminary rejection selection or posting attempts; the header provides orientation, while statements establish behavior. E-1, E-7–E-10 |
| Inputs | A daily transaction, card-to-account lookup information, account comparison/balance fields, and account/type/category balance information. E-4, E-8, E-20–E-22, E-27 |
| Preconditions | The relevant opens and reads must permit control to reach the described path. A non-EOF record is required for per-record processing. Account lookup is guarded by reason zero after card lookup. E-7, E-8, E-11 |
| Behavior | Reset per-record reason; perform guarded lookups and ordered comparisons; select posting or reject writing before posting begins. Posting constructs a transaction and attempts category, account, then transaction operations. R-1–R-6 |
| Conditional postconditions | On the reject path, the reject counter is incremented and a daily-record-plus-trailer write is attempted. On the posting path, local balance arithmetic and ordered write/rewrite attempts occur. These are not durable-state guarantees. E-7, E-9, E-10 |
| Outputs | Transaction-write attempts, reject-write attempts, displayed counts, and conditional assignment of return code 4 after closes when the reject count is positive. E-7, E-9–E-11 |
| Side effects | Account and category-balance modification attempts; output-file opens and writes. Their existing-file and failure effects remain unresolved. E-10, E-11; A-4, A-10 |

### 2.2 Interest Transaction Generation

| Element | Source-grounded meaning |
|---|---|
| Purpose | Compute category-balance-derived interest amounts, accumulate them for the current account group, and construct transaction records. E-2, E-12, E-14 |
| Inputs | Sequential category balances, account grouping data, account-key xref information, disclosure rates, external `PARM-DATE`, and current-date timestamp information. E-5, E-12–E-14, E-20–E-23 |
| Preconditions | Relevant opens and reads permit progress; a non-EOF category record reaches processing. The computation/write path is selected by a nonzero disclosure rate, not by a positive balance or positive computed amount. E-12–E-15 |
| Behavior | Recognize account transitions, update the preceding account subject to the first-time guard, reset the accumulator, load account/xref information, select a rate with bounded fallback, and compute/write for nonzero rates. R-7–R-11 |
| Conditional postconditions | An invoked account update adds accumulated interest and clears both cycle fields before rewrite. Each invoked computation adds the receiving-field result to the accumulator and invokes transaction writing. E-12, E-14 |
| Outputs | Constructed transaction-write attempts; no fee computation is established by the placeholder paragraph. E-14 |
| Side effects | Account rewrite attempts and sequential transaction-output activity are distinct. On the normal EOF path, generated transaction writing does not imply a final-account rewrite. E-12, E-14, E-15; A-11 |

### 2.3 Transaction Reporting

| Element | Source-grounded meaning |
|---|---|
| Purpose | Produce source-defined transaction detail, header, and total records through date-gated, card-change-sensitive processing. E-3, E-16–E-18 |
| Inputs | Sequential transactions, separately read date parameters, card xref information, transaction-type and category descriptions. E-6, E-16, E-18, E-21, E-24–E-26 |
| Preconditions | Relevant opens and reads permit progress. Date-parameter EOF sets the same EOF flag used by the transaction loop. Detail processing requires the date comparison to pass and the subsequent EOF test to permit the non-EOF branch. E-16, E-19 |
| Behavior | Apply the processing-timestamp comparison before the post-read EOF test; leave the loop sentence on its alternative; group by card changes; perform lookups; add amounts and write detail/header/total records at distinct sites. R-12–R-17 |
| Conditional postconditions | Each detail-path passage adds the transaction amount to page/account accumulators. Page-total processing transfers page accumulation into grand accumulation and clears the page accumulator; account-total processing clears account accumulation. E-17 |
| Outputs | Source-defined report-record write attempts, not a guaranteed complete date-range report or reconciled numerical result. E-16–E-18, E-28 |
| Side effects | Report output is opened and written. Finalization depends on date comparison over post-read storage whose EOF contents are unknown. E-16, E-19; A-14, A-15 |

### 2.4 Operation Dispatch Model

The three programs have distinct main procedures and corresponding job references. No common operation selector is evidenced. Within-track sequencing follows the respective source paths; mandatory study coverage does not prescribe cross-track execution order. E-1–E-3, E-7, E-12, E-16, E-29–E-34; R-19.

## Section 3: Named Semantic Rules

### 3.1 R-1 — Posting Selection Is Made Before Posting

- **Statement:** For each non-EOF daily record reaching processing, increment the transaction count, clear the reason and description, and perform preliminary checks. Reason zero then selects posting; a nonzero reason selects reject counting and reject writing.
- **Accepted outcome:** The posting paragraph is selected. This is preliminary acceptance, not proof that all posting effects succeed.
- **Rejected outcome:** Increment the reject count and attempt the reject-record write.
- **Scope and expression:** Posting only. EOF status `'10'` sets the EOF flag; no per-record selection follows that normal EOF read.
- **Evidence:** E-4, E-7. `app/cbl/CBTRN02C.cbl:193-234`, `345-378`.

### 3.2 R-2 — Posting Lookup and Comparison Precedence

- **Statement:** Card lookup uses the daily card number; its invalid-key branch assigns 100. Account lookup is performed only while the reason remains zero and uses the xref account identifier; its invalid-key branch assigns 101. In the non-invalid account branch, compute cycle credit minus cycle debit plus daily amount. A failed `credit limit >= computed value` comparison assigns 102; a subsequent failed `expiration text >= original timestamp first ten characters` comparison assigns 103.
- **Accepted outcome:** The comparisons that pass make no rejection assignment; equality passes each displayed comparison.
- **Rejected outcome:** The displayed branches assign their source reasons and descriptions.
- **Scope and expression:** Posting only. Under ordinary sequential execution, if both comparison alternatives occur, 103 and its description overwrite 102 and its description. This does not assert an intended business priority or calendar validation.
- **Evidence:** E-7, E-8, E-20, E-21, E-27. `app/cbl/CBTRN02C.cbl:370-422`.

### 3.3 R-3 — Posting Transaction and Reject Records Have Different Meanings

- **Statement:** Posting transfers the listed daily transaction fields into transaction storage, preserves the original timestamp, and supplies a newly constructed processing timestamp from `CURRENT-DATE`. Reject writing instead combines the daily record with the current reason trailer.
- **Accepted outcome:** The selected path prepares and attempts its corresponding write.
- **Rejected outcome:** Reject-record write failure follows its status-display and abend-call path; it is not an additional preliminary rejection rule.
- **Scope and expression:** Posting only. Daily and transaction declarations remain distinct despite similar layouts. No value is assigned here to untouched filler or unspecified storage.
- **Evidence:** E-4, E-9, E-26, E-27. `app/cbl/CBTRN02C.cbl:424-465`, `692-705`.

### 3.4 R-4 — Posting Category Accumulation Precedes Account Accumulation

- **Statement:** Build the category key from xref account, daily type, and daily category. Reset the create flag before lookup. An invalid-key lookup sets the create flag; the initial status handling admits `'00'` or `'23'`. The create path initializes category storage, assigns its key, adds the daily amount, and attempts a write; the existing-record path adds the amount and attempts a rewrite.
- **Accepted outcome:** The selected category operation proceeds through its successful status branch.
- **Rejected outcome:** Other checked statuses route to status display and the abend paragraph, not to the preliminary reject branch.
- **Scope and expression:** Posting only; signed amount addition is retained without reinterpretation as an absolute amount.
- **Evidence:** E-9, E-10, E-22. `app/cbl/CBTRN02C.cbl:440-442`, `467-542`.

### 3.5 R-5 — Posting Account Arithmetic and Reason 109

- **Statement:** Add the daily amount to current account balance. If the amount is nonnegative, add it to cycle credit; otherwise add the signed amount to cycle debit. Attempt account rewrite. Its invalid-key branch assigns reason 109 and the source description.
- **Accepted outcome:** The account rewrite is attempted after local arithmetic.
- **Rejected outcome:** Assignment of 109 does not itself increment the reject counter or invoke reject writing.
- **Scope and expression:** Posting only. **Static deduction:** assuming normal return from that invalid-key branch, the caller proceeds to transaction writing without rechecking the reason or revisiting the earlier selection.
- **Evidence:** E-7, E-9, E-10, E-20. `app/cbl/CBTRN02C.cbl:211-216`, `440-442`, `545-560`.

### 3.6 R-6 — Posting Completion Signals Do Not Establish Atomic Success

- **Statement:** Category write/rewrite, account rewrite, and transaction write are ordered attempts. Transaction-write non-success routes toward the external abend call after preceding attempts on a path reaching that site. No compensation appears in the inspected caller/update/write paragraphs.
- **Accepted outcome:** After the displayed closes, counts are displayed; a positive reject count causes assignment of 4 to `RETURN-CODE`.
- **Rejected outcome:** Checked I/O errors follow their local error paths. No guarantee that balances remain unchanged, or that partial changes persist, follows.
- **Scope and expression:** Posting only. `OPEN OUTPUT TRANSACT-FILE` remains significant; its deployed existing-file effects are unknown. No zero-reject return-code value is invented.
- **Evidence:** E-7, E-9–E-11, E-29. `app/cbl/CBTRN02C.cbl:221-234`, `254-270`, `424-579`.

### 3.7 R-7 — Interest Accumulation Is Account-Transition Driven

- **Statement:** On a changed category-record account identifier, update the previous account unless the first-time guard suppresses that update; then clear accumulated interest, retain the new account identifier, and perform account and account-key xref reads.
- **Accepted outcome:** Invoked account update adds accumulated interest to current balance, clears cycle credit and debit, and attempts rewrite.
- **Rejected outcome:** Account/xref read and account rewrite failures follow their checked error paths; no business-reject output is defined for them.
- **Scope and expression:** Interest only. This is grouping by encountered account transitions, not a proven global grouping property of actual input data.
- **Evidence:** E-5, E-12, E-13, E-20–E-22. `app/cbl/CBACT04C.cbl:188-218`, `350-413`.

### 3.8 R-8 — Normal Interest EOF Does Not Flush the Final Account

- **Statement:** Under standard default pre-test semantics, a normal EOF read sets the flag inside the already selected outer `THEN`; the inner test skips processing, and the next loop test exits. The outer `ELSE` is not reselected, and there is no post-loop account update.
- **Accepted outcome:** The normal EOF path proceeds to closes without a final-group update.
- **Rejected outcome:** Not a business rejection rule. Abnormal control flow and external intervention are outside this deduction.
- **Scope and expression:** Interest only. Transaction writing during category processing remains distinct from account rewriting. No final update is inserted.
- **Evidence:** E-12, E-14. `app/cbl/CBACT04C.cbl:188-228`, `325-370`, `462-515`.

### 3.9 R-9 — Disclosure Fallback Is Status-Specific

- **Statement:** Select disclosure information using account group, transaction type, and category. On initial status `'23'`, replace the group key with `'DEFAULT'` and perform a second read. The second read requires the displayed `'00'` success branch.
- **Accepted outcome:** A successful selected disclosure read supplies rate storage for the subsequent nonzero-rate test.
- **Rejected outcome:** Other checked initial statuses or an unsuccessful default read route to status display and the abend paragraph.
- **Scope and expression:** Interest only. Missing disclosure information is not normalized to a zero rate. Actual rate contents and units are unknown.
- **Evidence:** E-12, E-13, E-23. `app/cbl/CBACT04C.cbl:210-216`, `415-460`.

### 3.10 R-10 — Interest Uses the Literal Computation and Receiving Field

- **Statement:** When the selected disclosure rate is nonzero, compute `(TRAN-CAT-BAL * DIS-INT-RATE) / 1200` into `WS-MONTHLY-INT`, add that receiving-field value to `WS-TOTAL-INT`, and invoke transaction writing.
- **Accepted outcome:** A nonzero rate selects computation and writing, including where the balance or resulting amount is zero or negative.
- **Rejected outcome:** A zero rate bypasses both computation and the fee-paragraph call in this branch; this is not a rejection record.
- **Scope and expression:** Interest only. The two interest receivers are fixed-decimal `S9(09)V99`; the COMPUTE has no explicit `ROUNDED` or `ON SIZE ERROR`. No rate units, required rounding policy, or actual overflow result is inferred.
- **Evidence:** E-5, E-12, E-14, E-22, E-23. `app/cbl/CBACT04C.cbl:166-173`, `214-217`, `462-470`.

### 3.11 R-11 — Generated Interest Transaction Construction Is Local

- **Statement:** Each invoked transaction-write paragraph increments the six-digit suffix initialized to zero and combines `PARM-DATE` with it for the identifier. It assigns the source literals `'01'`, `'05'`, and `'System'`, constructs the account-related description, assigns computed amount and xref card, sets merchant fields to zero/spaces, and assigns constructed current-date information to both timestamps.
- **Accepted outcome:** The constructed transaction reaches its write attempt and successful status branch.
- **Rejected outcome:** Write non-success routes to status display and the abend paragraph.
- **Scope and expression:** Interest only. The job literal `PARM='2022071800'` is documentary configuration, not proof of an actual invocation. Identifier uniqueness across runs, suffix exhaustion, parameter validity, and safe repetition remain unknown. The fee paragraph contains only its placeholder comment and `EXIT`; it establishes no fee calculation or application-wide fee absence.
- **Evidence:** E-5, E-14, E-26, E-30. `app/cbl/CBACT04C.cbl:175-180`, `473-520`, `613-626`; `app/jcl/INTCALC.jcl:20-41`.

### 3.12 R-12 — Report Date Failure Leaves the Loop Sentence

- **Statement:** After a transaction read, compare the first ten processing-timestamp characters inclusively with the separately read start/end fields before checking post-read EOF.
- **Accepted outcome:** A passing date comparison permits the subsequent EOF test.
- **Rejected outcome:** **Static deduction:** under standard `NEXT SENTENCE` semantics, the date alternative transfers beyond the separator period at line 206 to the following closes; it is not “skip this record and continue.”
- **Scope and expression:** Reporting only. Date-parameter EOF sets the loop EOF flag before transaction processing. Post-transaction-EOF timestamp storage is unknown.
- **Evidence:** E-6, E-16, E-26. `app/cbl/CBTRN03C.cbl:159-243`, `248-272`.

### 3.13 R-13 — Account-Labelled Report Groups Are Triggered by Card Changes

- **Statement:** In the non-EOF detail path, a changed card number triggers the account-total call when first-time is `'N'`, then replaces current-card state and performs card-key xref lookup. Type and composite type/category lookups follow for the transaction.
- **Accepted outcome:** The detail path uses the resulting lookup storage, including the xref account identifier.
- **Rejected outcome:** Invalid-key lookup branches display their keys, assign 23 to `IO-STATUS`, and invoke status display and abend processing.
- **Scope and expression:** Reporting only. The grouping predicate compares card numbers, not account identifiers. No one-card-per-account assumption or invented handling for other lookup failures is adopted.
- **Evidence:** E-6, E-16, E-18, E-21, E-24, E-25. `app/cbl/CBTRN03C.cbl:179-196`, `484-512`.

### 3.14 R-14 — Report Accumulators Have Distinct Update Sites

- **Statement:** Each detail-report passage adds the transaction amount to page and account accumulation. Page-total processing writes the page-total record, adds page accumulation to grand accumulation, and clears page accumulation. Account-total processing writes its record and clears account accumulation. Grand-total processing writes the current grand accumulation.
- **Accepted outcome:** When the respective paragraph is reached and processing continues, its listed accumulation and output steps occur.
- **Rejected outcome:** Report-write errors route through the report-write error path; no alternative reconciled total is supplied.
- **Scope and expression:** Reporting only. Initial totals are zero. Paragraph names do not establish complete account or date-range totals.
- **Evidence:** E-6, E-16–E-18, E-28. `app/cbl/CBTRN03C.cbl:274-322`, `343-359`.

### 3.15 R-15 — EOF Report Finalization Is Conditional and Asymmetric

- **Statement:** Only if the preceding date comparison permits reaching the EOF test does the displayed EOF alternative add `TRAN-AMT` to page/account accumulation and call page-total and grand-total writing. It contains no account-total call.
- **Accepted outcome:** Reaching this branch selects those explicit steps, not final account-total emission.
- **Rejected outcome:** Taking the earlier date alternative bypasses this finalization path.
- **Scope and expression:** Reporting only. A repeated contribution of the last amount is a **runtime-dependent hypothesis**, requiring retained last-record storage and a passing EOF date comparison. Neither premise is established; no numerical double-counting result is asserted.
- **Evidence:** E-16, E-17. `app/cbl/CBTRN03C.cbl:170-206`, `287-322`.

### 3.16 R-16 — Pagination and Detail Presentation Are Source-Defined

- **Statement:** First-time report writing assigns header dates and writes headers. The subsequent modulo test uses the line counter and page size 20 to select page totals and further headers. Headers, totals, separators, and details have their own counter increments.
- **Accepted outcome:** Reached detail writing initializes detail storage and moves transaction identifier, xref account identifier, codes, descriptions, source, and amount into the report group.
- **Rejected outcome:** Report-write non-success follows the displayed error path; no substitute presentation is defined.
- **Scope and expression:** Reporting only. Page size is not twenty detail records. Description receivers are 15 and 29 characters, distinct from the 50-character lookup descriptions; detail and total amount pictures differ. No lossless-description or unlimited-numeric-display guarantee follows.
- **Evidence:** E-6, E-17, E-18, E-24–E-26, E-28. `app/cbl/CBTRN03C.cbl:274-374`; `app/cpy/CVTRA07Y.cpy:4-66`.

### 3.17 R-17 — Reporting Has Two Distinct Date Selection Sites

- **Statement:** The job's SORT instructions use literal inclusive bounds `2022-01-01` and `2022-07-06` and card sorting instructions. COBOL separately reads `DATEPARM` and performs its own comparison.
- **Accepted outcome:** **Conditional operational deduction:** if executable job steps supply the displayed SORT output as COBOL input, widening the later COBOL range cannot restore rows removed upstream.
- **Rejected outcome:** No common override or preferred date authority is evidenced. Complete output cannot be characterized merely as the intersection of two ranges because R-12 can terminate processing early.
- **Scope and expression:** Reporting only. Actual date-file contents, SORT behavior under the deployed configuration, dataset flow, duplicate step-label handling, and missing procedure control material remain unresolved.
- **Evidence:** E-16, E-31, E-34. `app/jcl/TRANREPT.jcl:19-80`; `app/proc/REPROC.prc:19-29`.

### 3.18 R-18 — Error Call Sites Do Not Supply External Failure Semantics

- **Statement:** The three programs distinguish local status handling and diagnostic output from calls to `CEE3ABD`, using code 999 and timing zero.
- **Accepted outcome:** A local success status permits the corresponding source continuation only.
- **Rejected outcome:** Reaching the abend call establishes a call attempt, not its termination, rollback, persistence, or return behavior.
- **Scope and expression:** Posting, interest, reporting, separately. Preserve diagnostic mismatches: posting reject-close moves xref status despite its reject label; interest disclosure-open names daily rejects while moving disclosure status. These are not corrected into reliable resource diagnoses.
- **Evidence:** E-11, E-15, E-19. Their defining open/close, diagnostic, and external-call anchors.

### 3.19 R-19 — Operational Resource Context Does Not Establish a Cycle Schedule

- **Statement:** Program/job bindings, backup instructions, combination sorting, deletion/definition instructions, and procedure references provide bounded operational dependencies, not proof of a required or completed cross-track sequence.
- **Accepted outcome:** Documentary relationships can inform conditional reasoning while retaining source-local ownership.
- **Rejected outcome:** No claim of executed backup, restored master, complete combination, shared live generation, or executable cycle is selected.
- **Scope and expression:** Posting and interest consume E-32; all three consume E-33–E-34. `REPROCT` is unavailable. Matching names do not establish resource-instance identity.
- **Evidence:** E-29–E-34.

### 3.20 R-20 — Repetition Safety Remains Unknown Per Track

- **Statement:** Repetition is **unknown to be safe** for each track. Posting contains balance additions and output-open/write activity; interest contains account additions/resets and locally constructed identifiers; reporting contains output-open/write activity and configuration-sensitive selection.
- **Accepted outcome:** No repeat-safety guarantee is established.
- **Rejected outcome:** No automatic retry, rollback, compensation, or reset behavior is inferred.
- **Scope and expression:** Posting: E-9–E-11. Interest: E-5, E-12, E-14–E-15. Reporting: E-16–E-19. Shared operational lifecycle context: E-32–E-34. These support uncertainty, not a universal claim that every repeated invocation necessarily causes damage.
- **Evidence:** E-5, E-9–E-12, E-14–E-19, E-32–E-34.

### 3.21 Failure, Ordering and Repetition Semantics

Preliminary posting rejection is distinct from an I/O error, an unavailable lookup dependency, and an external failure call. Interest and reporting error paths are not assigned posting rejection meanings. R-1, R-5, R-9, R-13, R-18.

Posting establishes earlier modification attempts before final transaction writing, but not their durability. Interest establishes record-time transaction writing separately from transition-time account rewriting. Reporting establishes conditional finalization rather than unconditional end-of-input totals. R-6, R-8, R-15.

No observed timeout, process termination, restart, or durable failure result is available. Repeat safety remains unknown for every track. R-18, R-20.

## Section 4: Data Semantics

The following are source-local meanings, not canonical definitions.

| Track / resource | Meaning, identity and state scope | Initialization, persistence and limits |
|---|---|---|
| Posting daily input | Candidate transaction records; daily identifier and card have distinct roles. E-4, E-27; R-1–R-3 | Sequential reads and EOF handling are established; actual contents/order are unavailable. |
| Posting xref | Card-key lookup supplies account identity used by account/category processing. E-21; R-2, R-4 | Input access; actual mappings and dependency completeness remain unknown. |
| Posting account | Current balance, cycle fields, limit, and expiration participate in different expressions. E-20; R-2, R-5 | Read and rewrite attempts; no durable postcondition inferred. |
| Posting category balance | Accumulation identified by account/type/category. E-22; R-4 | Creation initializes storage; existing-record processing adds to read storage. |
| Posting transaction output | Prepared posted-transaction record, distinct from daily input. E-26, E-27; R-3, R-6 | OUTPUT open and indexed write attempts; existing-file effects unknown. |
| Posting reject output | Daily record plus reason/description trailer selected before posting. E-4, E-9; R-1, R-3 | Reject count starts at zero; count is not proof of durable reject output. |
| Interest category input | Balance records drive computation and account-transition detection. E-22; R-7, R-10 | Sequential access; actual encountered grouping is not supplied. |
| Interest account | Current group’s account supplies disclosure group and receives accumulated interest/cycle resets when update is invoked. E-20; R-7, R-8 | Accumulated interest is cleared on account transition; normal EOF has no final flush. |
| Interest xref | Account-key lookup supplies card information for generated transactions. E-5, E-21; R-7, R-11 | Alternate-key multiplicity and actual binding remain unknown. |
| Interest disclosure | Group/type/category identifies rate information, with status-specific default-group fallback. E-23; R-9, R-10 | Rate contents, units, and required numeric policy unresolved. |
| Interest transaction output | Computation-time constructed transaction, not proof of corresponding account rewrite. E-26; R-8, R-11 | Suffix begins at zero; global identifier lifetime and output durability unknown. |
| Reporting transaction input | Supplies processing timestamp, card, codes, source, and amount. E-26; R-12–R-16 | EOF flag does not establish record-buffer contents. |
| Reporting xref | Card-key lookup supplies the account identifier displayed in detail. E-21; R-13, R-16 | Current card starts as spaces; grouping remains card-triggered. |
| Reporting type lookup | Type identifies descriptive text used in detail. E-24; R-13, R-16 | Actual descriptions unavailable; receiving width differs. |
| Reporting category lookup | Type/category identifies descriptive text used in detail. E-25; R-13, R-16 | Actual descriptions unavailable; receiving width differs. |
| Reporting date input | Separate start/end comparison fields and header values. E-6, E-16; R-12, R-17 | No contents, default range, or relationship to SORT literals invented. |
| Reporting output | Headers, details, page/account/grand-total records have distinct write sites. E-28; R-14–R-16 | Counters/totals begin at zero; output durability and actual final totals unresolved. |
| Backup/combined resources | Documentary transaction-resource lifecycle context with track-specific consumers. E-32–E-34; R-19 | Generation resolution, external control contents, schedule, and durable outcomes unknown. |

Currency, business rate units, universal account/card cardinality, and cross-track record-instance identity are not established by shared field names or PIC declarations. E-20–E-28; A-1, A-8, A-12, A-15.

## Section 5: Ambiguity Disposition

“Retained under authorized conditional scope” below records application of the supplied Stage 3-r2 disposition, not new human approval or resolution.

| ID | Disposition and adopted interpretation | Revisit trigger / blocked claim |
|---|---|---|
| A-1 | Open. Keep three mandatory tracks and unchanged chain identity; no final unified business decomposition. E-1–E-6 | Explicit boundary reconciliation; final cohesion claims remain blocked. |
| A-2 | Open. Allowlist does not establish dependency closure. E-29–E-34 | Newly authorized dependency evidence; completeness/executability claims blocked. |
| A-3 | Partially addressed upstream. Supplied numbered representation is UTF-8; deployed encoding remains unknown. | Authorized byte/deployment evidence. |
| A-4 | Open, retained under conditional scope. Local arithmetic and I/O attempts are not durable effects. R-6, R-18, R-20 | Authorized runtime evidence; persistence, restart and isolation guarantees blocked. |
| A-5 | Open. Use of approved upstream drafts is disclosed; broader participant exposure is not established. | Exposure records; independent/clean-context research claims blocked. |
| A-6 | Open. E-35 is licensing context, not behavioral semantics or legal clearance. | Authorized legal review for relevant activity. |
| A-7 | Addressed upstream for evidence layout. One E-n sequence and separate tracks are retained. | Authorized change of layout or namespace. |
| A-8 | Open. Documentary resource relationships do not establish required cross-job chronology. R-19 | Authorized schedule/resource evidence. |
| A-9 | Statically narrowed. Retain 103-over-102 assignment precedence and no reject reselection after 109 on normal return. R-2, R-5 | Changed evidence or explicit intended-policy decision; actual I/O effects remain unknown. |
| A-10 | Open runtime residual. Ordered attempts and no inspected local compensation are established; neither atomicity nor durable partial persistence is selected. R-6 | Deployment open semantics and authorized persistence observations. |
| A-11 | Statically narrowed. Adopt normal pre-test EOF deduction without final-account flush, separately from generated writes. R-7, R-8 | Contrary control-flow evidence or authorized abnormal-path observations. |
| A-12 | Open. Literal formula, receiving fields and local identifier construction only. R-10, R-11 | Rate-unit, numeric-policy, parameter, overflow or identifier-lifetime evidence. |
| A-13 | Open beyond inspected paragraph. Placeholder supplies no fee computation; job comment does not fill it. R-11 | Authorized fee-scope evidence; fee-computation claims blocked. |
| A-14 | Open configuration/runtime residual. Adopt sentence-level exit and two distinct date sites; leave EOF storage and actual selection unknown. R-12, R-15, R-17 | Date contents, executable job context, or authorized failed-read observations. |
| A-15 | Open meaning/runtime residual. Card-change grouping, total sites and absent EOF account-total call retained; numerical duplication remains conditional. R-13–R-16 | Actual card/account relationships, storage behavior and reporting-policy evidence. |
| A-16 | Open. Duplicate `STEP05R` and missing `REPROCT` remain unrepaired. R-17, R-19 | Authorized operational clarification; executable-chain claims blocked. |
| A-17 | Open. External call arguments are known; routine behavior is not. R-18 | Authorized external-routine evidence; termination and persistence consequences blocked. |

No ambiguity is closed by selecting conventional financial behavior. No desired-behavior decision is made.

## Section 6: Reverse-Completeness Matrix — Semantic Enrichment

Every Stage 3 item E-1–E-35 is accounted for below. The matrix starts from upstream observations and behavior inventory, not from a proposed downstream surface. References to rules identify semantic coverage; residual ambiguities delimit that coverage.

The template’s downstream columns remain placeholders only.

| Operation / rule / effect | Evidence | Semantic representation | Boundary signal | Contract destination / exclusion / gap |
|---|---|---|---|---|
| Posting identity/header | E-1 | Section 2.1 orientation; comment is not an independent behavioral rule | pending Stage 5 | pending Stage 6 |
| Interest identity/header | E-2 | Section 2.2 orientation; behavior derived from statements | pending Stage 5 | pending Stage 6 |
| Reporting identity/header | E-3 | Section 2.3 orientation; header does not guarantee complete reporting | pending Stage 5 | pending Stage 6 |
| Posting resources, records and initial counters | E-4 | R-1, R-3; Section 4; runtime scope A-4 | pending Stage 5 | pending Stage 6 |
| Interest access, receivers, grouping and linkage | E-5 | R-7, R-10, R-11, R-20; A-12 | pending Stage 5 | pending Stage 6 |
| Reporting access, dates, page size and initial state | E-6 | R-12–R-14, R-16; A-14, A-15 | pending Stage 5 | pending Stage 6 |
| Posting loop, selection, count and completion assignment | E-7 | R-1, R-2, R-5, R-6 | pending Stage 5 | pending Stage 6 |
| Posting lookup, comparisons and reason precedence | E-8 | R-2; A-9 residual intended-policy uncertainty | pending Stage 5 | pending Stage 6 |
| Posting construction, rejects and ordered caller | E-9 | R-3–R-6, R-20; A-10 | pending Stage 5 | pending Stage 6 |
| Posting category/account changes and final write | E-10 | R-4–R-6, R-20; A-9, A-10 | pending Stage 5 | pending Stage 6 |
| Posting open/close/error/external call context | E-11 | R-6, R-18, R-20; diagnostic mismatch retained; A-10, A-17 | pending Stage 5 | pending Stage 6 |
| Interest transition, accumulation update and EOF | E-12 | R-7–R-10, R-20; A-11 | pending Stage 5 | pending Stage 6 |
| Interest account/xref/disclosure reads and fallback | E-13 | R-7, R-9; A-2, A-12 | pending Stage 5 | pending Stage 6 |
| Interest arithmetic, construction, timestamp and fees | E-14 | R-8, R-10, R-11, R-20; A-12, A-13 | pending Stage 5 | pending Stage 6 |
| Interest open/close/error/external call context | E-15 | R-18, R-20; diagnostic mismatch retained; A-4, A-17 | pending Stage 5 | pending Stage 6 |
| Reporting date gate, loop exit, grouping and EOF | E-16 | R-12–R-15, R-17, R-20; A-14, A-15 | pending Stage 5 | pending Stage 6 |
| Reporting pagination and accumulation sites | E-17 | R-14–R-16, R-20; A-15 | pending Stage 5 | pending Stage 6 |
| Reporting detail, lookup and write-error paths | E-18 | R-13, R-14, R-16, R-20 | pending Stage 5 | pending Stage 6 |
| Reporting open/close/error/external call context | E-19 | R-18, R-20; A-4, A-17 | pending Stage 5 | pending Stage 6 |
| Account declarations: posting and interest | E-20 | Posting R-2, R-5; interest R-7; Section 4 distinguishes uses | pending Stage 5 | pending Stage 6 |
| Xref declarations: all three tracks | E-21 | Posting R-2; interest R-7; reporting R-13; cardinality remains A-15 | pending Stage 5 | pending Stage 6 |
| Category-balance declarations: posting and interest | E-22 | Posting R-4; interest R-7, R-10 | pending Stage 5 | pending Stage 6 |
| Disclosure declarations: interest | E-23 | R-9, R-10; units remain A-12 | pending Stage 5 | pending Stage 6 |
| Type descriptions: reporting | E-24 | R-13, R-16; actual descriptive contents unavailable | pending Stage 5 | pending Stage 6 |
| Category descriptions: reporting | E-25 | R-13, R-16; actual descriptive contents unavailable | pending Stage 5 | pending Stage 6 |
| Transaction declarations: all three tracks | E-26 | Posting R-3; interest R-11; reporting R-12, R-16; no merged resource identity | pending Stage 5 | pending Stage 6 |
| Daily declarations: posting | E-27 | R-2, R-3; distinct daily-record meaning retained | pending Stage 5 | pending Stage 6 |
| Report declarations: reporting | E-28 | R-14, R-16; A-15 numerical/presentation residuals | pending Stage 5 | pending Stage 6 |
| Posting job bindings | E-29 | R-6, R-19; documentary bindings, not deployed effects | pending Stage 5 | pending Stage 6 |
| Interest job parameter/output and fee comment | E-30 | R-11, R-19; A-12, A-13 | pending Stage 5 | pending Stage 6 |
| Reporting SORT/date/output and duplicate labels | E-31 | R-17, R-19; A-14, A-16 | pending Stage 5 | pending Stage 6 |
| Combination instructions: posting and interest | E-32 | R-19, R-20 for both consumers; schedule and results unresolved A-8 | pending Stage 5 | pending Stage 6 |
| Backup/delete/define context: all three tracks | E-33 | R-19, R-20; no completed backup/reset meaning inferred | pending Stage 5 | pending Stage 6 |
| Procedure and missing control member: all three tracks | E-34 | Reporting R-17; all three R-19, R-20; A-16 | pending Stage 5 | pending Stage 6 |
| Shared licensing context | E-35 | Justified non-semantic observation: license text does not define posting, interest or reporting behavior; legal clearance remains A-6 | pending Stage 5 | pending Stage 6 |

This accounting does not establish behavioral completeness. Declaration-only fields, labels, and comments are not forced into invented business obligations.

## Section 7: Completeness Gate and Stage 5 Entry Condition

### 7.1 Completeness Conditions

- [ ] All operations semantically modeled with pre/postconditions and side effects
- [ ] All core rules named (`R-n`), with accepted/rejected outcomes and evidence
- [ ] Data semantics defined (concept, identity, state scope, persistence)
- [ ] All semantics-touching ambiguities disposed or explicitly blocking
- [ ] Reverse-completeness matrix enriched from Stage 3 inventory at semantic level only
- [ ] No interface/implementation vocabulary present

These are external review conditions, not self-certified results. Preserved generic policy and template wording are not application-level decisions.

Additional local conditions:

- [ ] Posting, interest, and reporting receive separate substantive review.
- [ ] Rule identifiers and every E-1–E-35 destination are reconciled.
- [ ] Shared evidence retains its authorized consuming tracks.
- [ ] Reason precedence and reason 109 are reviewed without idealized rejection-policy substitution.
- [ ] Ordered attempts are distinguished from both atomicity and durable partial persistence.
- [ ] Interest EOF semantics retain the pre-test and normal-control assumptions.
- [ ] Reporting date exit, EOF storage uncertainty, card grouping, and total sites remain distinct.
- [ ] Missing dates, control material, external routines, numeric policy, and repeat safety remain explicit.

### 7.2 Semantic Integrity Condition

- [ ] Sampled claims trace back to `E-n` anchors or carry inference labels (traceability spot-check)

No mechanical anchor or integrity check was performed in this response. Supplied hashes are version pins, not newly verified checksums.

### 7.3 Counterexample Review Condition

- [ ] Recorded review includes risk-oriented samples for rule reading, claimed absence in dependencies, failure with persisted effects, and omitted obligation — or justified N/A with inspected scope
- [ ] Each sampled item has passage/objection/conclusion and resulting `R-n` / `A-n` / `G-n` disposition where applicable
- [ ] Review record states that the sample does not prove completeness

Required review targets include R-2/R-5 reason handling; R-6 failure after earlier attempts; R-8 final-account omission; R-11 bounded fee absence; and R-12/R-15/R-17 reporting termination and finalization. These are review targets, not scenarios, expected outcomes, or completed review findings.

### 7.4 Review Gaps

New gap identifiers continue after the upstream G-1–G-10 register.

| ID | Classification | Gap and required handling |
|---|---|---|
| G-11 | Blocking for Stage 4 completion | No human review of this concrete semantic artifact is recorded. Review all three tracks and conditional deductions. |
| G-12 | Blocking for review finalization | This response has no persisted output digest or bound review record. Preserve exact input/output versions and record actual review separately. |
| G-13 | Blocking for unrestricted semantic claims | A-4, A-8, A-10, A-12, A-14–A-17 prevent runtime, configuration, numerical, or full-cycle guarantees. Retain scoped limits; do not treat upstream permission to proceed conditionally as resolution. |
| G-14 | Blocking for gate completion | Required traceability and counterexample review records are not supplied for this artifact. Complete them externally without treating mechanical checks as substantive approval. |

### 7.5 AI Assistance and Provenance

AI assistance is limited to deriving and structuring conditional semantic interpretations from supplied approved evidence and numbered source text. The upstream material is explicitly supplied; this is not an independent extraction or experimental replica.

No tools, external retrieval, source changes, compilation, or execution were used. No excluded preparation or evaluation outputs were accessed. References to such materials within approved upstream or generic instructions were not used as application evidence.

Exact request/response retention, actual model configuration, usage, cost, generation timing, and later human corrections belong in the run record. Unavailable telemetry is not zero, and transport settings are not certified here.

### 7.6 Stage 5 Entry Condition

**Stage 5 may begin** only when the conditions above hold and human review outcome is Approve.

**Current Stage 4 status: not approved. Completeness gate: not passed. Ready for implementation: `false`.**

This specification grants no gate approval and no authorization for further-stage work.