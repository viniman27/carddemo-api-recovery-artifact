# Stage 4 counterexample review

Technical recommendation: Approve within the already authorized conditional documentary scope. This is a review recommendation, NOT the human gate decision or Stage 5 authorization.

Reviewed artifact SHA-256: 2f9d3ee52dd7788e206810e38c9173b19d21dfc44270cdd06d05e62dec95eb93

Method: risk-oriented static inspection of the same authorized source evidence. No execution, source repair, evaluation quarantine, prior experimental outputs or new model generation. All corpus hashes matched the stage-3 manifest. This is not independent empirical evidence or exhaustive proof.

## CE-01 — Rule review / posting

Passage: R-2; A-9

Source: app/cbl/CBTRN02C.cbl:370-421 (all references corpus-relative; exact file hashes in the manifest).

Objection: Suppose both amount and expiration alternatives occur, or card lookup fails before account lookup. Could the rule retain 102 or perform unguarded account checks?

Conclusion: The later 103 assignment replaces 102; account lookup is reason-zero guarded. R-2 explicitly preserves both.

Disposition: Accept; R-2/A-9 unchanged.

## CE-02 — Rule review / posting

Passage: R-5

Source: app/cbl/CBTRN02C.cbl:545-559 (all references corpus-relative; exact file hashes in the manifest).

Objection: A negative amount could be silently converted into a positive debit by a conventional financial interpretation.

Conclusion: The source ADD uses the signed amount. R-5 explicitly retains signed addition, rather than absolute-value normalization.

Disposition: Accept; R-5 unchanged.

## CE-03 — Failure with persisted effects / posting

Passage: R-5, R-6, R-18; A-9, A-10, A-17

Source: app/cbl/CBTRN02C.cbl:424-442,545-579 (all references corpus-relative; exact file hashes in the manifest).

Objection: Account rewrite assigns 109 and returns, or final transaction WRITE fails after earlier operations. Does rejection imply no prior effects or stop subsequent writing?

Conclusion: There is no reason recheck between account and transaction calls. Earlier category/account operations precede final WRITE. Rules state attempted order, no reject reselection, and no guaranteed rollback or durable partial state. Actual persistence is not observed.

Disposition: Accept within documented runtime limits; retain A-10/A-17, no new outcome claim.

## CE-04 — Omitted obligation / interest

Passage: R-7, R-8; A-11

Source: app/cbl/CBACT04C.cbl:188-228,325-370 (all references corpus-relative; exact file hashes in the manifest).

Objection: Only one account group reaches normal EOF. Does the specification insert an expected final-account flush?

Conclusion: Default pre-test loop and outer/inner IF nesting provide no final flush on the stated path. R-8 preserves that deduction and distinguishes transaction writing from account update.

Disposition: Accept; no remedial final flush or observed balance claim.

## CE-05 — Rule review / interest

Passage: R-9, R-10; A-12

Source: app/cbl/CBACT04C.cbl:210-217,415-470 (all references corpus-relative; exact file hashes in the manifest).

Objection: Missing disclosure could be interpreted as a zero rate; zero or negative balance could be assumed to suppress transaction generation.

Conclusion: Status 23 selects a DEFAULT reread, not zero-rate substitution. The computation selector is nonzero rate; no positive-balance guard occurs there. R-9/R-10 preserve this. Arithmetic exceptions and actual outputs remain outside this sample.

Disposition: Accept; A-12 remains open.

## CE-06 — Claimed dependency absence / interest

Passage: R-11; A-13

Source: app/cbl/CBACT04C.cbl:518-520 (all references corpus-relative; exact file hashes in the manifest).

Objection: Does an empty local fee paragraph justify claiming no fees anywhere in CardDemo?

Conclusion: The inspected paragraph contains a placeholder comment and EXIT. R-11 explicitly limits the absence to that paragraph and does not claim application-wide absence. No unsupplied fee modules inspected.

Disposition: Accept bounded absence; retain A-13.

## CE-07 — Rule review / reporting

Passage: R-12; A-14

Source: app/cbl/CBTRN03C.cbl:170-213 (all references corpus-relative; exact file hashes in the manifest).

Objection: An out-of-range transaction precedes a later eligible one. Does the rule promise ordinary skip-and-continue filtering?

Conclusion: NEXT SENTENCE targets beyond the separator period at END-PERFORM, followed by closes. R-12 describes loop-sentence exit under standard COBOL semantics, not processing all later eligible records. This is a static deduction, not a test run.

Disposition: Accept; no conventional filter substituted.

## CE-08 — Omitted obligation / reporting

Passage: R-14, R-15; A-14, A-15

Source: app/cbl/CBTRN03C.cbl:170-204,274-322 (all references corpus-relative; exact file hashes in the manifest).

Objection: EOF storage retains a prior record versus does not retain it. Could the specification assert unconditional duplicate contribution or mandatory final account totals?

Conclusion: Date comparison precedes EOF test; the EOF alternative has an extra ADD and no account-total call. R-15 makes repeated contribution conditional on storage and date premises, and explicitly omits final account emission.

Disposition: Accept; buffer and numerical outcomes stay unresolved.

## CE-09 — Omitted obligation / reporting

Passage: R-13, R-16; A-15

Source: app/cbl/CBTRN03C.cbl:179-196,274-341,361-374 (all references corpus-relative; exact file hashes in the manifest).

Objection: Different cards might map to one account; headers and total records also advance the line counter. Are groups silently normalized to accounts or page size to detail count?

Conclusion: Grouping compares cards, and several non-detail paragraphs increment the line counter. R-13/R-16 preserve both distinctions. Actual card/account mappings and complete rendered output remain unknown.

Disposition: Accept; no account cardinality or twenty-detail-record page guarantee.

## CE-10 — Failure with persisted effects / reporting

Passage: R-13, R-14, R-18; A-4, A-17

Source: app/cbl/CBTRN03C.cbl:179-196,306-322,343-359,484-512 (all references corpus-relative; exact file hashes in the manifest).

Objection: At card change, a previous-group total write precedes a failing new-card lookup. Could an error be treated as an empty/unchanged report?

Conclusion: The total call precedes xref lookup. R-13 gives that order and R-14/R-18 limit writes and abend effects. Prior output attempts exist; durability and external termination are unmeasured.

Disposition: Accept jointly across rules; preserve A-4/A-17 and ordering in downstream derivation.

## CE-11 — Claimed dependency absence / posting, interest, reporting

Passage: R-18, R-19; A-2, A-8, A-16, A-17

Source: app/proc/REPROC.prc:19-29; CBTRN02C.cbl:574-577; CBTRN03C.cbl:486-510 (all references corpus-relative; exact file hashes in the manifest).

Objection: Does the visible corpus imply standalone execution or a known CEE3ABD implementation?

Conclusion: REPROC references unsupplied REPROCT; error sites invoke an external routine. R-18/R-19 explicitly deny dependency closure, known external failure behavior and proven cycle schedule. There is no global no-dependency claim to endorse.

Disposition: Accept retained unknowns; no invented external implementation.

## CE-12 — Rule review / reporting

Passage: R-17; A-14, A-16

Source: app/jcl/TRANREPT.jcl:37-74; CBTRN03C.cbl:170-177,220-243 (all references corpus-relative; exact file hashes in the manifest).

Objection: A wider DATEPARM range could be treated as overriding the upstream SORT range or the final result as a simple interval intersection.

Conclusion: The JCL literals and separate COBOL date input are distinct. R-17 uses a conditional executable-job premise and warns that NEXT SENTENCE defeats a simple full-output intersection description. DATEPARM contents remain unsupplied.

Disposition: Accept; no preferred date source or execution claim.

## Outcome and limits

The 12 sampled objections revealed no blocking contradiction requiring another generated revision. Existing R-n and A-n wording covers the sampled failures, omitted-finalization risks and bounded absence claims. No new R-n/A-n/G-n item is proposed. The documentary effort required by G-14 is now recorded; it does not eliminate the need for human approval. Do not claim that every rule or source branch has been exhaustively verified.

Downstream must retain unresolved durable write effects, failed-read buffer state, date configuration, missing control/external routines, numeric policy and repeat safety. These block unconditional outcome guarantees, not this recommendation for conditional source-grounded semantics. The original specification and gate metadata were not edited.
