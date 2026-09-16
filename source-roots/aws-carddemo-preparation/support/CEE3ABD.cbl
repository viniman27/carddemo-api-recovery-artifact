>>source format free
*> LOCAL EXPERIMENT SUPPORT. Not IBM Language Environment emulation.
*> Retains fatal termination and displays arguments, but no LE dump,
*> mainframe condition handling, or exact z/OS process status mapping.
identification division.
program-id. CEE3ABD.
data division.
linkage section.
01 abcode pic s9(9) binary.
01 timing pic s9(9) binary.
procedure division using abcode timing.
 display 'LOCAL-CEE3ABD CODE=' abcode ' TIMING=' timing upon syserr
 stop run returning 12.
