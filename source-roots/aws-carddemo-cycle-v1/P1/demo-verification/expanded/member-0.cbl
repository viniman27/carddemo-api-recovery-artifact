       >>SOURCE FORMAT FREE
identification division.
program-id. PROBE.
data division.
working-storage section.
01 TIER-VALUE PIC X VALUE "G".
01 PURCHASE-VALUE PIC 9(5)V99 VALUE 0.
01 OUTPUT-VALUE PIC 9(5)V99 VALUE ZERO.
procedure division.
call "MEMBERSHIP-DISCOUNT" using TIER-VALUE PURCHASE-VALUE OUTPUT-VALUE
display OUTPUT-VALUE
stop run.
