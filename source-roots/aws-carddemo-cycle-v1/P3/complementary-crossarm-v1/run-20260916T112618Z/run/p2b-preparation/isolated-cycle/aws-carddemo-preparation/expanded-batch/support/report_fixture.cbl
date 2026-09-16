identification division. program-id. REPORT_FIXTURE.
environment division. input-output section. file-control.
  select XREF-FILE assign to CARDXREF organization indexed access sequential record key FD-XREF-CARD-NUM file status FS-XREF.
  select TRANTYPE-FILE assign to TRANTYPE organization indexed access random record key FD-TRAN-TYPE file status FS-TYPE.
  select TRANCATG-FILE assign to TRANCATG organization indexed access random record key FD-TRAN-CAT-KEY file status FS-CAT.
data division. file section.
  fd XREF-FILE. 01 FD-CARDXREF-REC. 05 FD-XREF-CARD-NUM pic x(16). 05 FD-XREF-DATA pic x(34).
  fd TRANTYPE-FILE. 01 FD-TRANTYPE-REC. 05 FD-TRAN-TYPE pic x(02). 05 FD-TRAN-DATA pic x(58).
  fd TRANCATG-FILE. 01 FD-TRAN-CAT-RECORD. 05 FD-TRAN-CAT-KEY. 10 FD-TRAN-TYPE-CD pic x(02). 10 FD-TRAN-CAT-CD pic 9(04). 05 FD-TRAN-CAT-DATA pic x(54).
working-storage section. 
>>source format fixed
       COPY CVACT03Y.
       >>source format free
 
>>source format fixed
       COPY CVTRA03Y.
       >>source format free
 
>>source format fixed
       COPY CVTRA04Y.
       >>source format free
 01 FS-XREF pic xx. 01 FS-TYPE pic xx. 01 FS-CAT pic xx.
procedure division.
  open output XREF-FILE TRANTYPE-FILE TRANCATG-FILE
  move '4111111111111111' to XREF-CARD-NUM move 000000001 to XREF-CUST-ID move 00000000001 to XREF-ACCT-ID move CARD-XREF-RECORD to FD-CARDXREF-REC write FD-CARDXREF-REC
  move '01' to TRAN-TYPE move 'System transaction' to TRAN-TYPE-DESC move TRAN-TYPE-RECORD to FD-TRANTYPE-REC write FD-TRANTYPE-REC
  move '01' to TRAN-TYPE-CD of TRAN-CAT-KEY move 0005 to TRAN-CAT-CD of TRAN-CAT-KEY move 'Interest charge' to TRAN-CAT-TYPE-DESC move TRAN-CAT-RECORD to FD-TRAN-CAT-RECORD write FD-TRAN-CAT-RECORD
  close XREF-FILE TRANTYPE-FILE TRANCATG-FILE stop run.
