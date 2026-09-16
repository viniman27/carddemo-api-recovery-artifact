identification division.
program-id. FLUSHPROBE.
data division.
working-storage section.
01 sleep-seconds binary-long value 2.
procedure division.
    display "FLUSH-PROBE-READY".
    call "technical_sleep_seconds" using sleep-seconds.
    display "FLUSH-PROBE-NORMAL-END".
    stop run.
