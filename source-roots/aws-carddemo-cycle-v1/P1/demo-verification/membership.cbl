       >>SOURCE FORMAT FREE
identification division.
program-id. PROBE-MEMBERSHIP.
data division.
working-storage section.
01 A PIC X VALUE "G".
01 B PIC 9(5)V99 VALUE 100.
01 RESULT-VALUE PIC 9(5)V99 VALUE 0.
procedure division.
call "MEMBERSHIP-DISCOUNT" using A B RESULT-VALUE
display RESULT-VALUE
stop run.
