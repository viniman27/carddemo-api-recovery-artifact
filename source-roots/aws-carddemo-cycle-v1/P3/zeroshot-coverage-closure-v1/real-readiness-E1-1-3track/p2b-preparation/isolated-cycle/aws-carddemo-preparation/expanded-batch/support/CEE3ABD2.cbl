>>source format free
identification division. program-id. CEE3ABD.
data division. linkage section.
01 abcode pic s9(9) binary. 01 timing pic s9(9) binary.
procedure division using abcode timing.
  display 'LOCAL-CEE3ABD/2 CODE=' abcode ' TIMING=' timing upon syserr
  stop run returning 12.
