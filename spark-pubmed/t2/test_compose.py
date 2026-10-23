"""Fake-data tests for compose.py (standard library only). Apache-2.0."""
import json
import os
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compose as c2  # noqa: E402

Q = "does drug x reduce migraine pain"
S0 = "Drug X significantly reduced migraine pain in adults."
S2 = "Drug X did not reduce migraine pain compared with placebo."
S5 = "Evidence on long term use remains unclear for migraine."
DOCS = [("11", "t", S0 + " Patients were enrolled from three clinics."),
        ("22", "t", S2 + " The trial ran for twelve weeks."),
        ("33", "t", S0 + " " + S5)]


class Text(unittest.TestCase):
    def test_split(self):
        text = ("BACKGROUND: Aspirin lowers risk in adults (Smith et al. 2001). It was studied e.g. "
                "in large trials. Short. Results were clear in 2 groups.")
        self.assertEqual(c2.split_sentences(text),
                         ["Aspirin lowers risk in adults (Smith et al. 2001).",
                          "It was studied e.g. in large trials.", "Results were clear in 2 groups."])
        self.assertEqual(len(c2.split_sentences("She played a grand piano. Then everyone left the hall.")), 2)
        self.assertEqual(c2.split_sentences(""), [])

    def test_polarity(self):
        self.assertEqual(c2.polarity("Drug X did not significantly reduce pain."), "null")
        self.assertEqual(c2.polarity("No significant difference in pain was seen."), "null")
        self.assertEqual(c2.polarity("Drug X significantly reduced pain."), "finding")
        self.assertIsNone(c2.polarity("Pain was measured weekly."))

    def test_bm25(self):
        s = c2.bm25_scores(["a", "b"], [["a", "b"], ["a"], ["c"]])
        self.assertGreater(s[0], s[1])
        self.assertGreater(s[1], 0)
        self.assertEqual(s[2], 0.0)
        self.assertEqual(c2.bm25_scores(["a"], []), [])


class Compose(unittest.TestCase):
    def test_fixture(self):
        a = c2.compose(Q, DOCS)
        self.assertEqual(a["responses"], [
            {"text": S2, "citations": ["22"], "role": "evidence"},
            {"text": S0, "citations": ["11", "33"], "role": "evidence"}])  # near-copy -> citation
        self.assertEqual(a["conflicts"], [{"pmids": ["22", "11"], "sentences": [0, 1]}])
        self.assertEqual(a["uncertain"], [])
        self.assertEqual(a["words"], 18)

    def test_grounded(self):
        a = c2.compose(Q, DOCS, min_rel=0.0)
        src = {p: abstract for p, _, abstract in DOCS}
        for r in a["responses"]:
            self.assertIn(r["text"], src[r["citations"][0]])
        self.assertEqual(a["responses"][2], {"text": S5, "citations": ["33"], "role": "evidence"})
        self.assertEqual(a["uncertain"], [2])
        self.assertEqual(a["words"], 27)
        self.assertEqual(len(a["conflicts"]), 1)

    def test_budget(self):
        a = c2.compose(Q, DOCS, words=12)
        self.assertEqual([r["text"] for r in a["responses"]], [S2])
        self.assertEqual((a["words"], a["conflicts"]), (10, []))

    def test_per_doc_and_empty(self):
        a = c2.compose(Q, [("9", "t", S0 + " " + S2 + " Drug use and migraine pain were common.")], per_doc=1)
        self.assertEqual(len(a["responses"]), 1)
        self.assertEqual(a["conflicts"], [])  # one article cannot conflict with itself
        self.assertEqual(c2.compose(Q, [])["responses"], [])


class Formats(unittest.TestCase):
    def test_validate(self):
        ok = {"info_need_id": "1", "responses": [{"text": "a b c", "citations": ["1", "2", "3"]}]}
        self.assertEqual(c2.validate([ok]), [])
        many = {"info_need_id": "2", "responses": [{"text": "a", "citations": ["1", "2", "3", "4"]}]}
        dup = {"info_need_id": "3", "responses": [{"text": "a", "citations": ["1", "1"]}]}
        long_ = {"info_need_id": "4", "responses": [{"text": "w " * 300, "citations": []}]}
        wide = {"info_need_id": "5", "responses": [{"text": "a", "citations": [str(3 * i + k) for k in range(3)]}
                                                   for i in range(11)]}
        probs = c2.validate([many, dup, long_, wide])
        self.assertEqual(len(probs), 4)
        self.assertTrue(probs[2].startswith("4: 300 words"))
        self.assertTrue(probs[3].startswith("5: 33 documents"))

    def test_biogen_rows_and_needs(self):
        rows = c2.biogen_rows([{"info_need_id": "116", "responses": [
            {"text": "a", "citations": ["1"], "role": "evidence"}], "conflicts": []}], "T", "T-r1")
        self.assertEqual(rows, [{"metadata": {"team_id": "T", "run_id": "T-r1", "topic_id": "116"},
                                 "responses": [{"text": "a", "citations": ["1"]}]}])
        self.assertEqual(c2.needs_from_topics({"topics": [{"id": 116, "question": "q?", "topic": "t"}]}),
                         [{"info_need_id": "116", "info_need": "q?"}])

    def test_stance_class(self):
        sup, con, other = {"1", "2"}, {"2", "3"}, {"1", "4"}
        self.assertEqual([c2.stance_class(p, sup, con, other) for p in ("1", "2", "3", "4", "5")],
                         ["supports", "mixed", "contradicts", "other", "unjudged"])

    def test_score(self):
        # 116 cites one PMID of each class: 1 supports (also not relevant elsewhere), 2 mixed,
        # 3 unjudged, 7 contradicts only, 8 neutral only; 117's only citation is mixed
        answers = [{"info_need_id": "116", "responses": [{"text": "a", "citations": ["1", "2", "3"]},
                                                         {"text": "b", "citations": ["7", "8"]}],
                    "conflicts": [{"pmids": ["2", "7"]}]},
                   {"info_need_id": "117", "responses": [{"text": "c", "citations": ["9"]}]},
                   {"info_need_id": "999", "responses": []}]
        gold = [{"topic": "116", "supports": [1, 4, 2, 6], "contradicts": [2, 7], "neutral": [8],
                 "notrelevant": [5, 1]},
                {"topic": "117", "supports": [9], "contradicts": [9], "neutral": [], "notrelevant": []}]
        s = c2.score(answers, gold)
        self.assertEqual((s["answers_scored"], s["answers_without_gold"]), (2, 1))
        p = s["per_topic"][0]
        self.assertEqual([p[k + "_share"] for k in c2.CLASSES], [0.2] * 5)
        self.assertAlmostEqual(sum(p[k + "_share"] for k in c2.CLASSES), 1.0)
        self.assertEqual((p["supports_recall"], round(p["supports_only_recall"], 4)), (0.5, 0.3333))
        self.assertEqual((p["mixed_found"], p["mixed_known"], p["contradicts_only_found"],
                          p["contradicts_only_known"]), (1, 1, 1, 1))
        self.assertEqual((p["conflict_flag_hits_mixed"], p["conflict_flag_hits_contradicts_only"]), (1, 1))
        q = s["per_topic"][1]
        self.assertEqual((q["mixed_share"], q["supports_share"], q["supports_only_recall"]), (1.0, 0.0, None))
        self.assertEqual((s["mean_supports_share"], s["mean_mixed_share"], s["mean_contradicts_share"],
                          s["mean_other_share"], s["mean_unjudged_share"]), (0.1, 0.6, 0.1, 0.1, 0.1))
        self.assertEqual((s["mean_supports_recall"], s["mean_supports_only_recall"]), (0.75, 0.3333))
        self.assertEqual((s["topics_with_mixed_found"], s["topics_with_mixed_known"],
                          s["topics_with_contradicts_only_found"], s["topics_with_contradicts_only_known"]),
                         (2, 2, 1, 1))


class Run(unittest.TestCase):
    def test_run_and_main(self):
        with tempfile.TemporaryDirectory() as d:
            db = os.path.join(d, "x.db")
            con = sqlite3.connect(db)
            con.execute("CREATE TABLE docs (title TEXT, abstract TEXT)")
            for p, t, ab in DOCS + [("44", "t", "")]:
                con.execute("INSERT INTO docs (rowid, title, abstract) VALUES (?, ?, ?)", (int(p), t, ab))
            con.commit()
            con.close()
            ranked = os.path.join(d, "ranked.jsonl")
            c2.write_jsonl(ranked, [{"info_need_id": "N1", "info_need": Q,
                                     "candidates": [[11, 5.0], [22, 4.0], [44, 3.0], [33, 2.0]]}])
            out = os.path.join(d, "out")
            self.assertEqual(c2.main(["compose", "--db", db, "--ranked", ranked, "--out-dir", out]), 0)
            with open(os.path.join(out, "compose.json"), encoding="utf-8") as f:
                s = json.load(f)
            self.assertEqual((s["needs"], s["empty"], s["needs_with_conflict"], s["validate"]), (1, 0, 1, []))
            row = c2.load_jsonl(os.path.join(out, "answers.jsonl"))[0]
            self.assertEqual(row["docs_with_abstract"], 3)
            self.assertEqual(row["responses"], c2.compose(Q, DOCS)["responses"])
            bg = os.path.join(d, "run.jsonl")
            self.assertEqual(c2.main(["biogen", "--answers", os.path.join(out, "answers.jsonl"),
                                      "--team-id", "T", "--run-id", "T-1", "--out", bg]), 0)
            self.assertEqual(c2.load_jsonl(bg)[0]["metadata"]["topic_id"], "N1")
            gold = os.path.join(d, "gold.jsonl")
            c2.write_jsonl(gold, [{"topic": "N1", "supports": [11], "contradicts": [22, 11],
                                   "neutral": [], "notrelevant": []}])
            self.assertEqual(c2.main(["score", "--answers", os.path.join(out, "answers.jsonl"),
                                      "--gold", gold, "--out-dir", out]), 0)
            with open(os.path.join(out, "scores.json"), encoding="utf-8") as f:
                sc = json.load(f)
            # cites 22, 11, 33: one contradicts-only, one mixed, one unjudged; both flagged
            self.assertEqual((sc["per_topic"][0]["mixed_found"], sc["per_topic"][0]["contradicts_only_found"],
                              sc["per_topic"][0]["conflict_flag_hits_mixed"]), (1, 1, 1))
            with self.assertRaises(FileNotFoundError):
                c2.run(os.path.join(d, "missing.db"), ranked, out)


if __name__ == "__main__":
    unittest.main()
