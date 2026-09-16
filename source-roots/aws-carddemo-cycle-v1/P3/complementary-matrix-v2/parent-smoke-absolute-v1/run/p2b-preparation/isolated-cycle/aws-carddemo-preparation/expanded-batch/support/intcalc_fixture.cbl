identification division. program-id. INTCALC_FIXTURE.
environment division. input-output section. file-control.
  select TCATBAL-FILE assign to TCATBALF organization indexed access sequential record key FD-TRAN-CAT-KEY file status FS-TCAT.
  select XREF-FILE assign to XREFFILE organization indexed access sequential record key FD-XREF-CARD-NUM alternate record key FD-XREF-ACCT-ID file status FS-XREF.
  select ACCOUNT-FILE assign to ACCTFILE organization indexed access random record key FD-ACCT-ID file status FS-ACCT.
  select DISCGRP-FILE assign to DISCGRP organization indexed access random record key FD-DISCGRP-KEY file status FS-DISC.
data division. file section.
fd TCATBAL-FILE. 01 FD-TRAN-CAT-BAL-RECORD. 05 FD-TRAN-CAT-KEY. 10 FD-TRANCAT-ACCT-ID pic 9(11). 10 FD-TRANCAT-TYPE-CD pic x(02). 10 FD-TRANCAT-CD pic 9(04). 05 FD-FD-TRAN-CAT-DATA pic x(33).
fd XREF-FILE. 01 FD-XREFFILE-REC. 05 FD-XREF-CARD-NUM pic x(16). 05 FD-XREF-CUST-NUM pic 9(09). 05 FD-XREF-ACCT-ID pic 9(11). 05 FD-XREF-FILLER pic x(14).
fd DISCGRP-FILE. 01 FD-DISCGRP-REC. 05 FD-DISCGRP-KEY. 10 FD-DIS-ACCT-GROUP-ID pic x(10). 10 FD-DIS-TRAN-TYPE-CD pic x(02). 10 FD-DIS-TRAN-CAT-CD pic 9(04). 05 FD-DISCGRP-DATA pic x(34).
fd ACCOUNT-FILE. 01 FD-ACCTFILE-REC. 05 FD-ACCT-ID pic 9(11). 05 FD-ACCT-DATA pic x(289).
working-storage section.
  
>>source format fixed
       COPY CVTRA01Y.
       >>source format free
 
>>source format fixed
       COPY CVACT03Y.
       >>source format free
 
>>source format fixed
       COPY CVTRA02Y.
       >>source format free
 
>>source format fixed
       COPY CVACT01Y.
       >>source format free

  01 FS-TCAT pic xx. 01 FS-XREF pic xx. 01 FS-ACCT pic xx. 01 FS-DISC pic xx.
procedure division.
  open output TCATBAL-FILE XREF-FILE ACCOUNT-FILE DISCGRP-FILE
  move 00000000001 to TRANCAT-ACCT-ID move '01' to TRANCAT-TYPE-CD move 0005 to TRANCAT-CD move 10000.00 to TRAN-CAT-BAL move TRAN-CAT-BAL-RECORD to FD-TRAN-CAT-BAL-RECORD write FD-TRAN-CAT-BAL-RECORD
  move '4111111111111111' to FD-XREF-CARD-NUM move 000000001 to FD-XREF-CUST-NUM move 00000000001 to FD-XREF-ACCT-ID move spaces to FD-XREF-FILLER write FD-XREFFILE-REC
  move 00000000001 to ACCT-ID move 'Y' to ACCT-ACTIVE-STATUS move 500.00 to ACCT-CURR-BAL move 10000.00 to ACCT-CREDIT-LIMIT move 5000.00 to ACCT-CASH-CREDIT-LIMIT move '2020-01-01' to ACCT-OPEN-DATE move '2030-01-01' to ACCT-EXPIRAION-DATE move '2025-01-01' to ACCT-REISSUE-DATE move 0 to ACCT-CURR-CYC-CREDIT ACCT-CURR-CYC-DEBIT move '99999' to ACCT-ADDR-ZIP move 'STANDARD  ' to ACCT-GROUP-ID move ACCOUNT-RECORD to FD-ACCTFILE-REC write FD-ACCTFILE-REC
  move 'STANDARD  ' to DIS-ACCT-GROUP-ID move '01' to DIS-TRAN-TYPE-CD move 0005 to DIS-TRAN-CAT-CD move 12.00 to DIS-INT-RATE move DIS-GROUP-RECORD to FD-DISCGRP-REC write FD-DISCGRP-REC
  close TCATBAL-FILE XREF-FILE ACCOUNT-FILE DISCGRP-FILE stop run.
