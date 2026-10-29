import json
import os
import stat
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import image_eq  # noqa: E402


def no(*a, **k):
    raise OSError("network is unreachable")


class Conn:
    def close(self):
        pass


def make_code(d, names):
    os.makedirs(d)
    for n in names:
        with open(os.path.join(d, n), "wb") as f:
            f.write(b"x")


def make_model(d):
    os.makedirs(os.path.join(d, "sub"))
    for rel, data in (("config.json", b"{}"), ("sub/a.bin", b"\x00\x01")):
        with open(os.path.join(d, rel), "wb") as f:
            f.write(data)


class ImageEq(unittest.TestCase):
    def test_git_blob(self):
        self.assertEqual(image_eq.git_blob(b""), "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391")
        self.assertEqual(image_eq.git_blob(b"hello\n"), "ce013625030ba8dba906f756967f9e9ca394464a")
        self.assertEqual(sorted(image_eq.APP_FILES),
                         ["build_index.py", "rerank.py", "rerank_run.py", "ro_db.py", "spark_t1.py", "t1.py"])
        self.assertTrue(all(len(v) == 40 for v in image_eq.APP_FILES.values()))

    def test_probe_blocked(self):
        rec = image_eq.probe(resolve=no, connect=no)
        self.assertFalse(rec["dns"])
        self.assertFalse(rec["connect"])
        self.assertFalse(rec["reachable"])
        self.assertEqual(rec["connect_error"], "OSError: network is unreachable")

    def test_probe_open(self):
        rec = image_eq.probe(resolve=lambda h, p: [], connect=lambda addr, t: Conn())
        self.assertTrue(rec["dns"] and rec["connect"] and rec["reachable"])
        self.assertIsNone(rec["dns_error"])

    def test_build_app(self):
        files = {"a.py": image_eq.git_blob(b"x"), "b.py": "0" * 40}
        with tempfile.TemporaryDirectory() as d:
            code, model, app = os.path.join(d, "code"), os.path.join(d, "m"), os.path.join(d, "app")
            make_code(code, ["a.py", "b.py", "extra.py"])
            make_model(model)
            rec = image_eq.build_app(code, model, app, files)
            self.assertIsNone(rec["problem"])
            self.assertEqual(rec["listing"], ["a.py", "b.py", "model"])
            self.assertEqual(rec["blob_mismatch"], ["b.py"])
            self.assertEqual(rec["files"]["a.py"]["bytes"], 1)
            self.assertEqual(sorted(rec["model"]), ["config.json", "sub/a.bin"])
            self.assertEqual(rec["model"]["sub/a.bin"]["bytes"], 2)
            self.assertNotIn("git_blob", rec["model"]["config.json"])
            self.assertEqual(rec["runtime"]["sqlite"], image_eq.sqlite3.sqlite_version)
            if os.name == "posix":
                self.assertEqual(stat.S_IMODE(os.stat(os.path.join(app, "a.py")).st_mode), 0o644)
                self.assertEqual(stat.S_IMODE(os.stat(os.path.join(app, "model", "sub")).st_mode), 0o755)

    def test_build_app_refuses(self):
        files = {"a.py": "0" * 40, "b.py": "0" * 40}
        with tempfile.TemporaryDirectory() as d:
            code, model, app = os.path.join(d, "code"), os.path.join(d, "m"), os.path.join(d, "app")
            make_code(code, ["a.py"])
            make_model(model)
            rec = image_eq.build_app(code, model, app, files)
            self.assertEqual(rec["problem"], "missing: b.py")
            self.assertFalse(os.path.exists(app))
            os.makedirs(app)
            rec = image_eq.build_app(code, model, app, files)
            self.assertEqual(rec["problem"], "%s already exists" % app)

    def test_main_app(self):
        with tempfile.TemporaryDirectory() as d:
            code, model, app = os.path.join(d, "code"), os.path.join(d, "m"), os.path.join(d, "app")
            out = os.path.join(d, "o", "app.json")
            make_code(code, list(image_eq.APP_FILES))
            make_model(model)
            argv = ["app", "--code", code, "--model", model, "--app", app, "--out", out]
            self.assertEqual(image_eq.main(argv), 0)
            with open(out, encoding="utf-8") as f:
                rec = json.load(f)
            self.assertEqual(len(rec["blob_mismatch"]), 6)  # every file is b"x", not the real code
            self.assertEqual(image_eq.main(argv), 1)  # app exists now


if __name__ == "__main__":
    unittest.main()
