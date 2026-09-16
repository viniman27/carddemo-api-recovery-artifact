# Campaign execution handoff v2

Verdict: **READY_PLAN_VERIFIED_NO_OFFICIAL_EXECUTION**

Freeze: `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-freeze-package-v3`
Config: `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-configuration-v3/campaign-config-v3.json`
Readiness JSON: `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-execution-handoff-v2/FINAL-READINESS.json`
Report JSON: `<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-execution-handoff-v2/REPORT.json`

## Blockers
- none

## Counts
- suites: 28
- cases: 12700
- by condition: {'T1': 88, 'T2': 5868, 'T3': 394, 'T4': 6350}

## Guard gate
- excluded string unknown T3 guards from v2: 7
- T3 remaining non-true guards: []
- T4 remaining non-true guards: []

## Parent fail-closed launch argv
```sh
"<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P2a/.venv/bin/python" "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/aws-campaign-runner-v3/aws_campaign_runner_cli.py" "--mode" "execute" "--config" "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-configuration-v3/campaign-config-v3.json" "--output" "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/official-campaign-large12k-run-v2" "--official-ready-json" "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-execution-handoff-v2/FINAL-READINESS.json" "--suite" "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-freeze-package-v3/E1-1/T1.json" "--suite" "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-freeze-package-v3/E1-2/T1.json" "--suite" "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-freeze-package-v3/E1-3/T1.json" "--suite" "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-freeze-package-v3/E2-1/T1.json" "--suite" "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-freeze-package-v3/E2-2/T1.json" "--suite" "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-freeze-package-v3/E2-3/T1.json" "--suite" "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-freeze-package-v3/E3-SDD-stage6r3/T1.json" "--suite" "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-freeze-package-v3/E1-1/T2.json" "--suite" "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-freeze-package-v3/E1-2/T2.json" "--suite" "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-freeze-package-v3/E1-3/T2.json" "--suite" "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-freeze-package-v3/E2-1/T2.json" "--suite" "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-freeze-package-v3/E2-2/T2.json" "--suite" "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-freeze-package-v3/E2-3/T2.json" "--suite" "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-freeze-package-v3/E3-SDD-stage6r3/T2.json" "--suite" "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-freeze-package-v3/E1-1/T3.json" "--suite" "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-freeze-package-v3/E1-2/T3.json" "--suite" "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-freeze-package-v3/E1-3/T3.json" "--suite" "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-freeze-package-v3/E2-1/T3.json" "--suite" "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-freeze-package-v3/E2-2/T3.json" "--suite" "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-freeze-package-v3/E2-3/T3.json" "--suite" "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-freeze-package-v3/E3-SDD-stage6r3/T3.json" "--suite" "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-freeze-package-v3/E1-1/T4.json" "--suite" "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-freeze-package-v3/E1-2/T4.json" "--suite" "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-freeze-package-v3/E1-3/T4.json" "--suite" "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-freeze-package-v3/E2-1/T4.json" "--suite" "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-freeze-package-v3/E2-2/T4.json" "--suite" "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-freeze-package-v3/E2-3/T4.json" "--suite" "<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-freeze-package-v3/E3-SDD-stage6r3/T4.json"
```

Do not run execute/resume from an auxiliary run. The main process must use a tracked background terminal/process. No official execution was started here.
