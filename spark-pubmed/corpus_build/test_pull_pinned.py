"""Fake-data tests for pull_pinned.py (no network). MV2 of Munim, Inc. Apache-2.0."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pull_pinned  # noqa: E402


class PullTest(unittest.TestCase):
    def test_git_sha1(self):
        # git hash-object of an empty file and of "hello\n" (well-known values)
        self.assertEqual(pull_pinned.git_sha1(b""), "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391")
        self.assertEqual(pull_pinned.git_sha1(b"hello\n"), "ce013625030ba8dba906f756967f9e9ca394464a")

    def test_pull_writes_only_matching_files(self):
        files = {pull_pinned.BASE + "a.py": b"hello\n", pull_pinned.BASE + "b.py": b"tampered\n"}
        pinned = {"a.py": (6, "ce013625030ba8dba906f756967f9e9ca394464a"),
                  "b.py": (6, "ce013625030ba8dba906f756967f9e9ca394464a")}
        with tempfile.TemporaryDirectory() as d:
            ok, report = pull_pinned.pull(d, opener=files.__getitem__, pinned=pinned)
            self.assertFalse(ok)
            self.assertEqual([(r["file"], r["ok"]) for r in report], [("a.py", True), ("b.py", False)])
            self.assertTrue(os.path.exists(os.path.join(d, "a.py")))
            self.assertFalse(os.path.exists(os.path.join(d, "b.py")))

    def test_pinned_set(self):
        self.assertEqual(sorted(pull_pinned.PINNED),
                         ["fetch_corpus.py", "full_count.py", "test_corpus_build.py"])
        self.assertIn(pull_pinned.COMMIT, pull_pinned.BASE)
        self.assertEqual(len(pull_pinned.COMMIT), 40)


if __name__ == "__main__":
    unittest.main()
