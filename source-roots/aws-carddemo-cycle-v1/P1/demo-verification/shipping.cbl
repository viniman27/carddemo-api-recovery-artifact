       >>SOURCE FORMAT FREE
identification division.
program-id. PROBE-SHIPPING.
data division.
working-storage section.
01 A PIC 9(3)V99 VALUE 2.
01 B PIC X VALUE "A".
01 RESULT-VALUE PIC 9(5)V99 VALUE 0.
01 D PIC X VALUE SPACE.
procedure division.
call "SHIPPING-QUOTE" using A B RESULT-VALUE D
display RESULT-VALUE "|" D
stop run.
