# Complementary INTEREST essential cases

Cases executed: 2
All local checks passed: True

| Obligation | Status | Cases | Evidence |
|---|---:|---|---|
| INTCALC-OBL-001 | covered | rates-specific-default-zero, single-final-eof | TCATBALF before/after pins |
| INTCALC-OBL-002 | covered | rates-specific-default-zero, single-final-eof | ACCTFILE qualified dump before/after |
| INTCALC-OBL-003 | covered | rates-specific-default-zero, single-final-eof | XREFFILE.1 sidecar + transaction cardReference |
| INTCALC-OBL-004 | covered | rates-specific-default-zero | STANDARD/ZERORATE/DEFAULT DISCGRP records |
| INTCALC-OBL-005 | covered | rates-specific-default-zero, single-final-eof | independent Decimal expected vs TRANSACT amount |
| INTCALC-OBL-006 | covered | rates-specific-default-zero, single-final-eof | 350-byte TRANSACT record provenance |
| INTCALC-OBL-007 | covered | rates-specific-default-zero | ZERORATE input with no matching output transaction |
| INTCALC-OBL-008 | covered | rates-specific-default-zero, single-final-eof | final account account-delta zero despite TRANSACT output |

## Omissions
- Local P3 technical cases only; not official campaign fixtures or proof of all 25 checker obligations.
- EOF final-account behavior records source-supported limitation, not desired finance behavior.
