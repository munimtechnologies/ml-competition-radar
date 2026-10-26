import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch_code  # noqa: E402

TABLE = {"a": ("c1", "f1", {"x.py": 3, "y.py": 3}),
         "b": ("c2", "f2", {"z.py": 4}),
         "dup": ("c3", "f3", {"x.py": 3})}
FILES = {"mem/c1/f1/x.py": b"abc", "mem/c1/f1/y.py": b"h\ni", "mem/c2/f2/z.py": b"wxyz",
         "mem/c3/f3/x.py": b"abc"}


def read(url):
    return FILES[url]


class Fetch(unittest.TestCase):
    def test_ok(self):
        with tempfile.TemporaryDirectory() as d:
            rep = fetch_code.fetch(d, ["a", "b"], raw="mem/%s/%s/", read=read, table=TABLE)
            self.assertIsNone(rep["problem"])
            self.assertEqual(sorted(os.listdir(d)), ["x.py", "y.py", "z.py"])
            with open(os.path.join(d, "y.py"), "rb") as f:
                self.assertEqual(f.read(), b"h\ni")
            self.assertEqual(rep["files"]["y.py"]["lines"], 2)
            self.assertEqual(rep["files"]["z.py"]["group"], "b")
            self.assertEqual(rep["groups"]["a"], {"commit": "c1", "folder": "f1"})
            self.assertEqual(rep["files"]["x.py"]["sha256"],
                             "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")

    def test_problems(self):
        table = {"a": ("c1", "f1", {"x.py": 4}), "dup": TABLE["dup"]}
        with tempfile.TemporaryDirectory() as d:
            rep = fetch_code.fetch(d, ["a", "dup", "nope"], raw="mem/%s/%s/", read=read, table=table)
            self.assertEqual(rep["problem"],
                             "x.py: 3 bytes, expected 4; x.py in two groups; unknown group nope")

    def test_main_usage_and_pins(self):
        self.assertEqual(fetch_code.main(["only-out"]), 2)
        self.assertEqual(sorted(fetch_code.GROUPS), ["dense", "prf", "rerank", "t1", "t2"])
        for commit, folder, want in fetch_code.GROUPS.values():
            self.assertEqual(len(commit), 40)
            self.assertTrue(all(n.endswith(".py") and s > 0 for n, s in want.items()))
        self.assertEqual(json.loads(json.dumps(fetch_code.GROUPS))["t1"][2]["t1.py"], 12240)
        self.assertEqual(fetch_code.GROUPS["prf"][:2], ("3ea7684edd27289353be78202041f24f308e342f", "prf"))
        self.assertEqual(fetch_code.GROUPS["dense"][:2], ("a5f527bebb6e532737aede8bc1f08c2e5dea3858", "dense"))
        self.assertEqual(fetch_code.GROUPS["dense"][2]["dense_build.py"], 14996)


if __name__ == "__main__":
    unittest.main()
