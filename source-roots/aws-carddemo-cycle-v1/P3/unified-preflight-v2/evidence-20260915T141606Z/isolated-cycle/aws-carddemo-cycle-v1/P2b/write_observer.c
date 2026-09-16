/* Local observation shim for generated C calls; original COBOL is unchanged.
 * Compile only CBTRN02C with -Dcob_write=p2b_observed_write. Each intercepted
 * call delegates exactly once to libcob and logs receiver bytes/status.
 * Returned success is not a durability/commit assertion.
 */
#undef cob_write
#include <libcob.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>

static FILE *capture;
static const char *identity;
static unsigned long sequence;
static void failed(void) { fputs("P2B-CAPTURE-FAIL: write observer I/O\n", stderr); }
static void finish(void) {
    if (capture) {
        if (fprintf(capture,"END|%s|%lu\n",identity,sequence)<0 || fflush(capture)) failed();
        if (fclose(capture)) failed();
    }
}
__attribute__((constructor)) static void begin(void) {
    const char *path=getenv("P2B_WRITE_LOG");
    identity=getenv("P2B_INVOCATION");
    if (!path || !identity) return;
    capture=fopen(path,"wx");
    if (!capture) { failed(); return; }
    if (fprintf(capture,"BEGIN|%s\n",identity)<0 || fflush(capture)) failed();
    atexit(finish);
}
void p2b_observed_write(cob_file *file, cob_field *record, const int opts,
                        cob_field *status, const unsigned int check_eop) {
    size_t size=record->size;
    unsigned char *bytes=NULL;
    if (capture) {
        bytes=malloc(size ? size : 1);
        if (bytes) memcpy(bytes,record->data,size);
        else failed();
    }
    cob_write(file,record,opts,status,check_eop);
    int saved_errno=errno;
    if (capture && bytes) {
        ++sequence;
        fprintf(capture,"WRITE|%lu|%s|%c%c|",sequence,file->select_name,
                file->file_status[0],file->file_status[1]);
        for (size_t n=0;n<size;++n) fprintf(capture,"%02x",bytes[n]);
        fputc('\n',capture);
        if (ferror(capture) || fflush(capture)) failed();
    }
    free(bytes);
    errno=saved_errno;
}
