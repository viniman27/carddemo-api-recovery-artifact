       >>SOURCE FORMAT FREE
identification division.
program-id. PROBE.
data division.
working-storage section.
01 INPUT-VALUE PIC S9(3)V99 VALUE 0.
01 OUTPUT-VALUE PIC S9(3)V99 VALUE ZERO.
procedure division.
call "CELSIUS-TO-FAHRENHEIT" using INPUT-VALUE OUTPUT-VALUE
display OUTPUT-VALUE
stop run.
