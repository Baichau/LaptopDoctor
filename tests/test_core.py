import os, sys, json, time, tempfile, unittest, urllib.request, urllib.error
from pathlib import Path
TMP = Path(tempfile.mkdtemp()).resolve()
os.environ["HOME"] = os.environ["USERPROFILE"] = str(TMP)  # tests never touch your real files
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from laptop_doctor import server as S


class Safety(unittest.TestCase):
    def test_roots(self):
        (TMP / "Downloads").mkdir(exist_ok=True); (TMP / ".ssh").mkdir(exist_ok=True)
        self.assertIsNone(S.safe_root(TMP))            # home itself
        self.assertIsNone(S.safe_root(TMP.parent))     # outside home
        self.assertIsNone(S.safe_root(TMP / ".ssh"))   # hidden
        self.assertIsNotNone(S.safe_root(TMP / "Downloads"))
        self.assertIsNotNone(S.safe_scan_root(TMP))
        self.assertIsNotNone(S.safe_scan_root(TMP.parent))

    def test_dest(self):
        for bad in ("../../etc", "/abs/path", "C:\\Windows\\..\\x"):
            d = S.clean_dest(bad)
            self.assertNotIn("..", d); self.assertFalse(d.startswith("/"))

    def test_scan_root_does_not_grant_cleanup_permission(self):
        allowed = TMP / "Downloads"
        outside = TMP / "OutsideScanOnly"
        allowed.mkdir(exist_ok=True); outside.mkdir(exist_ok=True)
        candidate = outside / "old-installer.exe"
        candidate.write_bytes(b"disposable")
        old = time.time() - 10 * 86400
        os.utime(candidate, (old, old))
        items, _ = S.scan({"folders": [str(allowed)], "scan_roots": [str(TMP)], "include_cache": False})
        self.assertTrue(all(S.inside(item["path"], allowed) for item in items))
        self.assertFalse(any(item["path"] == str(candidate) for item in items))


class Flow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.url = S.serve()
        d = TMP / "Downloads"; d.mkdir(exist_ok=True)
        blob = os.urandom(1_200_000)
        (d / "a.jpg").write_bytes(blob); (d / "b.jpg").write_bytes(blob)
        (d / "report.pdf").write_bytes(b"x"); (d / "notes.txt").write_bytes(b"recent")
        now = time.time()
        for n, days in (("a.jpg", 20), ("b.jpg", 10), ("report.pdf", 10)):
            os.utime(d / n, (now - days * 86400,) * 2)

    def call(self, path, body=None, hdr=True):
        h = {"Content-Type": "application/json"}
        if hdr: h["X-LD"] = "1"
        req = urllib.request.Request(self.url + path, data=None if body is None else json.dumps(body).encode(), headers=h)
        try:
            with urllib.request.urlopen(req) as r: return r.status, json.load(r)
        except urllib.error.HTTPError as e: return e.code, {}

    def test_api_rejects_bad_requests(self):
        self.assertEqual(self.call("/api/apply", {"ids": "i0"})[0], 200)
        self.assertEqual(self.call("/api/not-a-route", {})[0], 404)
        req = urllib.request.Request(self.url + "/api/config", data=b"not-json",
                                     headers={"X-LD": "1", "Content-Type": "application/json"})
        try:
            urllib.request.urlopen(req)
            status = 200
        except urllib.error.HTTPError as e:
            status = e.code
        self.assertEqual(status, 400)

    def test_full_flow(self):
        d = TMP / "Downloads"
        self.assertEqual(self.call("/api/apply", {"ids": []}, hdr=False)[0], 403)  # needs the app header
        _, r = self.call("/api/config", {"ollama_url": "http://127.0.0.1:9", "model": "", "folders": [str(d), "/etc", str(TMP)], "scan_roots": [str(d), str(TMP.parent)]})
        self.assertEqual(sorted(r["rejected"]), sorted(["/etc", str(TMP)]))
        self.assertEqual(r["rejected_scan"], [])
        self.assertEqual(S.cfg()["scan_roots"], sorted([str(d), str(TMP.parent)]))
        self.call("/api/config", {"folders": [str(d)], "scan_roots": [str(d)], "ollama_url": "http://127.0.0.1:9", "model": ""})
        self.call("/api/analyze", {})
        for _ in range(100):
            _, j = self.call("/api/job")
            if j["state"] != "running": break
            time.sleep(0.2)
        self.assertEqual(j["state"], "done")
        res = j["result"]
        self.assertTrue(res["error"])  # no model chosen -> rule-based plan still works
        self.assertEqual(sorted(i["kind"] for i in res["items"]), ["dup", "loose", "loose"])  # recent notes.txt skipped
        _, ap = self.call("/api/apply", {"ids": ["../../etc/passwd", "i999"]})
        self.assertEqual(ap["done"], 0)                # unknown ids / invented paths do nothing
        _, ap = self.call("/api/apply", {"ids": [i["id"] for i in res["items"]]})
        self.assertEqual(ap["done"], 3)
        self.assertTrue((d / "Documents" / "report.pdf").exists() and (d / "Images" / "a.jpg").exists())
        self.assertFalse((d / "b.jpg").exists())
        self.assertTrue(list(S.QUAR.rglob("b.jpg")))   # quarantined, not deleted
        self.assertTrue((d / "notes.txt").exists())
        _, st = self.call("/api/state")
        _, u = self.call("/api/undo", {"id": st["history"][0]["id"]})
        self.assertEqual(u["restored"], 3)
        self.assertTrue((d / "report.pdf").exists() and (d / "b.jpg").exists())


if __name__ == "__main__":
    unittest.main()
