import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nobody_run  # noqa: E402


def no_chown(path, uid, gid):
    pass


class NobodyRun(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.db = os.path.join(self.dir, "idx", "x.db")
        os.makedirs(os.path.dirname(self.db))
        open(self.db, "wb").close()
        self.work, self.out = os.path.join(self.dir, "w"), os.path.join(self.dir, "out")
        self.seen = {}

    def fake(self, code, stderr=""):
        def runner(cmd, env, uid):
            self.seen.update(cmd=cmd, env=env, uid=uid)
            os.makedirs(os.path.join(self.work, "l"), exist_ok=True)
            os.makedirs(os.path.join(self.work, ".cache"), exist_ok=True)
            for rel in ("l/run.json", ".cache/junk"):
                with open(os.path.join(self.work, rel), "w", encoding="utf-8") as f:
                    f.write("{}")
            return subprocess.CompletedProcess(cmd, code, "printed", stderr)
        return runner

    def test_version(self):
        self.assertEqual(nobody_run.VERSION, "0.1.0")

    def test_ok_copies_and_records(self):
        rec = nobody_run.run(["python", "x.py", "--out-dir", "{W}/l"], self.work, self.out, self.db, "ok",
                             runner=self.fake(0), chown=no_chown)
        self.assertEqual(self.seen["cmd"], ["python", "x.py", "--out-dir", self.work + "/l"])
        self.assertEqual((self.seen["uid"], self.seen["env"]["HOME"], self.seen["env"]["HF_HUB_OFFLINE"]),
                         (65534, self.work, "1"))
        self.assertEqual((rec["exit"], rec["as_expected"], rec["copied"]), (0, True, ["l/run.json"]))
        self.assertEqual(rec["before"], {"side_files": {"wal": None, "shm": None}, "beside": ["x.db"]})
        self.assertEqual(rec["after"], rec["before"])
        self.assertTrue(os.path.isfile(os.path.join(self.out, "l", "run.json")))
        self.assertFalse(os.path.exists(os.path.join(self.out, ".cache")))
        with open(os.path.join(self.out, "nobody.json"), encoding="utf-8") as f:
            self.assertEqual(json.load(f)["exit"], 0)

    def test_expect_fail(self):
        err = "Traceback\n  line\nsqlite3.OperationalError: attempt to write a readonly database\n"
        rec = nobody_run.run(["python", "x.py"], self.work, self.out, self.db, "fail",
                             runner=self.fake(1, err), chown=no_chown)
        self.assertEqual((rec["as_expected"], rec["stderr_last"][-1]),
                         (True, "sqlite3.OperationalError: attempt to write a readonly database"))
        rec = nobody_run.run(["python", "x.py"], self.work, self.out, self.db, "fail",
                             runner=self.fake(0), chown=no_chown)
        self.assertFalse(rec["as_expected"])
        rec = nobody_run.run(["python", "x.py"], self.work, self.out, self.db, "ok",
                             runner=self.fake(1), chown=no_chown)
        self.assertFalse(rec["as_expected"])

    def test_main_usage(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(nobody_run.main(["--work", self.work]), 2)
            with self.assertRaises(SystemExit):
                nobody_run.main(["--work", self.work, "--out-dir", self.out, "--db", self.db, "--expect", "ok", "--"])
            with self.assertRaises(SystemExit):
                nobody_run.main(["--work", self.work, "--out-dir", self.out, "--db", self.db, "--expect", "maybe",
                                 "--", "true"])


if __name__ == "__main__":
    unittest.main()
