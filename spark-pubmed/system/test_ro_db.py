import contextlib
import io
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ro_db  # noqa: E402


def make_db(path, wal=True):
    """Two-row table; WAL databases are checkpointed so no committed page is left in -wal."""
    con = sqlite3.connect(path)
    if wal:
        con.execute("PRAGMA journal_mode=WAL")
    con.execute("CREATE TABLE doc (pmid INTEGER PRIMARY KEY, title TEXT)")
    con.executemany("INSERT INTO doc VALUES (?, ?)", [(1, "renal fibrosis"), (2, "tubular atrophy")])
    con.commit()
    if wal:
        con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    con.close()


class RoDb(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)

    def path(self, name):
        return os.path.join(self.dir, name)

    def test_version(self):
        self.assertEqual(ro_db.VERSION, "0.1.0")

    def test_journal_mode(self):
        make_db(self.path("w.db"))
        make_db(self.path("r.db"), wal=False)
        self.assertEqual(ro_db.journal_mode(self.path("w.db")), "wal")
        self.assertEqual(ro_db.journal_mode(self.path("r.db")), "rollback")
        with open(self.path("bad.db"), "wb") as f:
            f.write(b"not a database at all, just some text")
        with self.assertRaises(ValueError):
            ro_db.journal_mode(self.path("bad.db"))
        open(self.path("empty.db"), "wb").close()
        with self.assertRaises(ValueError):
            ro_db.journal_mode(self.path("empty.db"))

    def test_immutable_reads_and_refuses_writes(self):
        p = self.path("w.db")
        make_db(p)
        con = ro_db.connect(p, immutable=True)
        try:
            self.assertEqual(con.execute("SELECT title FROM doc WHERE pmid = 2").fetchone(), ("tubular atrophy",))
            with self.assertRaises(sqlite3.OperationalError):
                con.execute("INSERT INTO doc VALUES (3, 'x')")
        finally:
            con.close()
        self.assertEqual(ro_db.journal_mode(p), "wal")

    def test_refuses_unchecked_wal(self):
        p = self.path("w.db")
        make_db(p)
        with open(p + "-wal", "wb") as f:
            f.write(b"\0" * 32)
        self.assertEqual(ro_db.side_files(p)["wal"], 32)
        with self.assertRaises(ValueError):
            ro_db.connect(p, immutable=True)

    def test_missing(self):
        for immutable in (False, True):
            with self.assertRaises(FileNotFoundError):
                ro_db.connect(self.path("nope.db"), immutable=immutable)

    def test_uri_quotes_awkward_paths(self):
        d = self.path("a b#c%d&e")
        os.mkdir(d)
        p = os.path.join(d, "w.db")
        make_db(p)
        u = ro_db.uri(p)
        self.assertTrue(u.startswith("file:"))
        self.assertTrue(u.endswith("?mode=ro&immutable=1"))
        for ch in " #&":
            self.assertNotIn(ch, u.split("?")[0])
        self.assertTrue(ro_db.uri(p, immutable=False).endswith("/w.db?mode=ro"))
        con = ro_db.connect(p, immutable=True)
        try:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM doc").fetchone(), (2,))
        finally:
            con.close()

    def test_fts5_bm25(self):
        p = self.path("f.db")
        con = sqlite3.connect(p)
        con.execute("PRAGMA journal_mode=WAL")
        try:
            con.execute("CREATE VIRTUAL TABLE t USING fts5(title, abstract)")
        except sqlite3.OperationalError:
            con.close()
            self.skipTest("this SQLite has no FTS5")
        con.executemany("INSERT INTO t (rowid, title, abstract) VALUES (?, ?, ?)",
                        [(11, "kidney fibrosis", "tubular atrophy and fibrosis"), (12, "liver", "steatosis")])
        con.commit()
        con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        con.close()
        ro = ro_db.connect(p, immutable=True)
        try:
            rows = ro.execute("SELECT rowid FROM t WHERE t MATCH ? ORDER BY bm25(t, 2.0, 1.0)", ("fibrosis",)).fetchall()
        finally:
            ro.close()
        self.assertEqual(rows, [(11,)])

    def test_describe_and_main(self):
        p = self.path("r.db")
        make_db(p, wal=False)
        d = ro_db.describe(p)
        self.assertEqual((d["journal_mode"], d["side_files"], d["bytes"]),
                         ("rollback", {"wal": None, "shm": None}, os.path.getsize(p)))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(ro_db.main([p]), 0)
        self.assertEqual(json.loads(out.getvalue())["journal_mode"], "rollback")
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(ro_db.main([]), 2)

    @unittest.skipUnless(hasattr(os, "geteuid") and os.geteuid() != 0,
                         "needs a non-root POSIX user (root ignores folder permissions)")
    def test_read_only_folder(self):
        d = self.path("ro")
        os.mkdir(d)
        p = os.path.join(d, "w.db")
        make_db(p)
        for name in os.listdir(d):  # side files left by the build; the checkpoint emptied -wal
            if name != "w.db":
                os.remove(os.path.join(d, name))
        os.chmod(d, 0o555)
        self.addCleanup(os.chmod, d, 0o755)
        con = ro_db.connect(p, immutable=True)
        try:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM doc").fetchone(), (2,))
        finally:
            con.close()
        self.assertEqual(os.listdir(d), ["w.db"])


if __name__ == "__main__":
    unittest.main()
