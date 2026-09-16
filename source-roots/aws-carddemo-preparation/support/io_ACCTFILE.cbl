>>source format free
identification division.
program-id. RAWIO.
environment division.
input-output section.
file-control.
 select raw-file assign to RAW
 organization sequential file status fs.
 select idx-file assign to IDX
 organization indexed access sequential
 record key idx-key file status ix.
data division.
file section.
fd raw-file.
01 raw-rec pic x(300).
fd idx-file.
01 idx-rec.
 02 idx-key pic x(11).
 02 idx-rest pic x(289).
working-storage section.
01 fs pic xx.
01 ix pic xx.
01 op pic x(8).
procedure division.
 accept op from environment 'IO_MODE'
 evaluate function trim(op)
 when 'LOAD'
   open input raw-file
   if fs not = '00' perform bad-raw end-if
   open output idx-file
   if ix not = '00' perform bad-index end-if
   perform until fs = '10'
     read raw-file
     evaluate fs
       when '00'
         move raw-rec to idx-rec
         write idx-rec
         if ix not = '00' perform bad-index end-if
       when '10' continue
       when other perform bad-raw
     end-evaluate
   end-perform
 when 'DUMP'
   open input idx-file
   if ix not = '00' perform bad-index end-if
   open output raw-file
   if fs not = '00' perform bad-raw end-if
   perform until ix = '10'
     read idx-file next record
     evaluate ix
       when '00'
         move idx-rec to raw-rec
         write raw-rec
         if fs not = '00' perform bad-raw end-if
       when '10' continue
       when other perform bad-index
     end-evaluate
   end-perform
 when other
   display 'INVALID IO_MODE' upon syserr
   stop run returning 12
 end-evaluate
 close raw-file
 if fs not = '00' perform bad-raw end-if
 close idx-file
 if ix not = '00' perform bad-index end-if
 stop run returning 0.
bad-raw.
 display 'RAW STATUS=' fs upon syserr
 stop run returning 12.
bad-index.
 display 'INDEX STATUS=' ix upon syserr
 stop run returning 12.
