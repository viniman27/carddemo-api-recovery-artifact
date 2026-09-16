
import json, sys, time
from http.server import BaseHTTPRequestHandler
from pathlib import Path
sys.path.insert(0, '<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-harness-v3/src')
from campaign_harness import Case, Expectation, HttpRequestSpec, PerApplicationHttpTarget, Suite, replay_suite
class HangHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    workdir = None
    def do_POST(self):
        Path(type(self).workdir, "attempts.txt").write_text("hit\n", encoding="utf-8")
        while True:
            time.sleep(1)
    def log_message(self, *args): pass
c = Case("hang", "PX", "probe", HttpRequestSpec("POST", "/hang"), "none", Expectation("ok", {"status": [200]}), timeout_seconds=0.05)
started = time.monotonic()
r = replay_suite(Suite("PX", [c]), target=PerApplicationHttpTarget(HangHandler), output_dir=Path('<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-harness-review-v3/evidence-20260915T132029Z/shutdown-hang-run'))
print(json.dumps({"duration_seconds": round(time.monotonic() - started, 3), "totals": r.totals, "applications": r.applications, "receipts": r.receipts}, sort_keys=True))
