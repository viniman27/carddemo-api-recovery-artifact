>>source format free
identification division.
program-id. SIGNPROBE.
data division.
working-storage section.
01 signed-number pic s9(09)v99.
01 raw-number redefines signed-number pic x(11).
procedure division.
move -1.20 to signed-number
display raw-number with no advancing
move -1.21 to signed-number
display raw-number with no advancing
move -1.22 to signed-number
display raw-number with no advancing
move -1.23 to signed-number
display raw-number with no advancing
move -1.24 to signed-number
display raw-number with no advancing
move -1.25 to signed-number
display raw-number with no advancing
move -1.26 to signed-number
display raw-number with no advancing
move -1.27 to signed-number
display raw-number with no advancing
move -1.28 to signed-number
display raw-number with no advancing
move -1.29 to signed-number
display raw-number with no advancing
move 0.00 to signed-number
display raw-number with no advancing
move 999999999.99 to signed-number
display raw-number with no advancing
move -999999999.99 to signed-number
display raw-number with no advancing
stop run.
