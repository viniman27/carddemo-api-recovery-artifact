>>source format free
identification division. program-id. LOADIDX.
environment division. input-output section. file-control.
  select raw-file assign to RAW organization sequential file status fs.
  select idx-file assign to IDX organization indexed access sequential record key idx-key file status ix.
data division. file section.
fd raw-file. 01 raw-rec pic x(500).
fd idx-file. 01 idx-rec. 05 idx-key pic x(32). 05 idx-rest pic x(468).
working-storage section. 01 fs pic xx. 01 ix pic xx. 01 op pic x(8). 01 reclen pic 9(4). 01 keylen pic 9(4).
procedure division.
  accept reclen from environment 'REC_LEN'
  accept keylen from environment 'KEY_LEN'
  open input raw-file open output idx-file
  perform until fs = '10'
    read raw-file
      at end move '10' to fs
      not at end move spaces to idx-rec move raw-rec(1:reclen) to idx-rec(1:reclen) write idx-rec invalid key display 'LOADIDX duplicate/key error ' ix upon syserr stop run returning 12 end-write
    end-read
  end-perform
  close raw-file idx-file stop run.
