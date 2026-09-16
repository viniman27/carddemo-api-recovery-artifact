# Legacy Evidence Specification

## Purpose

This Stage 3 artifact consolidates **documentary source evidence only** for run `E3-01` of the AWS CardDemo public cycle. It retains three mandatory, separately traceable tracks: **posting**, **interest**, and **reporting**.

The observations below describe supplied COBOL, copybook, JCL, and procedure text. They do not establish executed outcomes, recovered business obligations, or an executable end-to-end cycle.

| Attribute | Value |
|---|---|
| Run ID | `E3-01` |
| Pipeline stage | `3` |
| Feature | `legacy-evidence-carddemo` |
| Artifact type | `legacy-evidence` |
| Artifact path relative to `RUN_ROOT` | `specs/legacy-evidence-carddemo/requirements.md` |
| Immutable operational chain identity | `unselected-stage-1-scope-only` |
| Mandatory tracks | `posting`, `interest`, `reporting` |
| Status | Documentary draft for external human review |
| Human approval | `false` |
| Completeness gate passed | `false` |
| Ready for implementation | `false` |

This is the explicitly authorized local adaptation of `/sdd:spec-requirements --stage 3`, not a native slash command. This response supplies one specification; it does not assert filesystem persistence or metadata modification.

## Evidence Quality Discipline

- Every claim is one of: **observed evidence** (with anchor), **inference** (labeled), or **ambiguity** (registered as `A-n`).
- Evidence anchors use `file:line-range` (e.g., `main.cob:112-131`). Reference-layer anchors are marked as such and carry less weight.
- No semantic normalization yet: this artifact records what the legacy does, not what it means for modernization.

For this documentary authorization, **observed evidence means observation of source text**, not observation of execution. Comments, declarations, statements, and operational-document instructions remain distinguishable.

Evidence identifiers form one run-wide sequence, `E-1` through `E-35`; numbering does not restart by track. Their qualified identity is `E3-01/E-n`. Each defining entry states consuming tracks, full corpus-relative path, supplied original-file SHA-256, and inclusive line ranges from the supplied stable, 1-based `numbered_lines` representation. Subsequent references reuse those entries rather than create new evidence identities.

Original-file hashes and derived-representation hashes are distinct. The original-file hashes identify the corpus versions cited below; the supplied `input_pins.source_bodies` retains the separate derived-representation pins. Neither kind of hash is represented as independently recomputed.

## Section 1: Upstream Authority and Entry Condition

### 1.1 Upstream Authorities and Scope Inheritance

This artifact derives from the supplied approved Pipeline Scope Specification and revised Capability Selection Specification, together with the explicit Stage 3 authorization.

| Authority, relative to `RUN_ROOT` | Supplied SHA-256 |
|---|---|
| `specs/pipeline-scope-carddemo/spec.json` | `c71fe711834fec66fb417335a2f60cde5b9f3b5b63968849c71ecc513b465978` |
| `specs/pipeline-scope-carddemo/requirements.md` | `1362fab5d55b77ef6121328606ae974295cd5723849520e9a246f4bd45e64cc9` |
| `specs/capability-selection-carddemo-r2/spec.json` | `7d218739f4f338d568805051ec2e7f9ce70128d832c0dfbcdc11c34f704d2973` |
| `specs/capability-selection-carddemo-r2/requirements.md` | `abdb59180f379d9e14eb86dfa1d8226ec50c981346767e808fd382eb7462bbc4` |
| `reviews/stage-1-authorization.json` | `0ec9d89962c088507775523f266816b5c3c13f7631c7a6409b45bc13352542da` |
| `reviews/stage-2-r2-authorization.json` | `22294af2fb12235297e57e4b084a729695864af895d4047eb4a630d7286ec1c9` |

The supplied upstream metadata records completed human approvals for Stages 1 and 2-r2. Their original artifact text is not rewritten to replace historical draft-era statuses.

The Stage 2-r2 authorization states:

> Approve revised stage 2 three-candidate portfolio and authorize stage 3 documentary evidence only for all three mandatory areas. No stage 4 approval.

Its evidence-layout instruction states:

> Unique run-scoped E-n identifiers; every entry states track(s), full corpus-relative path, SHA-256 and line range. Shared evidence must explicitly list consuming tracks.

The inherited entry conditions are upstream approval, explicit track organization, and Stage 3-specific documentary visibility. The supplied authorization establishes the layout for this draft without granting approval of this artifact.

### 1.2 Inherited Constraints

- All three tracks remain mandatory; one track’s evidence cannot substitute for another’s.
- The portfolio does not establish one unified business capability or change the immutable operational chain identity.
- Only approved upstream documents, this authorization, supplied generic v3 instructions, and the exact 19 allowlisted corpus bodies inform extraction.
- The corpus remains immutable. No compilation, COBOL execution, network expansion, or runtime observations are included.
- Referenced but unsupplied resources remain unavailable; their contents are not reconstructed.
- No semantic reconstruction, canonical definitions, API claims, adapter behavior, validation results, or later-stage artifacts are produced.
- Framework and upstream text remain unchanged. Their references to excluded materials are not themselves application evidence.
- Shared source use does not establish shared business meaning, resource-instance identity, or a required cross-job schedule.
- This public study does not establish institutional applicability.

### 1.3 Roots and Representation

| Root | Supplied location |
|---|---|
| `RUN_ROOT` | `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/sdd-runs/E3-01` |
| `FRAMEWORK_ROOT` | `<REDACTED_LOCAL_PATH>/pipeline-sdd-v3/pipeline` |
| `CORPUS_ROOT` | `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-preparation/research-corpus` |

The supplied representations are described as:

> stable 1-based line numbering of exact UTF-8 source text; source content is otherwise unmodified

That description is the representation basis, not a filesystem or deployment-encoding finding.

The governing evidence template is `settings/templates/pipeline/legacy-evidence-spec.md`, supplied SHA-256 `fde83c5985c9d13213ec5deb01f047f1bd593b02b4196733a1fa8eeaa6e614bf`. The other eight framework documents remain the exact versions pinned in `input_pins.framework_context`.

## Section 2: Source Program Evidence

### 2.1 Program Inventory and Capability-Relative Roles

| ID | Track(s) | Full anchor | File SHA-256 | Documentary observation |
|---|---|---|---|---|
| E-1 | posting | `app/cbl/CBTRN02C.cbl:2-5`; `app/cbl/CBTRN02C.cbl:22-24` | `708f3cadc555acab63f11e2f3238f5372ac7180e6b01197bf960d96bf0d2e83f` | The header describes posting records from a daily transaction file; `PROGRAM-ID` is `CBTRN02C`. The header is a source comment, not an execution finding. |
| E-2 | interest | `app/cbl/CBACT04C.cbl:2-5`; `app/cbl/CBACT04C.cbl:22-24` | `5084bb8b0c9a0f0199f737487ae1863f12e43cabbdc459a62b6b67bedc683cc4` | The header describes an interest calculator; `PROGRAM-ID` is `CBACT04C`. Generation-related statements are separately recorded below. |
| E-3 | reporting | `app/cbl/CBTRN03C.cbl:2-5`; `app/cbl/CBTRN03C.cbl:22-24` | `8691e625502b7efcfd7ba4ae61797132e7b68f3fd5fedcdcc7dd6488f6871eef` | The header describes printing the transaction detail report; `PROGRAM-ID` is `CBTRN03C`. |

### 2.2 Structural Characteristics

| ID | Track(s) | Full anchor | File SHA-256 | Documentary observation |
|---|---|---|---|---|
| E-4 | posting | `app/cbl/CBTRN02C.cbl:29-97`; `app/cbl/CBTRN02C.cbl:102-129`; `app/cbl/CBTRN02C.cbl:176-190` | `708f3cadc555acab63f11e2f3238f5372ac7180e6b01197bf960d96bf0d2e83f` | `DALYTRAN-FILE` and `DALYREJS-FILE` are declared sequential; transaction, xref, account, and category-balance files are indexed with random access. COPY statements name `CVTRA06Y`, `CVTRA05Y`, `CVACT03Y`, `CVACT01Y`, and `CVTRA01Y`. Reject storage contains 350-character transaction data and an 80-character trailer; the trailer separately declares a four-digit reason and 76-character description. Counters start at zero and the category-create flag at `'N'`. |
| E-5 | interest | `app/cbl/CBACT04C.cbl:28-92`; `app/cbl/CBACT04C.cbl:97-120`; `app/cbl/CBACT04C.cbl:166-180` | `5084bb8b0c9a0f0199f737487ae1863f12e43cabbdc459a62b6b67bedc683cc4` | Category balances are indexed/sequential; xref, account, and disclosure files are indexed/random; transaction output is sequential. Xref declares an alternate account key. COPY statements name `CVTRA01Y`, `CVACT03Y`, `CVTRA02Y`, `CVACT01Y`, and `CVTRA05Y`. Working storage declares two `S9(09)V99` interest fields, first-time and last-account fields, and a six-digit suffix initialized to zero. Linkage declares a binary length and ten-character `PARM-DATE`; the procedure uses `EXTERNAL-PARMS`. |
| E-6 | reporting | `app/cbl/CBTRN03C.cbl:29-88`; `app/cbl/CBTRN03C.cbl:93-137` | `8691e625502b7efcfd7ba4ae61797132e7b68f3fd5fedcdcc7dd6488f6871eef` | Transaction, report, and date-parameter files are sequential; xref, transaction-type, and category files are indexed/random. Report and date-file records are declared as 133 and 80 characters. COPY statements name `CVTRA05Y`, `CVACT03Y`, `CVTRA03Y`, `CVTRA04Y`, and `CVTRA07Y`. Working storage declares two ten-character date fields separated by one character, page size 20, zero-initialized counters/totals, and a space-initialized current-card field. |

### 2.3 Primary Evidence Ownership

| Track | Primary statement owner | Supporting documentary owners |
|---|---|---|
| posting | `app/cbl/CBTRN02C.cbl` — E-1, E-4, E-7–E-11 | Posting job E-29; applicable copybooks E-20–E-22, E-26–E-27 |
| interest | `app/cbl/CBACT04C.cbl` — E-2, E-5, E-12–E-15 | Interest job E-30; applicable copybooks E-20–E-23, E-26 |
| reporting | `app/cbl/CBTRN03C.cbl` — E-3, E-6, E-16–E-19 | Reporting job E-31; applicable copybooks E-21, E-24–E-26, E-28; procedure E-34 |

Operational-document references E-32–E-34 provide additional resource and instruction context. They do not transfer ownership of COBOL statements or prove that a particular schedule has run.

## Section 3: Operation Branch Evidence

### 3.1 Posting

| ID | Track(s) | Full anchor | File SHA-256 | Documentary observation |
|---|---|---|---|---|
| E-7 | posting | `app/cbl/CBTRN02C.cbl:193-234`; `app/cbl/CBTRN02C.cbl:345-378` | `708f3cadc555acab63f11e2f3238f5372ac7180e6b01197bf960d96bf0d2e83f` | The main procedure lists six open paragraphs, then a loop reading daily transactions. For a non-EOF record it increments the transaction count, clears the reason/description, and performs `1500-VALIDATE-TRAN`. Reason zero selects posting; otherwise the source increments the reject count and performs reject writing. After six close calls, it displays both counters and conditionally moves 4 to `RETURN-CODE` when reject count exceeds zero. The read paragraph maps status `'10'` to `APPL-EOF` and sets the EOF flag. |
| E-8 | posting | `app/cbl/CBTRN02C.cbl:380-422` | `708f3cadc555acab63f11e2f3238f5372ac7180e6b01197bf960d96bf0d2e83f` | Xref lookup uses `DALYTRAN-CARD-NUM`; its `INVALID KEY` branch assigns reason 100. Account lookup uses `XREF-ACCT-ID`; its invalid-key branch assigns 101. The non-invalid branch computes `ACCT-CURR-CYC-CREDIT - ACCT-CURR-CYC-DEBIT + DALYTRAN-AMT`, compares it with `ACCT-CREDIT-LIMIT`, and assigns 102 in the alternative branch. A subsequent, separate comparison uses `ACCT-EXPIRAION-DATE` and `DALYTRAN-ORIG-TS (1:10)`, with reason 103 in its alternative branch. The source spelling `EXPIRAION` is retained. |
| E-9 | posting | `app/cbl/CBTRN02C.cbl:424-465`; `app/cbl/CBTRN02C.cbl:692-705` | `708f3cadc555acab63f11e2f3238f5372ac7180e6b01197bf960d96bf0d2e83f` | The posting paragraph moves daily fields to transaction fields, calls timestamp construction, then lists category update, account update, and transaction write in that textual order. Timestamp construction uses `FUNCTION CURRENT-DATE`. Reject writing moves the daily record and trailer into reject storage, writes it, and routes non-success status to status display and the abend paragraph. |
| E-10 | posting | `app/cbl/CBTRN02C.cbl:467-579` | `708f3cadc555acab63f11e2f3238f5372ac7180e6b01197bf960d96bf0d2e83f` | Category lookup builds account/type/category key fields. Its invalid-key branch sets the create flag; the status check explicitly lists `'00'` and `'23'`. The create paragraph initializes a record, moves key fields, adds the amount, and writes; the update paragraph adds the amount and rewrites. Account update adds the amount to current balance and, according to an `>= 0` comparison, to cycle credit or cycle debit. Its rewrite invalid-key branch assigns reason 109. Transaction writing is a separate paragraph with status checking and an abend call path. |
| E-11 | posting | `app/cbl/CBTRN02C.cbl:236-343`; `app/cbl/CBTRN02C.cbl:582-690`; `app/cbl/CBTRN02C.cbl:707-727` | `708f3cadc555acab63f11e2f3238f5372ac7180e6b01197bf960d96bf0d2e83f` | Open statements specify input daily/xref files, output transaction/reject files, and I-O account/category files. Open and close routines contain status comparisons and error paths. In the reject-close error branch, the displayed label names daily rejects but the moved status is `XREFFILE-STATUS`. The abend paragraph moves 999 to `ABCODE`, zero to `TIMING`, and calls `CEE3ABD`; its implementation is not supplied. |

These are statement and branch observations, not normalized rejection rules. In particular, E-8 and E-10 retain distinct assignment sites for reasons 100–103 and 109 without asserting a complete outcome taxonomy.

### 3.2 Interest Transaction Generation

| ID | Track(s) | Full anchor | File SHA-256 | Documentary observation |
|---|---|---|---|---|
| E-12 | interest | `app/cbl/CBACT04C.cbl:180-232`; `app/cbl/CBACT04C.cbl:325-370` | `5084bb8b0c9a0f0199f737487ae1863f12e43cabbdc459a62b6b67bedc683cc4` | The main procedure lists five opens and a category-read loop. On a changed account field it conditionally performs account update, clears total interest, sets last-account/key fields, and performs account/xref reads. It builds disclosure-key fields and conditionally performs interest and fee paragraphs when `DIS-INT-RATE NOT = 0`. The outer `ELSE` contains another account-update call; its placement is retained without claiming final-account execution. The read paragraph sets EOF on status `'10'`. Account update adds total interest, zeroes both cycle fields, and rewrites the account record with status handling. |
| E-13 | interest | `app/cbl/CBACT04C.cbl:372-460` | `5084bb8b0c9a0f0199f737487ae1863f12e43cabbdc459a62b6b67bedc683cc4` | Account and xref reads contain invalid-key messages followed by status handling; xref explicitly reads by `FD-XREF-ACCT-ID`. Disclosure lookup accepts status text `'00'` or `'23'` in its initial check. On `'23'`, it moves `'DEFAULT'` to the group key and performs a second disclosure read. The second-read paragraph accepts `'00'` and otherwise routes to status display and abend. |
| E-14 | interest | `app/cbl/CBACT04C.cbl:462-520`; `app/cbl/CBACT04C.cbl:613-626` | `5084bb8b0c9a0f0199f737487ae1863f12e43cabbdc459a62b6b67bedc683cc4` | The source contains `COMPUTE WS-MONTHLY-INT` with expression `( TRAN-CAT-BAL * DIS-INT-RATE) / 1200`, adds the result to total interest, and performs transaction writing. The write paragraph increments the suffix; strings `PARM-DATE` and suffix into `TRAN-ID`; assigns literals `'01'`, `'05'`, and `'System'`; builds a description; moves amount/card fields; fills merchant fields with zero/spaces; and assigns constructed current-date timestamps to both timestamp fields before writing. `1400-COMPUTE-FEES` contains the comment `To be implemented` followed by `EXIT`. |
| E-15 | interest | `app/cbl/CBACT04C.cbl:234-323`; `app/cbl/CBACT04C.cbl:522-611`; `app/cbl/CBACT04C.cbl:628-648` | `5084bb8b0c9a0f0199f737487ae1863f12e43cabbdc459a62b6b67bedc683cc4` | Opens specify input category/xref/disclosure files, I-O account file, and output transaction file. Five close paragraphs contain status handling. The disclosure-open error message names `DALY REJECTS FILE`, while the moved status is `DISCGRP-STATUS`. The abend paragraph calls `CEE3ABD` with code 999 and timing zero. |

The literal arithmetic in E-14 is recorded without assigning rate units, rounding obligations, billing-period meaning, or guarantees about final-account persistence.

### 3.3 Transaction Reporting

| ID | Track(s) | Full anchor | File SHA-256 | Documentary observation |
|---|---|---|---|---|
| E-16 | reporting | `app/cbl/CBTRN03C.cbl:159-243`; `app/cbl/CBTRN03C.cbl:248-272` | `8691e625502b7efcfd7ba4ae61797132e7b68f3fd5fedcdcc7dd6488f6871eef` | The main procedure opens six files and reads date parameters before its transaction loop. Following a transaction read, the source compares the first ten timestamp characters with start/end dates; its alternative uses `NEXT SENTENCE`. A subsequent non-EOF branch compares current card with transaction card, conditionally writes account totals, sets card fields, performs xref/type/category lookups, and performs report writing. Its EOF alternative adds `TRAN-AMT` to page/account totals and calls page/grand-total paragraphs. Both read routines map status `'10'` to EOF. |
| E-17 | reporting | `app/cbl/CBTRN03C.cbl:274-341` | `8691e625502b7efcfd7ba4ae61797132e7b68f3fd5fedcdcc7dd6488f6871eef` | First-time report writing sets header dates and performs header writing. A `FUNCTION MOD(WS-LINE-COUNTER, WS-PAGE-SIZE) = 0` comparison selects page totals and headers. The paragraph adds the amount to page/account totals and performs detail writing. Page-total writing adds page total to grand total and resets page total; account-total writing resets account total. Header and total paragraphs contain separate line-counter increments. |
| E-18 | reporting | `app/cbl/CBTRN03C.cbl:343-374`; `app/cbl/CBTRN03C.cbl:484-512` | `8691e625502b7efcfd7ba4ae61797132e7b68f3fd5fedcdcc7dd6488f6871eef` | Detail writing initializes report storage, moves transaction ID, xref account ID, type/category codes and descriptions, source, and amount, then performs record writing and increments the line counter. Report-write failure routes to status display and abend. Each lookup paragraph has an invalid-key branch that displays its key, moves 23 to `IO-STATUS`, and performs status display and abend. |
| E-19 | reporting | `app/cbl/CBTRN03C.cbl:376-482`; `app/cbl/CBTRN03C.cbl:514-621`; `app/cbl/CBTRN03C.cbl:626-646` | `8691e625502b7efcfd7ba4ae61797132e7b68f3fd5fedcdcc7dd6488f6871eef` | Opens specify input transaction/xref/type/category/date files and output report file. Each has a corresponding close paragraph and status handling. The abend paragraph calls `CEE3ABD` with code 999 and timing zero; status formatting is separately implemented in `9910-DISPLAY-IO-STATUS`. |

Date filtering, EOF handling, grouping, and totals remain separately identifiable observations. No report correctness or final-total outcome is asserted.

### 3.4 Relevant Behavior Inventory Matrix

| Operation / rule / effect candidate | Evidence or ambiguity | Observed behavior summary | Why relevant | Downstream status |
|---|---|---|---|---|
| posting: input loop and branch selection | E-7 | Read, reset reason, lookup, post/reject branch, counters and conditional return-code assignment | operation / ordering | Inventory only; enrich in Stage 4 |
| posting: lookup and comparison sites | E-8; A-9 | Card/account lookup and separate amount/date comparisons | rule candidate / rejection | Inventory only; enrich in Stage 4 |
| posting: ordered write sites | E-9–E-11; A-10 | Category operation, account rewrite, transaction write; separate reject path | state / failure | Inventory only; enrich in Stage 4 |
| interest: account transition and EOF sites | E-12; A-11 | Account-change branch, total reset, read-driven EOF and outer alternative | ordering / state | Inventory only; enrich in Stage 4 |
| interest: disclosure fallback | E-13 | Initial and default-group read sites | dependency / failure | Inventory only; enrich in Stage 4 |
| interest: arithmetic and generated record | E-14; A-12 | Literal expression, accumulator, ID construction, field assignments and write | operation / output | Inventory only; enrich in Stage 4 |
| interest: fee paragraph | E-14, E-30; A-13 | Job comment names fees; program paragraph contains placeholder comment and exit | scope / ambiguity | Inventory only; enrich in Stage 4 |
| reporting: dates and end of input | E-16, E-31; A-14 | Separate job/program date inputs; `NEXT SENTENCE`; EOF alternative | ordering / input | Inventory only; enrich in Stage 4 |
| reporting: grouping, pagination and totals | E-17–E-18, E-28; A-15 | Card comparison, account-labelled totals, line-count test, detail/total writes | output / state | Inventory only; enrich in Stage 4 |
| reporting: lookup and I/O failures | E-18–E-19 | Invalid-key and non-success paths reference abend | dependency / failure | Inventory only; enrich in Stage 4 |
| shared operational context | E-29–E-34; A-8, A-16 | Dataset literals, backup/combination/sort instructions and procedure reference | resource / sequence | Inventory only; enrich in Stage 4 |
| external abend reference | E-11, E-15, E-19; A-17 | Three programs reference unsupplied `CEE3ABD` | unavailable dependency | Inventory only; enrich in Stage 4 |

## Section 4: Data Access and State Evidence

### 4.1 Copybook Evidence

These entries record declarations, not canonical types or business meanings. Shared consuming tracks are explicitly listed.

| ID | Track(s) | Full anchor | File SHA-256 | Documentary observation |
|---|---|---|---|---|
| E-20 | posting, interest | `app/cpy/CVACT01Y.cpy:2-17` | `81a08bad15af5664326a6f0af3650f570821c4857ffdec3a6a39f91f07dca728` | `ACCOUNT-RECORD` declares an eleven-digit ID, status, signed balance/limit/cycle fields with `S9(10)V99`, date/ZIP/group character fields, and filler. The header states `RECLN 300`. |
| E-21 | posting, interest, reporting | `app/cpy/CVACT03Y.cpy:2-8` | `ffc6079e09b28739e154bf6c1e1c36d408209faa91f6cf7008078dc596a1c370` | `CARD-XREF-RECORD` declares card `X(16)`, customer `9(09)`, account `9(11)`, and filler `X(14)`; the header states `RECLN 50`. |
| E-22 | posting, interest | `app/cpy/CVTRA01Y.cpy:2-10` | `50637f13692c89b17a2fc60d249dc54e9eb3569d933afca3cdcf65b491a9d5ba` | Category-balance storage declares account/type/category key fields and `TRAN-CAT-BAL PIC S9(09)V99`; the header states `RECLN = 50`. |
| E-23 | interest | `app/cpy/CVTRA02Y.cpy:2-10` | `7828fae489c59944b4310e223028a8d3a525ccf4ead113c062bcaff04b52bf9c` | Disclosure storage declares group/type/category key fields and `DIS-INT-RATE PIC S9(04)V99`; the header states `RECLN = 50`. |
| E-24 | reporting | `app/cpy/CVTRA03Y.cpy:2-7` | `fb15dbc4a6924cbddce0704932f9e61c067ac10004cd00839dff0ed7c7bb0667` | Transaction-type storage declares a two-character type and 50-character description with filler; the header states `RECLN = 60`. |
| E-25 | reporting | `app/cpy/CVTRA04Y.cpy:2-9` | `89803bc13a06347e1f3d8a599a5383b87235b203dce9f18a486bc233186479f8` | Category storage declares two-character type, four-digit category, and 50-character description with filler; the header states `RECLN = 60`. |
| E-26 | posting, interest, reporting | `app/cpy/CVTRA05Y.cpy:2-18` | `d7bde0e78ff608497087b9909c889ed39e347269f964bda767b92b547fbb5fec` | Transaction storage declares ID `X(16)`, type `X(02)`, category `9(04)`, source, description, amount `S9(09)V99`, merchant fields, card `X(16)`, two `X(26)` timestamps, and filler. The header states `RECLN = 350`. |
| E-27 | posting | `app/cpy/CVTRA06Y.cpy:2-18` | `c5c69f1b86c5a10156d3c5881d7cf387e6b925aae32825360f85bf4056a554a1` | Daily-transaction storage separately declares `DALYTRAN-` fields including ID, type, category, amount, merchant/card fields, and two timestamps. The header states `RECLN = 350`; this entry does not merge it with E-26. |
| E-28 | reporting | `app/cpy/CVTRA07Y.cpy:4-66` | `72ba597b1a40e1e6cf908e15da9e6a818a0ab899ef1d27d15edeb074963102fa` | Report declarations contain name/date headers, detail fields, column labels, a 133-character separator, and page/account/grand-total groups. Detail descriptions are declared as 15 and 29 characters. Detail amount uses `-ZZZ,ZZZ,ZZZ.ZZ`; total fields use `+ZZZ,ZZZ,ZZZ.ZZ`. |

### 4.2 Operational-Document Evidence

| ID | Track(s) | Full anchor | File SHA-256 | Documentary observation |
|---|---|---|---|---|
| E-29 | posting | `app/jcl/POSTTRAN.jcl:20-42` | `ecff62c691e6ce101de08690e72ec065bc98bd845744ddf914899097d37c9191` | `STEP15` names `CBTRN02C`. DD statements name transaction KSDS, daily PS, card-xref KSDS, account KSDS, category-balance KSDS, and a new `DALYREJS(+1)` dataset with `LRECL=430`. Comments describe daily processing and master/category updates. |
| E-30 | interest | `app/jcl/INTCALC.jcl:20-41` | `61afa664a807558e58213641d9f3317ab3b354a350c4c1536a630897d194d275` | The comment names interest and fees. `STEP15` names `CBACT04C` with `PARM='2022071800'`. DD statements name category balances, xref KSDS and alternate-index path, accounts, disclosure groups, and new `SYSTRAN(+1)` output with `LRECL=350`. |
| E-31 | reporting | `app/jcl/TRANREPT.jcl:19-80` | `7d8fc0777e6b9fb1c62aee6b4b10a67d127057c84b92203c7152f230b3db9571` | The document names `REPROC`, overrides its input/output DDs, and contains SORT instructions with card position 263/length 16/`ZD` and date position 305/length 10/`CH`. Literal date bounds are `2022-01-01` and `2022-07-06`. It names `CBTRN03C`, transaction daily input, xref/type/category datasets, separate `DATEPARM`, and report output with `LRECL=133`. Lines 23 and 37 both use step label `STEP05R`. |
| E-32 | posting, interest | `app/jcl/COMBTRAN.jcl:20-48` | `ab60da6cfdc8c4ec66c8b950540553bf35e91dc1e61a1dd4ada5bb888011c85c` | SORT input lists `TRANSACT.BKUP(0)` and `SYSTRAN(0)`, with `TRAN-ID,1,16,CH` and ascending sort. Output names `TRANSACT.COMBINED(+1)`. A later IDCAMS instruction specifies `REPRO` from that combined dataset to `TRANSACT.VSAM.KSDS`. Consuming tracks concern the transaction-master and generated-transaction context, not proven execution order. |
| E-33 | posting, interest, reporting | `app/jcl/TRANBKP.jcl:19-67` | `457cd00d14a1d9ac9983d92212541df3456e8428862b97cf10bab7249b9e6183` | The document names `REPROC`, transaction KSDS input, and `TRANSACT.BKUP(+1)` output with `LRECL=350`. Subsequent IDCAMS text contains deletion of transaction cluster/AIX, conditional `MAXCC` assignments, and cluster definition with `KEYS(16 0)` and `RECORDSIZE(350 350)`. Shared attribution records transaction-resource context only. |
| E-34 | posting, interest, reporting | `app/proc/REPROC.prc:19-29` | `4562039d1c7b90f05cc946dd1cd1cb93571bb279740c5c9777acfa3ea23fbc9f` | The comment names a load/unload utility. `PRC001` names IDCAMS; `FILEIN` and `FILEOUT` default to `NULLFILE`; `SYSIN` references `&CNTLLIB(REPROCT)`. That member body is not supplied. Reporting references this procedure in E-31; shared transaction-backup context references it in E-33. |
| E-35 | posting, interest, reporting | `LICENSE:2-6`; `LICENSE:90-129`; `LICENSE:144-164` | `09e8a9bcec8067104652c168685ab0931e7868f9c8284b66f5ae6edae5f1130b` | The document identifies Apache License Version 2.0, contains redistribution conditions, and contains warranty/liability sections. This is shared documentary context, not legal clearance or behavioral evidence. |

All 19 allowlisted files have a documentary entry. That inventory accounting is not a claim of behavioral completeness.

### 4.3 Persistent Resources and Processing Sequence

Rows below retain source-local resource names. Dataset literals are documentary bindings, not confirmation of live resource identity.

| Resource / sequence edge | Read/write/order observation | Evidence anchors | Unknowns |
|---|---|---|---|
| posting `DALYTRAN-FILE` | Sequential input declaration, input open, read loop and EOF handling; job names daily PS | E-4, E-7, E-11, E-29 | Actual records, input order and lifecycle: A-2, A-4 |
| posting `TRANSACT-FILE` | Indexed/random declaration; output open; write after category/account calls | E-4, E-9–E-11, E-29 | Open effects, existing-data handling and partial persistence: A-10 |
| posting `DALYREJS-FILE` | Output open; separate record/trailer write | E-4, E-7, E-9, E-11, E-29 | Persisted reject output and interruption effects: A-4 |
| posting `ACCOUNT-FILE` | I-O open, lookup and rewrite | E-8, E-10–E-11, E-20, E-29 | Reason 109 handling and durability: A-9, A-10 |
| posting `TCATBAL-FILE` | I-O open, lookup, create/write or add/rewrite | E-10–E-11, E-22, E-29 | Persistence before subsequent errors: A-10 |
| posting `XREF-FILE` | Input open; card-key lookup | E-8, E-11, E-21, E-29 | Actual lookup contents and non-key failures: A-2, A-4 |
| interest `TCATBAL-FILE` | Indexed/sequential input and read-driven EOF | E-5, E-12, E-15, E-22, E-30 | Final-account handling: A-11 |
| interest `ACCOUNT-FILE` | Random lookup, I-O open, total addition and cycle-field reset before rewrite | E-12–E-13, E-15, E-20, E-30 | Final rewrite occurrence and persistence: A-11, A-4 |
| interest `XREF-FILE` | Alternate account key declared and explicitly used by read | E-5, E-13, E-15, E-21, E-30 | Actual alternate-key binding/multiplicity: A-2, A-4 |
| interest `DISCGRP-FILE` | Input reads, then default-group read on status `'23'` | E-13, E-15, E-23, E-30 | Rate contents and units: A-12 |
| interest `TRANSACT-FILE` | Sequential output open; constructed record write; job names `SYSTRAN(+1)` | E-14–E-15, E-26, E-30 | Identifier lifetime, arithmetic representation and interrupted writes: A-12, A-4 |
| reporting `TRANSACT-FILE` | Sequential input, timestamp comparison and read-driven EOF | E-6, E-16, E-19, E-26, E-31 | Date/EOF interactions: A-14 |
| reporting `XREF-FILE` | Input card-key lookup selected by current-card comparison | E-16, E-18–E-19, E-21, E-31 | Grouping meaning and actual records: A-15 |
| reporting `TRANTYPE-FILE` | Input lookup; description moved to detail field | E-18–E-19, E-24, E-28, E-31 | Data contents and representation effects: A-2, A-15 |
| reporting `TRANCATG-FILE` | Input composite-key lookup; description moved to detail field | E-18–E-19, E-25, E-28, E-31 | Data contents and representation effects: A-2, A-15 |
| reporting `DATE-PARMS-FILE` | Separate input open/read and two date fields | E-6, E-16, E-19, E-31 | Unsupplied contents and relation to SORT dates: A-14 |
| reporting `REPORT-FILE` | Output open; separate headers, details and total records | E-17–E-19, E-28, E-31 | Final totals, empty input and interrupted output: A-14, A-15 |
| Transaction backup / combined intermediates | JCL lists backup, sort/combination, deletion/definition and REPRO instructions | E-31–E-34 | Cross-job schedule, generation resolution and missing control member: A-8, A-16 |

No row establishes atomicity, safe repetition, rollback, restart isolation, or a completed persistence boundary. Those properties remain unknown under the documentary-only scope.

## Section 5: Complexity Factor Documentation

| Factor | Documentary basis | Evidence boundary |
|---|---|---|
| Multiple resources per track | E-4–E-6, E-11, E-15, E-19 | File declarations and access statements are visible; deployed resources are not observed. |
| Write ordering and failure sites | E-9–E-15 | Separate write/rewrite sites and error branches are visible; durable partial effects are not measured. |
| Account-transition and EOF structure | E-12, E-16–E-17 | Source placement is preserved rather than replaced with a presumed finalization algorithm. |
| Numeric representation differences | E-5, E-20, E-22–E-23, E-26, E-28 | PIC declarations and literal arithmetic are visible; business units and required rounding are not assigned. |
| Shared copybooks with distinct file contexts | E-4–E-6, E-20–E-27 | COPY names support source attribution, not a merged canonical meaning. |
| Separate operational parameters | E-5–E-6, E-30–E-31 | Interest linkage, SORT literals and reporting date-file fields remain separate inputs. |
| Comments differing from nearby statements | E-11, E-14–E-15, E-30 | Fee placeholder and error-label mismatches remain documentary observations, not corrected text. |
| External references and operational limits | E-11, E-15, E-19, E-31–E-34 | Missing control/runtime bodies and duplicate job-step labels prevent assumed executability. |

### AI Assistance and Provenance

AI assistance in this artifact is limited to locating supplied anchors, summarizing source structures, organizing evidence, and registering uncertainty.

No tools, external retrieval, compilation, execution, checksum computation, or source modification were performed. No model-generated expected outcomes are included. The supplied initialization timestamps are metadata, not measured generation timing. Requested/reported model identifiers for this generation, provider usage, token counts, monetary cost, and human effort measurements are unavailable here.

The exact request, response, input pins, and subsequent human corrections should be retained separately in run records. This artifact does not certify persistence or exposure history beyond the supplied context.

## Section 6: Completeness Gate and Stage 4 Entry Condition

### 6.1 Ambiguity Register

Inherited identifiers remain stable. New ambiguities begin at `A-9`.

| ID | Description | Anchors / authority | Candidate interpretations or handling | Blocking? | Status |
|---|---|---|---|---|---|
| A-1 | Final capability cohesion and boundaries remain unsettled. | Approved Stage 2-r2; E-1–E-6 | Keep the ratified portfolio and source ownership separate from final business decomposition. | Blocks final boundary claims | Open |
| A-2 | Inventory completeness and dependency closure are unknown. | Upstream; E-29–E-34 | Allowlist availability is not complete application/environment availability. | Blocks completeness/executability claims | Open |
| A-3 | Original encoding question requires scoped treatment. | Upstream; supplied representation descriptor | UTF-8 is explicitly supplied for this representation; no deployed encoding claim follows. | Conditional for byte-sensitive work | Partially addressed |
| A-4 | Runtime state, persistence, restart and failure properties remain unknown. | Upstream; Section 4.3 | Documentary access statements do not settle actual effects or repetition safety. | Blocks runtime guarantees | Open |
| A-5 | Broader participant exposure is not documented. | Upstream | Preserve existing disclosures; do not assert independent or clean experimental exposure. | Conditional for research claims | Open |
| A-6 | Licensing review requirements remain unresolved. | E-35 | Visible license text is not legal clearance. | Conditional on later activity | Open |
| A-7 | Stage 3 layout and evidence namespace required authorization. | Stage 2-r2 authorization | One artifact, three tracks, and one run-wide E-n sequence are explicitly supplied. | No remaining layout blocker | Addressed by supplied authorization |
| A-8 | Relationships and required schedule among tracks remain unsettled. | E-29–E-34 | Matching dataset literals provide context; required cross-job chronology remains unestablished. | Blocks cycle-sequence claims | Open |
| A-9 | Posting reason precedence and post-rewrite reason handling require interpretation. | E-7–E-10 | Preserve separate assignment sites and textual call order; do not assume all reasons enter the same reject path. | Requires disposition before affected semantic claims | Open |
| A-10 | Posting output-open and multi-resource write effects are unresolved. | E-9–E-11, E-29 | Do not equate the job’s master-update comment with preservation of existing data or atomic updates. | Requires disposition before persistence claims | Open |
| A-11 | Interest final-account handling is not established by the paragraph name or outer alternative. | E-12 | Retain loop/read/EOF placement; do not assume an unconditional final rewrite. | Requires disposition before core finalization claims | Open |
| A-12 | Interest units, numeric handling, and generated-ID lifetime are unsettled. | E-5, E-14, E-20, E-22–E-23, E-26, E-30 | Record expression and declarations without inventing units, rounding policy, uniqueness or repetition safety. | Requires disposition before affected semantic claims | Open |
| A-13 | Fee scope comment and placeholder paragraph differ in documentary detail. | E-14, E-30 | Retain both; do not invent fee calculation or conclude application-wide fee absence. | Blocks a fee-computation claim | Open |
| A-14 | Reporting date sources, `NEXT SENTENCE`, and EOF-path data use need interpretation. | E-16, E-31 | SORT literals and unsupplied DATEPARM contents need not agree; no empty-input or EOF outcome is assumed. | Requires disposition before core filtering/finalization claims | Open |
| A-15 | Card-change grouping, account-labelled totals and pagination effects need interpretation. | E-6, E-16–E-18, E-24–E-28 | Do not equate a card boundary with an account boundary or infer final-total correctness from labels. | Requires disposition before reporting obligations | Open |
| A-16 | Operational-document executability is unestablished. | E-31, E-34 | Duplicate `STEP05R` labels and unsupplied `REPROCT` remain explicit; neither is repaired or expanded here. | Blocks execution-chain claims | Open |
| A-17 | External abend routine behavior is unavailable. | E-11, E-15, E-19 | Only call sites and arguments are evidenced; termination and persistence consequences remain unknown. | Blocks claims relying on external routine behavior | Open |

### Review Gaps

Earlier gap identifiers remain historical upstream records. Supplied approvals, version pins and Stage 3 authorization provide the entry basis; this draft does not rewrite those records.

| ID | Classification | Gap | Required external handling |
|---|---|---|---|
| G-7 | Blocking for Stage 3 completion | No human review of this concrete Stage 3 artifact is recorded. | Review each mandatory track and the shared entries; retain the exact reviewed version and decision. |
| G-8 | Blocking for gate completion | The prescribed source-anchor check is not performed in this documentary response. | Handle the framework’s mechanical-anchor requirement separately; its result cannot substitute for substantive review. |
| G-9 | Blocking for unrestricted Stage 4 entry | Core control-flow and resource ambiguities remain unresolved or undisposed. | Record which uncertainties block semantic work and any explicit, scoped human disposition. |
| G-10 | Blocking for review finalization | This response has no persisted output digest or bound Stage 3 review record. | Preserve and pin the exact artifact and input versions before recording review. |

### 6.2 Completeness Conditions

- [ ] All constituent operations evidenced with anchors
- [ ] Data access and state model evidenced
- [ ] Every claim classified as evidence / inference / ambiguity
- [ ] Complexity factors documented
- [ ] Relevant behavior inventory created without downstream endpoint/type/contract conclusions
- [ ] Ambiguity register current, blocking status assessed
- [ ] Human review outcome: Approve

The final checklist item is preserved template text and remains **unchecked**. It is not an approval decision.

Additional local review conditions:

- [ ] Posting, interest, and reporting are each reviewed separately.
- [ ] Shared evidence explicitly identifies every consuming track.
- [ ] E-n identities are reconciled against full paths, original-file hashes, and stable numbered ranges.
- [ ] Source comments, declarations, statements, and operational instructions are distinguished from executed outcomes.
- [ ] Missing dependencies and uncertain EOF/write effects remain explicit.
- [ ] No track is omitted, made optional, or closed by another track’s progress.
- [ ] Exact upstream and output versions are retained without rewriting historical text.

### 6.3 Stage 4 Entry Condition

**Stage 4 may begin** only when the conditions above hold and no blocking ambiguity prevents semantic reconstruction of the core rule set.

**Current Stage 3 human approval: `false`. Completeness gate passed: `false`.**

This specification grants no gate approval and no Stage 4 authorization. Human review and any subsequent authorization remain external.