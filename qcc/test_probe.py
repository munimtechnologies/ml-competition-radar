"""Fake-data tests for probe.py (no kickmix needed). Apache-2.0."""
import os
import tempfile
import types
import unittest

import probe


class Fake:
    """A fake circuit class."""

    def gates(self, n):
        """Return n gates."""
        return n

    def _hidden(self):
        return 0


def make_module():
    m = types.ModuleType("fake")
    m.Fake = Fake
    m.CONST = 3
    m._private = 1

    def build(a, b=2):
        """Build something.

        More text."""
        return a + b

    m.build = build
    return m


class TestProbe(unittest.TestCase):
    def test_walk_skips_private_and_lists_members(self):
        api = probe.walk(make_module())
        self.assertEqual(sorted(api), ["CONST", "Fake", "build"])
        self.assertEqual(api["build"]["signature"], "(a, b=2)")
        self.assertTrue(api["build"]["doc"].startswith("Build something."))
        self.assertIn("gates", api["Fake"]["members"])
        self.assertIn("__init__", api["Fake"]["members"])
        self.assertNotIn("_hidden", api["Fake"]["members"])
        self.assertEqual(api["CONST"]["kind"], "int")

    def test_first_line(self):
        self.assertEqual(probe.first_line("  one\ntwo"), "one")
        self.assertEqual(probe.first_line(None), "")

    def test_list_sources(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "kickmix"))
            with open(os.path.join(d, "kickmix", "a.py"), "w", encoding="utf-8") as f:
                f.write('"""Adds things.\n\nMore."""\nx = 1\n')
            with open(os.path.join(d, "kickmix", "b.cc"), "w", encoding="utf-8") as f:
                f.write("int x;\n")
            rows = probe.list_sources(d)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["path"], "kickmix/a.py")
            self.assertEqual(rows[0]["doc"], "Adds things.")
            self.assertEqual(rows[0]["lines"], 4)


if __name__ == "__main__":
    unittest.main()
