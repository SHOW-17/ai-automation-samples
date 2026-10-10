"""127.0.0.1 だけで待ち受ける Slack Incoming Webhook の代わり。受けた JSON を1行ずつ追記する。"""
import json, sys, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

LOG = sys.argv[2] if len(sys.argv) > 2 else "received.jsonl"

class H(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode("utf-8")
        try:
            data = json.loads(body)
        except ValueError:
            data = {"raw": body}
        rec = {"received_at": datetime.datetime.now().isoformat(timespec="seconds"), "path": self.path, "body": data}
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        self.send_response(200); self.send_header("Content-Type", "text/plain"); self.end_headers()
        self.wfile.write(b"ok")  # Slack Incoming Webhook と同じく "ok" を返す
    def log_message(self, *a):
        pass

HTTPServer(("127.0.0.1", int(sys.argv[1]) if len(sys.argv) > 1 else 9999), H).serve_forever()
