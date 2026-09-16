# Stage 3 targeted review — proposed feedback, not a gate decision

## Scope and recommendation

Review requested by Researcher: inspect the important issues before deciding review feedback. This is a read-only documentary inspection of the authorized source corpus, not execution, a repaired model response, Stage 4 production, or approval. Corpus bytes were checked against the stage-3 manifest. The original requirements.md remains unchanged. No evaluation-quarantine, prior test results, or E1/E2 responses were consulted.

Recommendation: request a focused Stage 3 revision. Its caution about runtime is appropriate, but some open questions can already be narrowed by source control-flow inspection. Distinguish documentary facts, static deductions with assumptions, and runtime-dependent outcomes. Do not declare every uncertainty resolved or approve Stage 4 yet.

All paths below are relative to CORPUS_ROOT; exact source hashes remain in specs/legacy-evidence-carddemo/anchor-manifest.json.

## R1 — Posting reason precedence and reason 109 (A-9)

Evidence: app/cbl/CBTRN02C.cbl:202-219, 370-421, 440-442, 545-579.

The source gates account lookup on reason zero after xref lookup. Within a successful account lookup, two successive IF statements assign 102 for the amount comparison and then 103 for the date comparison. Static deduction: when both alternative branches are taken, 103 overwrites 102. This is not an unresolved choice of intended business priority.

The reason-zero decision occurs before performing posting. The account REWRITE invalid-key branch assigns 109, but the caller proceeds to transaction WRITE without rechecking that reason. The reject counter/write branch belongs to the earlier decision and is not revisited. On this explicit source path, 109 does not automatically produce a reject record; do not normalize it into the earlier reject handling. Actual I/O errors and external runtime consequences are not measured.

Requested feedback: add these specific control-flow facts and conditionally derived consequences; narrow A-9 rather than silently defining an ideal rejection policy.

## R2 — Posting updates and partial effects (A-10)

Evidence: app/cbl/CBTRN02C.cbl:254-269, 424-442, 503-579.

The transaction file is opened OUTPUT. The posting caller performs category update, account update, then transaction write. Category WRITE/REWRITE and account REWRITE precede the final transaction WRITE in the explicit path. No compensation is present in these inspected paragraphs. A transaction WRITE failure routes to CEE3ABD after these earlier operations have been attempted.

Static conclusion: the code does not establish all-or-nothing behavior across those sites. Do not claim that a failed posting necessarily leaves balances unchanged. Conversely, the inspection does not prove durable partial persistence on a particular filesystem/runtime or effects of OUTPUT opening an existing indexed file. Do not state that a particular duplicate-key scenario was executed.

Requested feedback: retain order and lack of local compensation as source evidence; leave durability, open-mode deployment effects, and external abend behavior explicitly runtime-dependent.

## R3 — Interest final-account path (A-11)

Evidence: app/cbl/CBACT04C.cbl:188-228, 325-370, 462-500.

The inline PERFORM UNTIL uses the default pre-test. Its outer IF tests END-OF-FILE before the read. Reading EOF sets the flag to Y; the inner IF then skips processing. The already-selected outer THEN does not switch to its ELSE after the flag changes. At the next loop test, Y exits the loop. There is no post-loop account-update call before the closes.

Static deduction for the displayed normal EOF path: the ELSE at lines 219-220 does not flush the final account. Account update is called on a later account transition at lines 194-196; the last account group has no such later transition. Interest transaction writes occur through a separate paragraph during processing. Thus transaction generation and final account rewrite must not be assumed equivalent. This is stronger than merely saying that final-account behavior is unknown, but it is not a measured runtime result.

Requested feedback: expose the loop/IF nesting and missing final flush explicitly. Preserve the legacy; do not add a final update as a silent repair.

## R4 — Reporting NEXT SENTENCE and termination (A-14)

Evidence: app/cbl/CBTRN03C.cbl:170-217, 248-272.

The out-of-range date branch uses NEXT SENTENCE, not CONTINUE or a loop-continue statement. The next separator period in the caller is at END-PERFORM (line 206), followed by close calls. Under COBOL NEXT SENTENCE control-flow semantics, this branch transfers beyond that sentence: it exits this reporting loop rather than simply skipping a record and reading another.

The date comparison also occurs before the post-read EOF check. Therefore the EOF-finalization branch is reached only if the date comparison permits it. No assumption is made about the contents of TRAN-RECORD after an unsuccessful READ INTO.

Requested feedback: explicitly anchor the jump target and qualify A-14 accordingly. Do not describe the source as a conventional filter that necessarily processes every subsequent eligible record.

## R5 — Report totals and grouping (A-15)

Evidence: app/cbl/CBTRN03C.cbl:179-204, 274-322.

Each processed detail adds TRAN-AMT to page/account totals. The EOF alternative contains another ADD TRAN-AMT before page/grand-total writing. The same branch contains no account-total call; account totals are emitted on card-number change at lines 181-183. Hence the grouping trigger is card change, not an account-ID comparison.

Conditional risk: if the EOF buffer retains the last processed record and passes the date comparison, the EOF ADD can include its amount again. This inspection does not establish that buffer-retention premise, so numerical double counting remains a runtime-dependent hypothesis, not an observed fact. The missing final account-total call and location of the extra ADD are directly visible.

Requested feedback: separate these visible sites from the conditional duplicate-total hypothesis. Do not infer correct totals or one group per account from paragraph labels.

## R6 — Two report-date inputs

Evidence: app/jcl/TRANREPT.jcl:37-48, 59-74; app/cbl/CBTRN03C.cbl:168-178, 220-243.

JCL SORT specifies literal dates and produces the dataset named as COBOL input. COBOL separately reads DATEPARM and performs its own date comparison. There is no evidenced single parameter overriding the other. If the displayed job steps are made executable and run as written, a row removed upstream is not restored by widening the later filter. Because NEXT SENTENCE can terminate reporting, describing the complete output as a simple intersection is also insufficient.

DATEPARM contents, duplicate STEP05R handling, missing procedure control material and actual execution are not settled here. Do not choose a preferred date source as though it were recovered behavior.

Requested feedback: describe two distinct filtering sites and preserve unsupplied configuration as unknown.

## Additional bounded clarifications

app/cbl/CBACT04C.cbl:166-178 and 462-520 shows fixed decimal receiving fields, no explicit ROUNDED or ON SIZE ERROR in the inspected COMPUTE, an initialized six-digit suffix, PARM-DATE plus suffix for the ID, and a fee paragraph containing only its placeholder comment and EXIT. Record these facts without inventing rate units, a global uniqueness guarantee, runtime overflow results or application-wide fee absence.

## Proposed review decision text

Request revision, not approval: strengthen the evidence on reason precedence/109, normal EOF finalization of interest, the NEXT SENTENCE target, and report total/grouping sites. Keep persistence, runtime buffer behavior, external dependencies and missing date configuration open with precise boundaries. Preserve all three mandatory tracks and the original output. No COBOL repair, new model call, execution experiment, Stage 4 authorization or gate approval is implied by this review.
