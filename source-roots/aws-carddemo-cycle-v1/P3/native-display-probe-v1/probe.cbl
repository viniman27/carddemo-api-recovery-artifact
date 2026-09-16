>>source format free
identification division.
program-id. NATIVE-DISPLAY-PROBE.
environment division.
input-output section.
file-control.
 select output-file assign to "native.bin"
 organization is sequential.
data division.
file section.
fd output-file.
01 output-record.
 02 amount-field pic s9(9)v99.
procedure division.
 open output output-file
 move -1.23 to amount-field
 write output-record
 close output-file
 stop run.
