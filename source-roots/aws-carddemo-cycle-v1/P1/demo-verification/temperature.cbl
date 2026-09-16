       >>SOURCE FORMAT FREE
identification division.
program-id. PROBE-TEMPERATURE.
data division.
working-storage section.
01 A PIC S9(3)V99 VALUE 0.
01 B PIC S9(3)V99 VALUE 0.
procedure division.
call "CELSIUS-TO-FAHRENHEIT" using A B
display B
stop run.
