>>source format free
identification division.
program-id. P2B_INTEREST_DRIVER.
environment division.
input-output section.
file-control.
    select parameter-file assign to PARMFILE
        organization sequential file status parameter-status.
data division.
file section.
fd parameter-file.
01 parameter-bytes pic x(10).
working-storage section.
01 parameter-status pic xx.
01 external-parms.
   05 parm-length pic s9(4) comp value 10.
   05 parm-value pic x(10).
procedure division.
    open input parameter-file
    if parameter-status not = '00'
        display 'P2B-PARAMETER-FAIL: open' upon syserr
        stop run returning 12
    end-if
    read parameter-file
    if parameter-status not = '00'
        display 'P2B-PARAMETER-FAIL: read' upon syserr
        stop run returning 12
    end-if
    move parameter-bytes to parm-value
    close parameter-file
    call 'CBACT04C' using external-parms
    stop run.
