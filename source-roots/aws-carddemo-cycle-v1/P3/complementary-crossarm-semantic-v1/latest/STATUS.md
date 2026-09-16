# Complementary cross-arm semantic v1 STATUS

Status: partial actual semantic qualification over the preserved21 real cases, without API reruns.

- Cases checked: 21 ({'posting': 7, 'interest': 7, 'reporting': 7})
- Checker statuses: {'pass': 14, 'inconclusive': 28}
- Case semantic statuses: {'inconclusive': 21}
- Pin verification failures: 0
- Evidence boundary: API-visible response evidence and raw COBOL file effects are reported separately. Same underlying raw bytes can pass internal effects while public API fields remain omitted/limited.
- Inconclusive is used where source-derived typed inputs or trace/totals evidence are not bound; no source-pending obligation is promoted to full 25-obligation validation.

Next step: bind qualified source extractors for INTCALC TCATBALF/DISCGRP rate+balance and TRANREPT totals/framing before upgrading current inconclusive observations to pass/fail business claims.
