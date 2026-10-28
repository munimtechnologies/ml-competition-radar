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
            self.assertEqual(rep["version"], "0.2.0")
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
        self.assertEqual(sorted(fetch_code.GROUPS),
                         ["prf", "rerank", "system", "t1", "t2", "t2dev"])
        for commit, folder, want in fetch_code.GROUPS.values():
            self.assertEqual(len(commit), 40)
            self.assertTrue(all(n.endswith(".py") and s > 0 for n, s in want.items()))
        self.assertEqual(json.loads(json.dumps(fetch_code.GROUPS))["t1"][2]["t1.py"], 12240)
        self.assertEqual(fetch_code.GROUPS["prf"][:2], ("3ea7684edd27289353be78202041f24f308e342f", "prf"))
        self.assertEqual(fetch_code.GROUPS["system"][2]["spark_t1.py"], 10821)
        self.assertEqual(fetch_code.GROUPS["t2dev"][:2], fetch_code.GROUPS["system"][0:1] + ("t2",))

    def test_no_name_in_two_groups(self):
        # spark43 fetches t1, t2, rerank, system and t2dev together: no file name may repeat
        names = [n for g in ("t1", "t2", "rerank", "system", "t2dev")
                 for n in fetch_code.GROUPS[g][2]]
        self.assertEqual(len(names), len(set(names)))


if __name__ == "__main__":
    unittest.main()
