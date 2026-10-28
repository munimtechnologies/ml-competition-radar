"""Tests for nli_check.py on hand-made records and a fake scorer (standard library only).

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.
"""
import json
import os
import tempfile
import unittest

import nli_check as nc

RECORDS = [
    {"question_id": "1", "machine_generated_answers": {
        "runA": {"answer_sentences": [
            {"answer_sentence": "Drug X  helps.", "citation_assessment": [
                {"cited_pmid": "11", "evidence_relation": "Supporting", "evidence_support": "X helped."},
                {"cited_pmid": "11", "evidence_relation": "Contradicting", "evidence_support": "X failed."},
                {"cited_pmid": "12", "evidence_relation": "Not Relevant", "evidence_support": ""}]},
            {"answer_sentence": "Y is safe.", "citation_assessment": [
                {"cited_pmid": 13, "evidence_relation": "neutral",
                 "evidence_support": ["Y was", "studied."]},
                {"cited_pmid": "x", "evidence_relation": "supporting", "evidence_support": "Y ok."},
                {"cited_pmid": "14", "evidence_relation": "weird", "evidence_support": "?"}]}]},
        "runB": {"answer_sentences": [
            {"answer_sentence": "Drug X helps.", "citation_assessment": [
                {"cited_pmid": "11", "evidence_relation": "supporting",
                 "evidence_support": "X  helped."}]}]}}},
    {"question_id": "2", "machine_generated_answers": {
        "runA": {"answer_sentences": [
            {"answer_sentence": "Z works.", "citation_assessment": [
                {"cited_pmid": "21", "evidence_relation": "contradicting",
                 "evidence_support": "Z did not work."},
                {"cited_pmid": "22", "evidence_relation": "Invalid Citation",
                 "evidence_support": "Z works well."}]}]}}},
]
TABLE = {"X helped.": (0.1, 0.8, 0.1), "X failed.": (0.7, 0.1, 0.2), "Y was studied.": (0.2, 0.2, 0.6),
         "Z did not work.": (0.4, 0.3, 0.3), "Z works well.": (0.05, 0.9, 0.05)}


def fake_scorer(pairs):
    return [TABLE[p] for p, _ in pairs], {"pairs": len(pairs)}


class Parts(unittest.TestCase):
    def test_label_pmid_text(self):
        self.assertEqual(nc.label("Not Relevant"), "notrelevant")
        self.assertEqual(nc.label("Invalid_Citation"), "invalid")
        self.assertIsNone(nc.label("weird"))
        self.assertEqual(nc.pmid(" 42 "), 42)
        self.assertIsNone(nc.pmid("x"))
        self.assertIsNone(nc.pmid(True))
        self.assertEqual(nc.norm_text(["a ", " b"]), "a b")
        self.assertEqual(nc.norm_text({"a": 1}), "")

    def test_auroc_ap(self):
        self.assertEqual(nc.auroc([0.9, 0.8, 0.3, 0.1], [True, False, True, False]), 0.75)
        self.assertEqual(nc.auroc([0.5, 0.5], [True, False]), 0.5)
        self.assertIsNone(nc.auroc([0.5, 0.4], [True, True]))
        self.assertAlmostEqual(nc.average_precision([0.9, 0.8, 0.3, 0.1],
                                                    [True, False, True, False]), 5 / 6)

    def test_best_f1_prf(self):
        b = nc.best_f1([0.9, 0.8, 0.3, 0.1], [True, False, True, False])
        self.assertEqual((b["f1"], b["threshold"], b["tp"], b["fp"], b["fn"]), (0.8, 0.3, 2, 1, 0))
        self.assertIsNone(nc.best_f1([0.1], [False]))
        p = nc.prf([True, True, False], [True, False, True])
        self.assertEqual((p["tp"], p["fp"], p["fn"], p["precision"], p["f1"]), (1, 1, 1, 0.5, 0.5))
        self.assertEqual(nc.prf([False], [True])["f1"], 0.0)

    def test_fetch_model_once(self):
        calls = []

        def get(url, dest, max_bytes):
            calls.append(url)
            with open(dest, "wb") as f:
                f.write(b"x")

        with tempfile.TemporaryDirectory() as d:
            rep = nc.fetch_model(d, files=("config.json", "spm.model"), get=get)
            nc.fetch_model(d, files=("config.json", "spm.model"), get=get)
        self.assertEqual(len(calls), 2)
        self.assertIn(nc.MODEL_REV, calls[0])
        self.assertIn(nc.MODEL_ID, calls[0])
        self.assertEqual(rep["files"]["spm.model"]["bytes"], 1)


class Run(unittest.TestCase):
    def go(self, sha=None):
        def get(url, dest, max_bytes):
            self.assertEqual(url, nc.ASSESS_URL)
            with open(dest, "w", encoding="utf-8") as f:
                json.dump(RECORDS, f)
            return {"url": url}

        with tempfile.TemporaryDirectory() as d:
            res = nc.run(os.path.join(d, "biogen"), fake_scorer, sha=sha, get=get)
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
                          c["unique_pairs"], c["empty_sentence"]), (8, 1, 1, 6, 5, 0))
        self.assertEqual(c["labels"], {"supports": 3, "contradicts": 2, "neutral": 1,
                                       "notrelevant": 1, "invalid": 1})
        self.assertEqual(c["empty_passage"]["notrelevant"], 1)
        self.assertEqual(c["scored_labels"]["supports"], 2)
        self.assertEqual(res["census"], {"topic_papers": 5, "topic_papers_contradicts": 2,
                                         "topic_papers_mixed": 1})
        self.assertEqual(res["scoring"], {"pairs": 5})

    def test_metrics(self):
        res = self.go()
        e = res["entry"]
        cr = e["contradicts_vs_rest"]
        self.assertEqual((cr["n"], cr["positives"], cr["auroc"], cr["average_precision"]),
                         (6, 2, 1.0, 1.0))
        self.assertEqual((cr["argmax"]["tp"], cr["argmax"]["fp"], cr["argmax"]["f1"]), (2, 0, 1.0))
        self.assertEqual((cr["best_f1"]["f1"], cr["best_f1"]["threshold"]), (1.0, 0.4))
        sr = e["supports_vs_rest"]
        self.assertEqual((sr["auroc"], sr["argmax"]["fp"], sr["argmax"]["precision"],
                          sr["argmax"]["f1"]), (0.75, 1, 0.6667, 0.8))
        cs = e["contradicts_vs_supports"]
        self.assertEqual((cs["n"], cs["positives"], cs["auroc"]), (4, 2, 1.0))
        self.assertEqual(e["confusion"]["supports"], {"contradiction": 0, "entailment": 2, "neutral": 0})
        self.assertEqual(e["confusion"]["invalid"]["entailment"], 1)
        self.assertEqual(e["mean_p"]["supports"], [0.1, 0.8, 0.1])
        self.assertEqual((res["slot"]["n"], res["slot"]["positives"], res["slot"]["auroc"]), (5, 2, 1.0))
        self.assertEqual((res["topic_paper"]["n"], res["topic_paper"]["positives"]), (4, 2))


if __name__ == "__main__":
    unittest.main()
