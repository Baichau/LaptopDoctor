#!/usr/bin/env python3
"""Laptop Doctor - review-first laptop tidy-up with a local Ollama model.
Backend: a tiny local web server plus safe file operations. The UI is in ./web, the entry point is ../main.py

SAFETY MODEL
- The AI never sees or returns file paths. It gets short ids and can only comment or suggest a folder name.
- Only folders you whitelist (inside your home folder) can be scanned or changed.
- Nothing is ever permanently deleted: "remove" means move to a quarantine folder you empty yourself.
- Nothing is pre-selected. You tick each change, confirm, and can undo every batch.
"""
import sys, traceback, json, os, re, stat, shutil, hashlib, time, threading, webbrowser, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORT = 0  # chosen by serve()
WEB = (Path(getattr(sys, '_MEIPASS', '.')) / 'laptop_doctor' / 'web') if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent / 'web'
STATIC = {'/': ('index.html', 'text/html; charset=utf-8'), '/style.css': ('style.css', 'text/css'),
          '/app.js': ('app.js', 'application/javascript')}
HOME = Path.home().resolve()
APP = HOME / ".laptop_doctor"
QUAR = APP / "quarantine"
QUAR.mkdir(parents=True, exist_ok=True)
if sys.stderr is None or sys.stdout is None:  # windowed .exe has no console
    _log = open(str(APP / 'log.txt'), 'a', buffering=1)
    sys.stdout, sys.stderr = sys.stdout or _log, sys.stderr or _log
CFG_F, HIST_F = APP / "config.json", APP / "history.json"
DEFAULT = {"ollama_url": "http://localhost:11434", "model": "",
           "folders": [str(HOME / "Downloads")], "include_cache": False}
CATS = {"Images": "jpg jpeg png gif webp heic svg bmp",
        "Documents": "pdf doc docx txt odt rtf md xls xlsx ppt pptx csv",
        "Videos": "mp4 mkv mov avi webm", "Audio": "mp3 wav flac m4a ogg",
        "Archives": "zip rar 7z tar gz iso", "Installers": "exe msi dmg pkg deb apk"}
EXT = {e: c for c, s in CATS.items() for e in s.split()}
STATE = {"items": {}}


def jload(p, d):
    try:
        return json.loads(p.read_text())
    except Exception:
        return d


def cfg():
    return {**DEFAULT, **jload(CFG_F, {})}


def inside(p, root):
    try:
        Path(p).resolve().relative_to(Path(root).resolve())
        return True
    except Exception:
        return False


def safe_root(p):
    """A folder is allowed only if it is strictly inside HOME and not hidden."""
    try:
        p = Path(p).expanduser().resolve()
    except Exception:
        return None
    if not p.is_dir() or p == HOME or HOME not in p.parents:
        return None
    if any(x.startswith(".") for x in p.relative_to(HOME).parts):
        return None
    return p


def cache_dirs():
    c = [HOME / ".cache", HOME / "Library/Caches"]
    if os.environ.get("LOCALAPPDATA"):
        c.append(Path(os.environ["LOCALAPPDATA"]) / "Temp")
    return [p for p in c if p.is_dir()]


def roots(c):
    r = [x for x in (safe_root(f) for f in c["folders"]) if x]
    return r + (cache_dirs() if c["include_cache"] else [])


def dsize(p):
    t = 0
    for dp, _, fn in os.walk(p):
        for f in fn:
            try:
                t += os.lstat(os.path.join(dp, f)).st_size
            except OSError:
                pass
    return t


def ollama(c, path, body=None, timeout=300):
    req = urllib.request.Request(c["ollama_url"].rstrip("/") + path,
                                 data=json.dumps(body).encode() if body else None,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


# ---------- scanning (plain rules, no AI) ----------
def scan(c):
    items, files, now = [], [], time.time()

    def add(kind, p, size, age, root, dest=None, note=""):
        items.append({"id": "i%d" % len(items), "kind": kind, "path": str(p), "name": p.name,
                      "size": size, "age": age, "root": str(root), "dest": dest,
                      "action": "move" if dest else "quarantine", "note": note})

    for r in c["folders"]:
        root = safe_root(r)
        if not root:
            continue
        for dp, dn, fn in os.walk(root):
            dn[:] = [d for d in dn if not d.startswith(".")]
            rel = Path(dp).relative_to(root).parts
            if len(rel) >= 3:
                dn[:] = []
            for f in fn:
                if f.startswith(".") or len(files) > 30000:
                    continue
                p = Path(dp) / f
                try:
                    st = p.lstat()
                except OSError:
                    continue
                if stat.S_ISREG(st.st_mode):
                    files.append((p, st.st_size, int((now - st.st_mtime) / 86400), root, len(rel)))

    used, by = set(), {}
    for f in files:
        if (1 << 20) <= f[1] <= (300 << 20):
            by.setdefault(f[1], []).append(f)
    for g in by.values():
        if len(g) < 2:
            continue
        hs = {}
        for f in g:
            try:
                d = hashlib.sha1()
                with open(f[0], "rb") as fh:
                    for b in iter(lambda: fh.read(1 << 20), b""):
                        d.update(b)
                hs.setdefault(d.hexdigest(), []).append(f)
            except OSError:
                pass
        for dup in hs.values():
            dup.sort(key=lambda f: -f[2])  # keep the oldest copy
            for f in dup[1:]:
                if f[2] >= 2:
                    add("dup", f[0], f[1], f[2], f[3], note="Identical to " + dup[0][0].name)
                    used.add(f[0])
    for p, s, a, root, depth in files:
        if p in used or a < 2:  # never touch files changed in the last 2 days
            continue
        cat = EXT.get(p.suffix.lower().lstrip("."))
        if depth == 0 and cat:
            add("loose", p, s, a, root, dest=cat)
        elif a > 365 and s > (50 << 20):
            add("old", p, s, a, root)
    if c["include_cache"]:
        for cd in cache_dirs():
            for ch in cd.iterdir():
                try:
                    if ch.is_symlink():
                        continue
                    s = dsize(ch) if ch.is_dir() else ch.stat().st_size
                    if s > (20 << 20):
                        add("cache", ch, s, int((now - ch.stat().st_mtime) / 86400), cd,
                            note="Close the owning app first; it rebuilds this on its own.")
                except OSError:
                    pass
    du = shutil.disk_usage(HOME)
    st = {"disk_total": du.total, "disk_used": du.used, "files": len(files)}
    try:
        import psutil
        st["ram"], st["cpu"] = psutil.virtual_memory().percent, psutil.cpu_percent(0.3)
    except Exception:
        pass
    st["largest"] = [{"name": f[0].name, "size": f[1]} for f in sorted(files, key=lambda f: -f[1])[:5]]
    return items, st


# ---------- AI advisor ----------
def clean_dest(s):
    parts = [re.sub(r'[<>:"|?*\\]', "", x).strip() for x in str(s).replace("\\", "/").split("/")]
    return "/".join([x for x in parts if x and x not in (".", "..") and not x.startswith(".")][:3])


def ask_ai(c, items, st):
    if not c["model"]:
        raise RuntimeError("No model selected. Choose one in Settings.")
    brief = {"disk_used_pct": round(st["disk_used"] * 100 / st["disk_total"]),
             "ram_pct": st.get("ram"), "cpu_pct": st.get("cpu"), "files_scanned": st["files"],
             "largest_files": st["largest"],
             "candidates": [{"id": i["id"], "name": i["name"], "kind": i["kind"],
                             "mb": round(i["size"] / 1048576), "age_days": i["age"],
                             "proposed_folder": i["dest"]} for i in items[:40]]}
    sysmsg = ("You are a cautious laptop health advisor. You only see summaries. Reply with JSON only: "
              '{"score":0-100,"diagnosis":"2-3 sentences","tips":["short actionable tip"],'
              '"notes":{"<id>":"one-line reason it is safe or needs a human check"},'
              '"folders":{"<id>":"Better/Relative Folder"}}. Use only the ids provided. '
              "Never invent files. If unsure, say a human should check.")
    r = ollama(c, "/api/chat", {"model": c["model"], "stream": False, "format": "json", "options": {"num_predict": 900},
                                "messages": [{"role": "system", "content": sysmsg},
                                             {"role": "user", "content": json.dumps(brief)}]}, 600)
    return json.loads(r["message"]["content"])


def analyze():
    c = cfg()
    items, st = scan(c)
    ai, err = {}, ""
    try:
        ai = ask_ai(c, items, st)
    except Exception as e:
        err = str(e)
    if not isinstance(ai, dict):
        ai = {}
    notes, folders = ai.get("notes"), ai.get("folders")
    for i in items:
        if isinstance(notes, dict) and notes.get(i["id"]):
            i["note"] = str(notes[i["id"]])[:200]
        if i["action"] == "move" and isinstance(folders, dict) and folders.get(i["id"]):
            d = clean_dest(folders[i["id"]])
            if d:
                i["dest"] = d
    STATE["items"] = {i["id"]: i for i in items}
    tips = ai.get("tips") if isinstance(ai.get("tips"), list) else []
    return {"stats": st, "items": items, "error": err,
            "ai": {"score": ai.get("score"), "diagnosis": ai.get("diagnosis"), "tips": tips[:6]}}


JOB = {"state": "idle", "result": None, "error": ""}


def start_analyze():
    if JOB["state"] == "running":
        return {"started": False}
    JOB.update(state="running", result=None, error="")

    def run():
        try:
            JOB["result"] = analyze()
            JOB["state"] = "done"
        except Exception as e:
            traceback.print_exc()
            JOB["error"], JOB["state"] = str(e), "error"
    threading.Thread(target=run, daemon=True).start()
    return {"started": True}


# ---------- applying and undoing ----------
def uniq(p):
    q, n = p, 1
    while q.exists():
        q = p.with_name("%s (%d)%s" % (p.stem, n, p.suffix))
        n += 1
    return q


def apply(ids):
    # Accept only a bounded list of server-issued item ids, never client-supplied paths.
    if not isinstance(ids, list):
        return {"done": 0, "skipped": ["Expected a list of item ids."]}
    ids = [i for i in ids[:500] if isinstance(i, str)]
    rs = roots(cfg())
    stamp = time.strftime("%Y%m%d-%H%M%S")
    moves, skipped = [], []
    for i in ids:
        it = STATE["items"].get(i)  # only server-known ids; the client cannot supply paths
        if not it:
            continue
        src = Path(it["path"])
        try:
            if src.is_symlink() or not src.exists() or not any(inside(src, r) for r in rs):
                raise ValueError("outside allowed folders or missing")
            if it["action"] == "move":
                dst = Path(it["root"]) / it["dest"]
                if not inside(dst, it["root"]):
                    raise ValueError("bad destination")
            else:
                dst = QUAR / stamp
            dst.mkdir(parents=True, exist_ok=True)
            dst = uniq(dst / src.name)
            shutil.move(str(src), str(dst))
            moves.append({"from": str(src), "to": str(dst), "name": src.name})
        except Exception as e:
            skipped.append("%s: %s" % (it["name"], e))
    if moves:
        h = jload(HIST_F, [])
        h.insert(0, {"id": stamp, "ts": time.strftime("%Y-%m-%d %H:%M"), "moves": moves, "undone": False})
        HIST_F.write_text(json.dumps(h[:50]))
    return {"done": len(moves), "skipped": skipped}


def undo(bid):
    h, restored = jload(HIST_F, []), 0
    for b in h:
        if b["id"] == bid and not b["undone"]:
            for m in reversed(b["moves"]):
                src, dst = Path(m["to"]), Path(m["from"])
                if src.exists() and not dst.exists() and inside(src, HOME) and inside(dst, HOME):
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(src), str(dst))
                    restored += 1
            b["undone"] = True
    HIST_F.write_text(json.dumps(h))
    return {"restored": restored}


def save_config(body):
    c, rejected = cfg(), []
    c["ollama_url"] = str(body.get("ollama_url") or c["ollama_url"])
    c["model"] = str(body.get("model") or "")
    c["include_cache"] = bool(body.get("include_cache"))
    ok = []
    for f in body.get("folders", []):
        r = safe_root(f)
        (ok if r else rejected).append(str(r) if r else str(f))
    c["folders"] = sorted(set(ok))
    CFG_F.write_text(json.dumps(c))
    return {"rejected": rejected}


# ---------- HTTP ----------
class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def out(self, code, body, ctype="application/json"):
        b = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def host_ok(self):  # blocks DNS-rebinding and other sites poking at localhost
        return self.headers.get("Host") in ("127.0.0.1:%d" % PORT, "localhost:%d" % PORT)

    def do_GET(self):
        if not self.host_ok():
            return self.out(403, {})
        if self.path in STATIC:
            name, ctype = STATIC[self.path]
            return self.out(200, (WEB / name).read_bytes(), ctype)
        if self.path == "/api/state":
            c = cfg()
            try:
                models, err = [m["name"] for m in ollama(c, "/api/tags", timeout=4)["models"]], ""
            except Exception:
                models, err = [], "Can't reach Ollama at " + c["ollama_url"]
            return self.out(200, {"config": c, "models": models, "ollama_error": err,
                                  "history": jload(HIST_F, []), "quarantine": str(QUAR),
                                  "quarantine_size": dsize(QUAR)})
        if self.path == "/api/job":
            return self.out(200, JOB)
        self.out(404, {})

    def do_POST(self):
        if not self.host_ok() or self.headers.get("X-LD") != "1":
            return self.out(403, {})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 0 or length > 1_000_000:
                return self.out(413, {"error": "Request body is too large."})
            body = json.loads(self.rfile.read(length) or b"{}")
            if not isinstance(body, dict):
                return self.out(400, {"error": "Request body must be a JSON object."})
            routes = {"/api/config": lambda: save_config(body), "/api/analyze": start_analyze,
                      "/api/apply": lambda: apply(body.get("ids", [])),
                      "/api/undo": lambda: undo(body.get("id")),
                      "/api/open": open_quarantine}
            action = routes.get(self.path)
            if action is None:
                return self.out(404, {"error": "Unknown API endpoint."})
            self.out(200, action())
        except (json.JSONDecodeError, ValueError) as e:
            self.out(400, {"error": "Invalid request: " + str(e)})
        except Exception as e:
            traceback.print_exc()
            self.out(500, {"error": str(e)})


def open_quarantine():
    if os.name == "nt":
        os.startfile(str(QUAR))
    else:
        webbrowser.open(QUAR.as_uri())
    return {"ok": True}


def serve():
    """Start the local server on a free port and return its URL."""
    global PORT
    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    PORT = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return "http://localhost:%d" % PORT
