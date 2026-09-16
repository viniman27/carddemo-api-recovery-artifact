
>>source format free
identification division.
program-id. P2B_INTEREST_DRIVER.
environment division.
input-output section.
file-control.
    select parameter-file assign to PARMFILE organization sequential file status parameter-status.
    select capture-file assign to LINKCAP organization sequential file status capture-status.
data division.
file section.
fd parameter-file.
01 parameter-bytes pic x(10).
fd capture-file.
01 capture-bytes pic x(12).
working-storage section.
01 parameter-status pic xx.
01 capture-status pic xx.
01 parameter-length-text pic x(16).
01 external-parms.
   05 parm-length pic s9(4) comp value 10.
   05 parm-value pic x(10).
procedure division.
    accept parameter-length-text from environment 'P2C_PARAMETER_LENGTH'
    if function trim(parameter-length-text) not = ''
        move function numval(function trim(parameter-length-text)) to parm-length
    end-if
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
    move external-parms to capture-bytes
    open output capture-file
    if capture-status = '00'
        write capture-bytes
        close capture-file
    else
        display 'P2C-LINKAGE-CAPTURE-FAIL: open' upon syserr
    end-if
    call 'CBACT04C' using external-parms
    stop run.
