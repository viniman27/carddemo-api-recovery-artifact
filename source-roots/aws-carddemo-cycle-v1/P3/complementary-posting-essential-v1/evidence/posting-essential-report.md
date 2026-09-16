# Complementary posting essential v1 report

Scope: posting-only essential complementary scenarios; real isolated local API/COBOL; not official campaign; not oracle quarantine

Case status counts: `{"pass": 6}`

## Case receipts
- valid-new-tcatbal: pass HTTP=200 COBOL=True run=`<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/complementary-posting-essential-v1/evidence/p2b-runs/posting-vycdf27l` failures=[]
- valid-existing-tcatbal: pass HTTP=200 COBOL=True run=`<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/complementary-posting-essential-v1/evidence/p2b-runs/posting-cv4stdh2` failures=[]
- reject-card-missing: pass HTTP=200 COBOL=True run=`<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/complementary-posting-essential-v1/evidence/p2b-runs/posting-efgra50l` failures=[]
- reject-account-missing: pass HTTP=200 COBOL=True run=`<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/complementary-posting-essential-v1/evidence/p2b-runs/posting-666rt572` failures=[]
- reject-limit: pass HTTP=200 COBOL=True run=`<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/complementary-posting-essential-v1/evidence/p2b-runs/posting-rtlm6wsl` failures=[]
- reject-expiry: pass HTTP=200 COBOL=True run=`<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/complementary-posting-essential-v1/evidence/p2b-runs/posting-zwqqbubn` failures=[]

## Obligation matrix
- POSTTRAN-OBL-001: partial_qualified_pending_partitions :: all DD/open statuses are 00 before first read => qualified_observed cases=['valid-new-tcatbal', 'valid-existing-tcatbal', 'reject-card-missing', 'reject-account-missing', 'reject-limit', 'reject-expiry']; one required open returns non-00 and must stop before processing => pending_unattempted cases=[]
- POSTTRAN-OBL-002: partial_qualified_pending_partitions :: first read status 00 increments processed count => qualified_observed cases=['valid-new-tcatbal']; read status 10 ends loop without processing a new record => qualified_observed cases=['valid-new-tcatbal', 'reject-card-missing']; non-00/non-10 read status abends => pending_unattempted cases=[]
- POSTTRAN-OBL-003: qualified_observed_all_listed_partitions :: accepted transaction copies business fields from DALYTRAN => qualified_observed cases=['valid-new-tcatbal', 'valid-existing-tcatbal']; processing timestamp is current-date derived and not pre-fixed => qualified_observed cases=['valid-new-tcatbal', 'valid-existing-tcatbal']
- POSTTRAN-OBL-004: qualified_observed_all_listed_partitions :: card absent in XREF rejects with reason 100 => qualified_observed cases=['reject-card-missing']; card present continues to account checks without format-only validation => qualified_observed cases=['valid-new-tcatbal', 'reject-account-missing', 'reject-limit', 'reject-expiry']
- POSTTRAN-OBL-005: qualified_observed_all_listed_partitions :: account absent rejects 101 => qualified_observed cases=['reject-account-missing']; account over limit rejects 102 unless later expiry check overwrites with 103 => qualified_observed cases=['reject-limit']; textual expiration comparison fails and final reason is 103 => qualified_observed cases=['reject-expiry']
- POSTTRAN-OBL-006: qualified_observed_all_listed_partitions :: one validation reason writes one reject trailer => qualified_observed cases=['reject-card-missing', 'reject-account-missing', 'reject-limit', 'reject-expiry']; normal close with reject count greater than zero returns RC 4 => qualified_observed cases=['reject-card-missing', 'reject-account-missing', 'reject-limit', 'reject-expiry']
- POSTTRAN-OBL-007: partial_qualified_pending_partitions :: TCATBAL missing key creates initial category balance => qualified_observed cases=['valid-new-tcatbal']; TCATBAL existing key rewrites balance plus amount => qualified_observed cases=['valid-existing-tcatbal']; TCATBAL I/O status outside documented set abends before account/TRANFILE effects => pending_unattempted cases=[]
- POSTTRAN-OBL-008: partial_qualified_pending_partitions :: positive amount updates balance and credit => qualified_observed cases=['valid-new-tcatbal', 'valid-existing-tcatbal']; negative amount updates balance and debit => pending_unattempted cases=[]; ACCOUNT rewrite invalid key records reason 109 but continues toward TRANFILE write => pending_unattempted cases=[]
- POSTTRAN-OBL-009: inconclusive_internal_order :: TRANFILE write status 00 completes after prior effects => inconclusive_internal_order_unobserved cases=['valid-new-tcatbal', 'valid-existing-tcatbal']; TRANFILE write non-00 abends after prior effects were attempted => inconclusive_internal_order_unobserved cases=[]; duplicate DALYTRAN/TRAN id is not prevalidated before write => pending_unattempted cases=[]
