>>source format free
identification division.
program-id. XREFALT.
environment division.
input-output section.
file-control.
 select xref-file assign to XREFFILE organization indexed access random
   record key xref-card-num alternate record key xref-acct-id
   file status fs.
data division.
file section.
fd xref-file.
01 xref-rec.
 05 xref-card-num pic x(16).
 05 xref-cust-id pic 9(09).
 05 xref-acct-id pic 9(11).
 05 xref-fill pic x(14).
working-storage section.
01 fs pic xx.
01 ws-mode pic x(8).
01 keyin pic x(32).
procedure division.
 accept ws-mode from environment 'LOOKUP_MODE'
 accept keyin from environment 'LOOKUP_KEY'
 open input xref-file
 display 'OPEN=' fs
 if fs not = '00' stop run returning 12 end-if
 evaluate function trim(ws-mode)
 when 'PRIMARY'
   move keyin(1:16) to xref-card-num
   read xref-file invalid key display 'MISS=' fs end-read
 when 'ALT'
   move keyin(1:11) to xref-acct-id
   read xref-file key is xref-acct-id invalid key display 'MISS=' fs end-read
 when other
   display 'BADMODE' stop run returning 12
 end-evaluate
 display 'READ=' fs ' CARD=' xref-card-num ' ACCT=' xref-acct-id
 close xref-file
 if fs = '00' stop run returning 0 else stop run returning 2 end-if.
