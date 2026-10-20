"""ECO 414 games: lecturer server for a local network (no internet needed).

Run on the lecturer's laptop (run_games_server.bat). Students on the same Wi-Fi or lab network open the address it
prints; results are sent here as soon as they finish. Only the lecturer page (PIN) can read them.
It speaks the same API as backend/Code.gs (the Google Sheet), so the app works with either. Standard library only.
"""
import datetime
import json
import pathlib
import random
import re
import socket
import sys
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = pathlib.Path(__file__).resolve().parent
DOCS = ROOT / "docs"
DATA_DIR = ROOT / "results"
DATA_DIR.mkdir(exist_ok=True)
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
PIN_FILE = ROOT / "pin.txt"


def get_pin():
    """Fixed lecturer PIN, chosen once and kept in pin.txt. Delete pin.txt to choose a new one."""
    try:
        saved = PIN_FILE.read_text(encoding="utf-8").strip()
        if re.fullmatch(r"\d{4,8}", saved):
            return saved
    except OSError:
        pass
    if not sys.stdin or not sys.stdin.isatty():  # started without a window to type in
        return f"{random.randint(0, 9999):04d}"
    print("Choose a lecturer PIN (4 to 8 digits). You will use it every time; it is saved on this laptop.")
    while True:
        a = input("  New PIN: ").strip()
        if not re.fullmatch(r"\d{4,8}", a):
            print("  Use 4 to 8 digits only.")
            continue
        if input("  Type it again: ").strip() != a:
            print("  The two entries differ. Try again.")
            continue
        PIN_FILE.write_text(a, encoding="utf-8")
        print("  Saved.\n")
        return a


PIN = get_pin()
TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript", ".webmanifest": "application/manifest+json",
         ".png": "image/png", ".json": "application/json"}

STORE = DATA_DIR / "data.json"
lock = threading.Lock()
db = {"sessions": [], "responses": [], "outcomes": []}
if STORE.exists():
    try:
        db.update(json.loads(STORE.read_text(encoding="utf-8")))
    except ValueError:  # keep a damaged file aside rather than overwrite it
        STORE.rename(STORE.with_name(f"data.broken-{datetime.datetime.now():%Y%m%d%H%M%S}.json"))


def save():
    tmp = STORE.with_suffix(".tmp")
    tmp.write_text(json.dumps(db, indent=1), encoding="utf-8")
    tmp.replace(STORE)


def now():
    return datetime.datetime.now().isoformat(timespec="seconds")


def txt(v, n):
    return str("" if v is None else v)[:n]


def num(v):
    try:
        return max(0, round(float(v)))
    except (TypeError, ValueError):
        return ""


def code(v):
    return re.sub(r"[^A-Z0-9]", "", str(v or "").upper())[:8]


def lan_ips():
    ips = set()
    try:
        sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sk.connect(("10.255.255.255", 1))  # no packet is sent; just picks the main interface
        ips.add(sk.getsockname()[0])
        sk.close()
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


def api_get(p):
    a = p.get("action")
    if a == "ping":
        return {"ok": True}
    if a == "info":
        return {"ok": True, "ips": lan_ips(), "port": PORT}
    if a == "session":
        ss = [x for x in db["sessions"] if x["code"] == code(p.get("code"))]
        return {"ok": True, "session": ss[-1]} if ss else {"ok": False, "error": "no such session"}
    if a == "outcome":  # a student reads only their own result: uid and device token must match
        if not p.get("token") or not any(r["uid"] == p.get("uid") and r["token"] == p.get("token") for r in db["responses"]):
            return {"ok": False, "error": "not found"}
        oc = [o for o in db["outcomes"] if o["uid"] == p.get("uid")]
        return {"ok": True, "outcome": oc[-1] if oc else None}
    if p.get("key") != PIN:
        return {"ok": False, "error": "key"}
    if a == "check":
        return {"ok": True}
    if a == "results":
        return {"ok": True, "sessions": db["sessions"],
                "responses": [{k: v for k, v in r.items() if k != "token"} for r in db["responses"]]}
    return {"ok": False, "error": "unknown action"}


OUTCOME_FIELDS = ["uid", "name", "offer_made", "offer_made_result", "offer_received", "offer_received_result",
                  "ug_earnings", "dg_given", "dg_received", "dg_earnings", "total"]


def api_post(b):
    a = b.get("action")
    if a == "submit":
        seen = {r["uid"] for r in db["responses"]}
        done, added = [], 0
        for x in (b.get("items") or [])[:50]:
            if not isinstance(x, dict) or not x.get("uid"):
                continue
            uid = txt(x["uid"], 40)
            if uid not in seen:
                db["responses"].append({
                    "received": now(), "uid": uid, "session": code(x.get("session")), "mode": "P" if x.get("mode") == "P" else "S",
                    "name": txt(x.get("name"), 40), "student_no": txt(x.get("sno"), 20), "partner": txt(x.get("partner"), 40),
                    "stake": num(x.get("stake")), "ug_offer": num(x.get("o")), "ug_min_accept": num(x.get("m")),
                    "ug_response": {"A": "accept", "R": "reject"}.get(x.get("r"), ""), "dg_gift": num(x.get("g")),
                    "guess_avg_offer": num(x.get("b")), "client_time": txt(x.get("t"), 30), "token": txt(x.get("token"), 40)})
                seen.add(uid)
                added += 1
            done.append(uid)
        if added:
            save()
            print(f"  received {added} result(s)   ({len(db['responses'])} in total)")
        return {"ok": True, "done": done}
    if b.get("key") != PIN:
        return {"ok": False, "error": "key"}
    if a == "createSession":
        c = code(b.get("code"))
        if not any(x["code"] == c for x in db["sessions"]):
            db["sessions"].append({"created": now(), "code": c, "stake": num(b.get("stake")), "step": num(b.get("step")),
                                   "currency": txt(b.get("cur"), 6), "title": txt(b.get("title"), 60)})
            save()
        return {"ok": True}
    if a == "saveOutcomes":
        c = code(b.get("session"))
        rows = [r for r in (b.get("rows") or []) if isinstance(r, dict)]
        db["outcomes"] = [o for o in db["outcomes"] if o["session"] != c] + [
            {"paired_at": now(), "session": c, **{k: r.get(k) for k in OUTCOME_FIELDS}} for r in rows]
        save()
        return {"ok": True, "saved": len(rows)}
    return {"ok": False, "error": "unknown action"}


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

    def do_GET(self):
        path, _, query = self.path.partition("?")
        if path in ("/", "/index.html", "/lecturer"):
            return self.send(200, page(), TYPES[".html"])
        if path == "/api":
            p = {k: v[0] for k, v in urllib.parse.parse_qs(query).items()}
            with lock:
                return self.send(200, api_get(p))
        f = (DOCS / path.lstrip("/")).resolve()
        if f.is_file() and DOCS in f.parents and f.name != "sw.js":
            return self.send(200, f.read_bytes(), TYPES.get(f.suffix, "application/octet-stream"))
        self.send(404, {"ok": False, "error": "not found"})

    def do_POST(self):
        if self.path.partition("?")[0] != "/api":
            return self.send(404, {"ok": False, "error": "not found"})
        n = min(int(self.headers.get("Content-Length") or 0), 200000)
        try:
            b = json.loads(self.rfile.read(n) or b"{}")
            assert isinstance(b, dict)
        except (ValueError, AssertionError):
            return self.send(200, {"ok": False, "error": "bad request"})
        with lock:
            return self.send(200, api_post(b))


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
    print(f" Lecturer PIN:                 {PIN}" + ("   (to change it, delete pin.txt)" if PIN_FILE.exists() else ""))
    print(f"\n Results are saved in: {STORE}")
    if db["responses"]:
        print(f" {len(db['responses'])} results from earlier sessions are kept.")
    print(" Close this window to stop the server.\n")
    threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{PORT}/lecturer")).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
