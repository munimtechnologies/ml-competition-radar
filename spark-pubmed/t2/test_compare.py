import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compare  # noqa: E402


def topic(t, cites, sup, mixed, other, unj, recall):
    return {"topic": t, "citations": cites, "supports_share": sup, "mixed_share": mixed,
            "contradicts_share": 0.0, "other_share": other, "unjudged_share": unj, "supports_recall": recall}


A = {"answers_scored": 2, "topics_with_mixed_found": 1,
     "mean_supports_share": 0.25, "mean_mixed_share": 0.125, "mean_contradicts_share": 0.0,
     "mean_other_share": 0.0, "mean_unjudged_share": 0.625, "mean_supports_recall": 0.1,
     "mean_supports_only_recall": 0.1,
     "per_topic": [topic("1", 4, 0.5, 0.25, 0.0, 0.25, 0.2), topic("2", 2, 0.0, 0.0, 0.0, 1.0, 0.0)]}
B = {"answers_scored": 3, "topics_with_mixed_found": 0,
     "mean_supports_share": 0.25, "mean_mixed_share": 0.0, "mean_contradicts_share": 0.0,
     "mean_other_share": 0.25, "mean_unjudged_share": 0.5, "mean_supports_recall": 0.05,
     "mean_supports_only_recall": 0.05,
     "per_topic": [topic("1", 4, 0.25, 0.0, 0.25, 0.5, 0.1), topic("2", 2, 0.0, 0.0, 0.0, 1.0, 0.0),
                   topic("3", 1, 1.0, 0.0, 0.0, 0.0, None)]}


class Compare(unittest.TestCase):
    def test_summary(self):
        s = compare.summary(A)
        self.assertEqual(s["judged_precision"], 1.0)
        self.assertEqual((s["citations"], s["judged_citations"], s["answers_without_judged"]), (6, 3, 1))
        self.assertEqual(s["mean_unjudged_share"], 0.625)
        self.assertEqual(compare.summary(B)["judged_precision"], 0.5)

    def test_paired(self):
        p = compare.paired(A, B)
        self.assertEqual(p["topics"], 2)
        self.assertEqual(p["supports_share"], {"a_higher": 1, "a_lower": 0, "equal": 1})
        self.assertEqual(p["unjudged_share"], {"a_higher": 0, "a_lower": 1, "equal": 1})
        self.assertEqual(p["supports_recall"], {"a_higher": 1, "a_lower": 0, "equal": 1})
        self.assertEqual(p["topics_judged_in_both"], 1)
        self.assertEqual(p["judged_precision"], {"a_higher": 1, "a_lower": 0, "equal": 0})

    def test_none_and_all_unjudged(self):
        self.assertIsNone(compare.judged_precision({"mean_unjudged_share": 1.0, "mean_supports_share": 0.0,
                                                    "mean_mixed_share": 0.0}))
        self.assertEqual(compare.updown([(None, 1.0), (0.3, None), (0.2, 0.2)]),
                         {"a_higher": 0, "a_lower": 0, "equal": 1})
        self.assertIsNone(compare.topic_precision(topic("9", 0, 0.0, 0.0, 0.0, 0.0, None)))

    def test_main(self):
        with tempfile.TemporaryDirectory() as d:
            fa, fb, fo = (os.path.join(d, n) for n in ("a.json", "b.json", "sub/out.json"))
            for path, obj in ((fa, A), (fb, B)):
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(obj, f)
            self.assertEqual(compare.main(["--a", fa, "--b", fb, "--out", fo]), 0)
            with open(fo, encoding="utf-8") as f:
                res = json.load(f)
            self.assertEqual(res["version"], "0.1.0")
            self.assertEqual(res["a"]["judged_precision"], 1.0)
            self.assertEqual(res["paired"]["topics"], 2)


if __name__ == "__main__":
    unittest.main()
