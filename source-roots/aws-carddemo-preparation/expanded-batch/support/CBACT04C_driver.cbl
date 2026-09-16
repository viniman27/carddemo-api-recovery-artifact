>>source format free
identification division. program-id. CBACT04C_DRIVER.
data division. working-storage section.
01 external-parms.
  05 parm-length pic s9(4) comp value 10.
  05 parm-date pic x(10) value '2022071800'.
procedure division.
  call 'CBACT04C' using external-parms
  stop run.
