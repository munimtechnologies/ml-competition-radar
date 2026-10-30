import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bench_dtype  # noqa: E402


class Bench(unittest.TestCase):
    def test_parse_configs(self):
        self.assertEqual(bench_dtype.parse_configs("float32:2, bfloat16:4"), [("float32", 2), ("bfloat16", 4)])
        for bad in ("float16:2", "float32:0", "float32"):
            with self.assertRaises(ValueError):
                bench_dtype.parse_configs(bad)

    def test_prompt_and_summary(self):
        msgs = bench_dtype.prompt_messages(250)
        passage = msgs[1]["content"].split("\n")[1]
        self.assertEqual(len(passage.split()), 250)
        self.assertTrue(passage.startswith("The trial measured"))
        self.assertIn("Statement:\nDrug X lowers blood pressure.", msgs[1]["content"])
        self.assertEqual(bench_dtype.summarize("float32", 2, [9.0, 3.0, 1.0, 2.0])["median_s"], 2.0)
        self.assertIsNone(bench_dtype.summarize("bfloat16", 4, [130.0])["median_s"])


if __name__ == "__main__":
    unittest.main()
