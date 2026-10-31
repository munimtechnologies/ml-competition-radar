"""Tests for mv2_nugget.py (MV2 of Munim, Inc.; made with AI agents working in his name). Apache-2.0."""
import json
import os
import tempfile
import unittest

import mv2_nugget as mv


def fs(*words):
    return frozenset(words)


class TestMv2Nugget(unittest.TestCase):
    def test_cut(self):
        rows = [(None, fs("a", "b")), (None, fs("c", "d", "e")), (None, fs("f"))]
        self.assertEqual(len(mv.cut(rows, None)), 3)
        self.assertEqual(mv.cut(rows, 0), [])
        self.assertEqual(mv.cut(rows, 1), rows[:1])  # the first sentence is always kept
        self.assertEqual(mv.cut(rows, 5), rows[:2])
        self.assertEqual(mv.cut(rows, 4), rows[:1])  # stops at the first sentence that does not fit

    def test_recall(self):
        nug = [fs("aspirin", "fever"), fs("eases", "pain")]
        rows = [(None, fs("aspirin", "lowers", "fever"))]
        self.assertEqual(mv.recall(rows, nug), 0.5)
        self.assertEqual(mv.recall([], nug), 0.0)
        self.assertIsNone(mv.recall(rows, []))

    def test_ceiling(self):
        nug = [fs("a", "b"), fs("c", "d"), fs("e", "f")]
        rows = [(None, fs("a", "b", "x")), (None, fs("c", "d", "e", "f", "y", "z")), (None, fs("c", "d", "q"))]
        self.assertEqual(mv.ceiling(rows, nug, None), 1.0)
        self.assertAlmostEqual(mv.ceiling(rows, nug, 6), 2 / 3)
        self.assertAlmostEqual(mv.ceiling(rows, nug, 5), 1 / 3)  # ties go to the earlier sentence
        self.assertIsNone(mv.ceiling(rows, [], 5))

    def test_load_mv2(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "answers.jsonl")
            with open(path, "w", encoding="utf-8") as f:
                f.write(json.dumps({"info_need_id": "116", "responses": [
                    {"text": "Aspirin lowers fever [PMID: 1].", "citations": ["1"], "role": "evidence"},
                    {"text": "It eases pain.", "citations": ["2"], "role": "evidence"}]}) + "\n")
                f.write(json.dumps({"info_need_id": 117, "responses": []}) + "\n\n")
            got = mv.load_mv2(path)
        self.assertEqual(sorted(got), ["116", "117"])
        self.assertEqual(got["116"], [(None, fs("aspirin", "lowers", "fever")), (None, fs("eases", "pain"))])
        self.assertEqual(got["117"], [])

    def test_map_topics(self):
        expert = {"1": {"question": fs("aspirin", "fever")}, "2": {"question": fs("statin", "muscle", "pain")},
                  "3": {"question": fs("zzz")}}
        qmap = {"1": "116", "2": "2", "3": "3"}
        mv2 = {"116": [], "117": []}
        tq = {"116": fs("aspirin", "fever"), "117": fs("statin", "muscle", "pain")}
        out, how = mv.map_topics(qmap, mv2, expert, tq)
        self.assertEqual(out, {"1": "116", "2": "117"})
        self.assertEqual(how, {"by_id": 1, "by_text": 1, "unmatched": 1, "min_text_dice": 1.0})

    def test_compare(self):
        expert = {"1": {"nuggets": [fs("a", "b"), fs("c", "d")]}}
        data = {"116": {"A": [("required", fs("a", "b", "x"))],
                        "B": [("required", fs("c", "d", "y")), ("unnecessary", fs("a", "b", "z"))]}}
        mv2 = {"116": [(None, fs("p", "q", "r")), (None, fs("a", "b", "c", "d"))]}
        res, per = mv.compare(expert, {"1": "116"}, data, mv2, {"1": "116"})
        m = res["matched_length"]
        self.assertEqual((m["runs_beaten"], m["runs_tied"], m["runs_beaten_by_ceiling"]), (0, 0, 0))
        self.assertEqual((m["mean_gap"], m["mean_ceiling_gap"], m["mean_word_shortfall"]), (-75.0, -25.0, 1.5))
        self.assertEqual(m["per_run"]["A"]["questions_mv2_lower"], 1)
        self.assertEqual(m["per_run"]["B"]["mv2_ceiling"], 100.0)
        f = res["fixed_budget"]["40"]
        self.assertEqual((f["mv2_recall"], f["mv2_rank"], f["of"], f["runs_median"]), (100.0, 1, 3, 75.0))
        self.assertEqual(res["mv2_answered"], 1)
        self.assertEqual(res["mv2_shuffled_recall"], 100.0)  # one question: its own nuggets
        self.assertEqual(per["MV2"]["content_words_per_question"], 7)
        self.assertEqual(per["A"]["recall"]["all"], 50.0)

    def test_main_records_problem(self):
        with tempfile.TemporaryDirectory() as d:
            for name in ("topics.json", "assessments.json", os.path.join("med", "medaesqa_v1.json")):
                os.makedirs(os.path.dirname(os.path.join(d, name)), exist_ok=True)
                with open(os.path.join(d, name), "w", encoding="utf-8") as f:
                    f.write("{}")
            out = os.path.join(d, "out")
            code = mv.main(["--data-dir", d, "--medaesqa-dir", os.path.join(d, "med"), "--official", "x.json",
                            "--answers", "x.jsonl", "--out-dir", out])
            with open(os.path.join(out, "mv2_nugget.json"), encoding="utf-8") as f:
                res = json.load(f)
        self.assertEqual(code, 1)
        self.assertTrue(res["problem"].startswith("ValueError"))


if __name__ == "__main__":
    unittest.main()
