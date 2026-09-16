
import sys, time, json
from http.server import BaseHTTPRequestHandler
from pathlib import Path
sys.path.insert(0, '<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-harness-v2/src')
from campaign_harness import Case, Expectation, HttpRequestSpec, PerApplicationHttpTarget, Suite, replay_suite
class HangHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    workdir = None
    def do_POST(self):
        time.sleep(60)
        self.send_response(200); self.send_header("Content-Length", "2"); self.end_headers(); self.wfile.write(b"{}")
    def log_message(self, *args): pass
c = Case("hang", "PX", "probe", HttpRequestSpec("POST", "/hang"), "none", Expectation("ok", {"status": [200]}), timeout_seconds=0.05)
replay_suite(Suite("PX", [c]), target=PerApplicationHttpTarget(HangHandler), output_dir=Path('<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P3/campaign-harness-review-v2/evidence-20260915T130807Z/shutdown-hang-run'))
print("completed")
