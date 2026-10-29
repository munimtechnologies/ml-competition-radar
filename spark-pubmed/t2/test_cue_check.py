"""Tests for cue_check.py on hand-made records (standard library only).

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.
"""
import json
import os
import tempfile
import unittest

import cue_check as cc

RECORDS = [
    {"question_id": "1", "machine_generated_answers": {
        "runA": {"answer_sentences": [
            {"answer_sentence": "Drug X  improves survival.", "citation_assessment": [
                {"cited_pmid": "11", "evidence_relation": "Supporting",
                 "evidence_support": "X improved survival significantly."},
                {"cited_pmid": "11", "evidence_relation": "Contradicting",
                 "evidence_support": "X did not improve survival."},
                {"cited_pmid": "12", "evidence_relation": "Not Relevant", "evidence_support": ""}]},
            {"answer_sentence": "Y is safe.", "citation_assessment": [
                {"cited_pmid": 13, "evidence_relation": "neutral",
                 "evidence_support": ["Y was", "studied."]},
                {"cited_pmid": "x", "evidence_relation": "supporting", "evidence_support": "Y ok."},
                {"cited_pmid": "14", "evidence_relation": "weird", "evidence_support": "?"}]}]},
        "runB": {"answer_sentences": [
            {"answer_sentence": "Drug X improves survival.", "citation_assessment": [
                {"cited_pmid": "11", "evidence_relation": "supporting",
                 "evidence_support": "Evidence remains unclear."}]}]}}},
    {"question_id": "2", "machine_generated_answers": {
        "runA": {"answer_sentences": [
            {"answer_sentence": "Z works.", "citation_assessment": [
                {"cited_pmid": "21", "evidence_relation": "contradicting",
                 "evidence_support": "Z had no significant effect."},
                {"cited_pmid": "22", "evidence_relation": "Invalid Citation",
                 "evidence_support": "Z works well."}]}]}}},
]


class Parts(unittest.TestCase):
    def test_label_pmid_text(self):
        self.assertEqual(cc.label("Not Relevant"), "notrelevant")
        self.assertEqual(cc.label("Invalid_Citation"), "invalid")
        self.assertIsNone(cc.label("weird"))
        self.assertEqual(cc.pmid(" 42 "), 42)
        self.assertIsNone(cc.pmid("x"))
        self.assertIsNone(cc.pmid(True))
        self.assertEqual(cc.norm_text(["a ", " b"]), "a b")

    def test_features(self):
        f = cc.features("X did not improve survival.", "Drug X improves survival.")
        self.assertEqual(f, {"neg_passage": True, "null_passage": True, "hedge_passage": False,
                             "neg_sentence": False, "neg_mismatch": True, "polarity_clash": True})
        f = cc.features("Z had no significant effect.", "Z works.")
        self.assertEqual((f["null_passage"], f["neg_mismatch"], f["polarity_clash"]), (True, True, False))
        f = cc.features("Evidence remains unclear.", "Drug X improves survival.")
        self.assertEqual((f["hedge_passage"], f["neg_passage"], f["polarity_clash"]), (True, False, False))
        self.assertEqual(cc.polarity("X improved survival significantly."), "finding")
        self.assertIsNone(cc.polarity("Y was studied."))
        self.assertIsNone(cc.polarity("A significant but similar rise."))

    def test_flag_block(self):
        b = cc.flag_block([True, False, False, False], [True, True, False, False])
        self.assertEqual((b["tp"], b["fp"], b["fn"], b["fires"], b["precision"], b["recall"],
                          b["f1"], b["prevalence"], b["lift"]), (1, 1, 0, 2, 0.5, 1.0, 0.6667, 0.25, 2.0))
        b = cc.flag_block([True, False], [False, False])
        self.assertEqual((b["fires"], b["precision"], b["recall"], b["f1"], b["lift"]),
                         (0, None, 0.0, 0.0, None))


class Run(unittest.TestCase):
    def go(self, sha=None):
        def get(url, dest, max_bytes):
            self.assertEqual(url, cc.ASSESS_URL)
            with open(dest, "w", encoding="utf-8") as f:
                json.dump(RECORDS, f)
            return {"url": url}

        with tempfile.TemporaryDirectory() as d:
            res = cc.run(os.path.join(d, "biogen"), sha=sha, get=get)
        return res

    def test_sha_mismatch_stops(self):
        res = self.go(sha="0" * 64)
        self.assertTrue(res["problems"])
        self.assertNotIn("counts", res)

    def test_counts_and_census(self):
        res = self.go()
        c = res["counts"]
        self.assertEqual(res["problems"], [])
        self.assertEqual((c["judgments"], c["unknown_label"], c["no_pmid"], c["scored"],
                          c["empty_sentence"]), (8, 1, 1, 6, 0))
        self.assertEqual(c["labels"], {"supports": 3, "contradicts": 2, "neutral": 1,
                                       "notrelevant": 1, "invalid": 1})
        self.assertEqual(c["scored_labels"]["supports"], 2)
        self.assertEqual(res["census"], {"topic_papers": 5, "topic_papers_contradicts": 2,
                                         "topic_papers_mixed": 1})

    def test_metrics(self):
        res = self.go()
        self.assertEqual(res["fires_by_label"]["neg_passage"],
                         {"supports": 0, "contradicts": 2, "neutral": 0, "notrelevant": 0, "invalid": 0})
        self.assertEqual(res["rate_by_label"]["hedge_passage"],
                         {"supports": 0.5, "contradicts": 0.0, "neutral": 0.0, "notrelevant": None,
                          "invalid": 0.0})
        self.assertIsNone(res["ratio_c_to_s"]["neg_passage"])
        self.assertEqual(res["ratio_c_to_s"]["hedge_passage"], 0.0)
        r = res["contradicts_vs_rest"]
        self.assertEqual((r["neg_passage"]["n"], r["neg_passage"]["positives"], r["neg_passage"]["f1"],
                          r["neg_passage"]["prevalence"], r["neg_passage"]["lift"]),
                         (6, 2, 1.0, 0.3333, 3.0))
        self.assertEqual((r["polarity_clash"]["tp"], r["polarity_clash"]["fn"],
                          r["polarity_clash"]["f1"]), (1, 1, 0.6667))
        self.assertEqual((r["hedge_passage"]["precision"], r["hedge_passage"]["lift"]), (0.0, 0.0))
        self.assertEqual((r["neg_sentence"]["fires"], r["neg_sentence"]["precision"]), (0, None))
        v = res["contradicts_vs_supports"]["polarity_clash"]
        self.assertEqual((v["n"], v["positives"], v["tp"], v["fp"]), (4, 2, 1, 0))
        s = res["slot"]
        self.assertEqual((s["polarity_clash"]["n"], s["polarity_clash"]["positives"],
                          s["polarity_clash"]["tp"], s["polarity_clash"]["fp"]), (5, 2, 1, 0))
        self.assertEqual((s["neg_mismatch"]["tp"], s["neg_mismatch"]["fp"]), (2, 0))


if __name__ == "__main__":
    unittest.main()
