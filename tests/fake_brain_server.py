#!/usr/bin/env python3
"""Local stand-in for server/Code.gs, same JSON protocol and the same rules,
so brain.py can be tested without Google. One lock around every request,
like LockService. Usage: fake_brain_server.py PORT KEY"""
import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROWS, LOCK = [], threading.Lock()
STATUSES = ["claimed", "drafted", "sent", "replied", "call", "client", "dead", "released"]


def handle(req):
    if req.get("key") != KEY:
        return {"ok": False, "error": "bad key"}
    act = req.get("action")
    if act == "list":
        return {"ok": True, "rows": ROWS}
    if act == "claim":
        row = req["row"]
        row["email"] = row["email"].strip().lower()
        old = next((r for r in ROWS if r["email"] == row["email"]), None)
        time.sleep(0.2)  # widen the race window
        if old and old["status"] != "released":
            return {"ok": False, "blocked": True, "row": old}
        if old:
            row["history"] = old["history"] + row["history"]
            ROWS[ROWS.index(old)] = row
        else:
            ROWS.append(row)
        return {"ok": True, "row": row}
    if act == "set":
        if req["status"] not in STATUSES:
            return {"ok": False, "error": "bad status"}
        row = next((r for r in ROWS if r["email"] == req["email"]), None)
        if not row:
            return {"ok": False, "error": "not in brain"}
        if req["status"] == "released" and row["status"] not in ("claimed", "drafted"):
            return {"ok": False, "error": f"already {row['status']}, cannot release"}
        row.update(status=req["status"], updated_at=req["at"])
        row["history"].append({"at": req["at"], "by": req["by"], "status": req["status"], "note": req.get("note", "")})
        return {"ok": True, "row": row}
    return {"ok": False, "error": "unknown action"}


class H(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        with LOCK:
            out = json.dumps(handle(body)).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    KEY = sys.argv[2]
    ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
