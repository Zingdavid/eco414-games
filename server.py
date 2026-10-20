"""ECO 414 games: lecturer server for a local network (no internet needed).

Run on the lecturer's laptop (run_games_server.bat). Students on the same Wi-Fi or lab network open the address it
prints; every result is sent here as soon as they finish. Results are only shown on the lecturer page (PIN).
Standard library only.
"""
import datetime
import json
import pathlib
import random
import re
import socket
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = pathlib.Path(__file__).resolve().parent
DOCS = ROOT / "docs"
DATA_DIR = ROOT / "results"
DATA_DIR.mkdir(exist_ok=True)
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
PIN = f"{random.randint(0, 9999):04d}"
CODE_RE = re.compile(r"^(S-[A-Z0-9]{1,10}-\d+-\d+-\d+-\d+-\d+|P-[A-Z0-9]{1,10}-[A-Z0-9]{1,10}-\d+-[AR]-\d+-\d+)$")
TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript", ".webmanifest": "application/manifest+json",
         ".png": "image/png", ".json": "application/json"}

lock = threading.Lock()
settings = {"stake": 1000, "step": 50, "cur": "MWK"}
session_file = DATA_DIR / f"session-{datetime.datetime.now():%Y-%m-%d}.jsonl"
codes = []  # list of dicts {t, ip, code}, in arrival order
if session_file.exists():  # resume today's session after a restart
    for line in session_file.read_text(encoding="utf-8").splitlines():
        try:
            codes.append(json.loads(line))
        except ValueError:
            pass


def lan_ips():
    ips = set()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))  # no packet is sent; just picks the main interface
        ips.add(s.getsockname()[0])
        s.close()
    except OSError:
        pass
    try:
        ips.update(socket.gethostbyname_ex(socket.gethostname())[2])
    except OSError:
        pass
    return sorted(i for i in ips if not i.startswith(("127.", "169.254.")))


def page():
    html = (DOCS / "index.html").read_text(encoding="utf-8")
    return html.replace("<!--SERVER-->", "<script>window.ECO_SERVER = true;</script>")


class Handler(BaseHTTPRequestHandler):
    server_version = "ECO414Games"

    def log_message(self, fmt, *args):  # keep the console readable
        pass

    def send(self, status, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else (json.dumps(body) if ctype == "application/json" else body).encode()
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def authed(self):
        return self.headers.get("X-Pin", "") == PIN

    def body(self):
        n = min(int(self.headers.get("Content-Length") or 0), 20000)
        try:
            return json.loads(self.rfile.read(n) or b"{}")
        except ValueError:
            return {}

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html", "/lecturer"):
            return self.send(200, page(), TYPES[".html"])
        if path == "/api/settings":
            return self.send(200, settings)
        if path == "/api/info":
            return self.send(200, {"ips": lan_ips(), "port": PORT})
        if path == "/api/results":
            if not self.authed():
                return self.send(403, {"error": "PIN required"})
            with lock:
                return self.send(200, {"codes": [c["code"] for c in codes], "n": len(codes)})
        f = (DOCS / path.lstrip("/")).resolve()
        if f.is_file() and DOCS in f.parents and f.name != "sw.js":
            return self.send(200, f.read_bytes(), TYPES.get(f.suffix, "application/octet-stream"))
        self.send(404, {"error": "not found"})

    def do_POST(self):
        global session_file
        path = self.path.split("?")[0]
        b = self.body()
        if path == "/api/submit":
            code = str(b.get("code", "")).strip().upper()
            if not CODE_RE.match(code):
                return self.send(400, {"ok": False, "error": "invalid code"})
            rec = {"t": datetime.datetime.now().isoformat(timespec="seconds"), "ip": self.client_address[0], "code": code}
            with lock:
                codes.append(rec)
                with session_file.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(rec) + "\n")
                n = len(codes)
            print(f"  received {code}   ({n} so far)")
            return self.send(200, {"ok": True})
        if not self.authed():
            return self.send(403, {"error": "PIN required"})
        if path == "/api/settings":
            try:
                stake, step = int(b["stake"]), int(b["step"])
                assert stake >= 10 and step >= 1 and stake % step == 0
            except (KeyError, ValueError, AssertionError):
                return self.send(400, {"error": "bad settings"})
            settings.update(stake=stake, step=step, cur=str(b.get("cur") or "MWK")[:6])
            return self.send(200, settings)
        if path == "/api/clear":
            with lock:
                codes.clear()
                if session_file.exists():  # keep the old file; start a fresh one
                    session_file = DATA_DIR / f"session-{datetime.datetime.now():%Y-%m-%d_%H%M%S}.jsonl"
            return self.send(200, {"ok": True})
        self.send(404, {"error": "not found"})


def main():
    try:
        srv = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    except OSError:
        print(f"Port {PORT} is busy. Is the games server already running in another window?")
        input("Press Enter to close.")
        return
    ips = lan_ips()
    print("=" * 64)
    print(" ECO 414 Classroom Games: lecturer server")
    print("=" * 64)
    print(" Students open (same Wi-Fi or lab network):")
    for ip in ips or ["<no network found: connect to Wi-Fi or start a hotspot>"]:
        print(f"     http://{ip}:{PORT}")
    print(f"\n Lecturer page (this laptop):  http://localhost:{PORT}/lecturer")
    print(f" Lecturer PIN for today:       {PIN}")
    print(f"\n Results are saved in: {DATA_DIR}")
    if codes:
        print(f" Resumed today's session: {len(codes)} results already received.")
    print(" Close this window to stop the server.\n")
    threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{PORT}/lecturer")).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
