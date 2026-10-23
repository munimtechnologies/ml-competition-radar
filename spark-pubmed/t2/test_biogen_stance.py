"""Fake-data tests for biogen_stance.py (standard library only). Apache-2.0.

The fake file uses biogen_collection_v3.json's real layout and its literal label words, as read
from schema.json of job biogen-census-v2."""
import hashlib
import json
import os
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import biogen_stance as bs  # noqa: E402

SENTINEL = "SENTINEL abstract text that must never be copied anywhere"


def s(text, cites):
    return {"answer_sentence": text, "answer_sentence_id": "1",
            "answer_sentence_relevance": "required", "citation_assessment": cites}


def c(p, rel):
    return {"cited_pmid": p, "evidence_relation": rel, "evidence_support": SENTINEL}


def ans(*sents):
    return {"answer": SENTINEL, "answer_sentences": list(sents), "is_answer_accurate": "yes"}


FAKE = [
    {"question_id": "116", "machine_generated_answers": {
        "runA": ans(s("Claim one SENTINEL.", [c("101", "supporting"), c("103", "neutral")]),
                    s("Claim two SENTINEL.", [c("101", "contradicting")])),
        "runB": ans(s("claim   ONE sentinel.", [c("102", "supporting"), c("1", "invalid citation")]),
                    s("Other SENTINEL.", [c("104", "contradicting")])),
        "runC": ans(s("Claim one SENTINEL.", [c("102", "contradicting")]),
                    s("No citations SENTINEL.", None))}},
    {"question_id": 117, "machine_generated_answers": {
        "runA": ans(s("X SENTINEL.", [c("105", "supporting"), c("106", "Weird Label")])),
        "runB": ans(s("Y SENTINEL.", [c("105", "contradicting")]))}}]

AGREE = [{"question_id": "3", "machine_generated_answers": {
    "r1": ans(s("Same.", [c("107", "supporting")])),
    "r2": ans(s("Same.", [c("107", "supporting")])),
    "r3": ans(s("same.", [c("107", "contradicting")])),
    "r4": ans(s("Same.", [c("108", "neutral")])),
    "r5": ans(s("Same.", [c("108", "neutral")]))}}]

# one run judges the same sentence text both ways (twice in one sentence, once more later)
WITHIN = [{"question_id": "4", "machine_generated_answers": {
    "r1": ans(s("Dup.", [c("109", "supporting"), c("109", "contradicting")]),
              s("dup.", [c("109", "supporting")])),
    "r2": ans(s("Dup.", [c("109", "supporting")]))}}]


class Parts(unittest.TestCase):
    def test_label(self):
        self.assertEqual(bs.label("Supporting"), "supports")
        self.assertEqual(bs.label("contradicting"), "contradicts")
        self.assertEqual(bs.label("not  relevant"), "notrelevant")
        self.assertEqual(bs.label("Not_Relevant"), "notrelevant")
        self.assertEqual(bs.label(" Invalid Citation "), "invalid")
        self.assertIsNone(bs.label("supports"))  # not a word the file uses
        self.assertIsNone(bs.label(None))

    def test_pmid(self):
        self.assertEqual(bs.pmid("38000001"), 38000001)
        self.assertEqual(bs.pmid(" 123 "), 123)
        self.assertEqual(bs.pmid(7), 7)
        for bad in ("abc", "0", True, "1234567890", None, ""):
            self.assertIsNone(bs.pmid(bad))

    def test_text_key(self):
        self.assertIsNone(bs.text_key(""))
        self.assertIsNone(bs.text_key("   "))
        self.assertIsNone(bs.text_key(None))
        self.assertEqual(bs.text_key("A  b\n"), bs.text_key("a b"))
        self.assertNotEqual(bs.text_key("a b"), bs.text_key("a c"))

    def test_agreement_formulas(self):
        self.assertEqual(bs.agreement({}, 0, 0), (dict.fromkeys(bs.ORDER[:4]), None))
        spec, pi = bs.agreement({"supports|supports": 2}, 2, 2)  # one label only: pi undefined
        self.assertEqual((spec["supports"], spec["contradicts"], pi), (1.0, None, None))


class Census(unittest.TestCase):
    def test_judgments(self):
        js, unknown = bs.judgments(FAKE)
        self.assertEqual(len(js), 9)
        self.assertEqual(dict(unknown), {"Weird Label": 1})
        self.assertEqual({j[0] for j in js}, {"116", "117"})
        self.assertIn(("116", "runC", 0, bs.text_key("Claim one SENTINEL."), 102, "contradicts"), js)

    def test_analyse(self):
        r = bs.analyse(bs.judgments(FAKE)[0])
        self.assertEqual(r["judgments"], 9)
        self.assertEqual(r["labels"], {"supports": 3, "contradicts": 4, "neutral": 1,
                                       "notrelevant": 0, "invalid": 1})
        self.assertEqual((r["topics"], r["runs"], r["judgments_without_pmid"]), (2, 3, 0))
        self.assertEqual((r["contradicting_pairs"], r["mixed_pairs"], r["contradiction_only_pairs"]),
                         (4, 3, 1))
        # 116/101: one run, two sentences; 116/102: one sentence text in two runs; 117/105: neither
        self.assertEqual((r["mixed_same_text"], r["mixed_same_run"],
                          r["mixed_same_run_not_same_text"], r["mixed_across_only"]), (1, 1, 1, 1))
        self.assertEqual(r["mixed_same_text_within_one_run"], 0)
        self.assertEqual((r["contradicts_judgments_on_mixed_pairs"],
                          r["supports_judgments_on_mixed_pairs"]), (3, 3))
        self.assertEqual((r["mixed_supports_texts_median"], r["mixed_contradicts_texts_median"]), (1, 1))
        self.assertEqual((r["repeated_groups"], r["repeated_groups_all_agree"],
                          r["repeated_judgment_pairs"], r["repeated_pairs_agree"]), (1, 0, 1, 0))
        self.assertEqual(r["repeated_pair_agreement"], 0.0)
        self.assertEqual(r["repeated_pair_confusion"], {"contradicts|supports": 1})
        self.assertEqual(r["repeated_pair_matrix"], {"contradicts|supports": 1})
        self.assertEqual(r["specific_agreement"], {"supports": 0.0, "contradicts": 0.0,
                                                   "neutral": None, "notrelevant": None})
        self.assertEqual(r["repeated_pair_scotts_pi"], -1.0)
        self.assertEqual((r["repeated_within_run_pairs"], r["repeated_across_run_pairs"],
                          r["repeated_across_run_agree"], r["repeated_within_run_agreement"]), (0, 1, 0, None))
        self.assertEqual((r["repeated_groups_with_contradicts"],
                          r["repeated_groups_with_contradicts_all_agree"]), (1, 0))
        self.assertEqual(r["per_topic"], [
            {"topic": "116", "contradicts_judgments": 3, "contradicting_pmids": 3, "mixed_pmids": 2,
             "mixed_same_text": 1, "mixed_same_run": 1},
            {"topic": "117", "contradicts_judgments": 1, "contradicting_pmids": 1, "mixed_pmids": 1,
             "mixed_same_text": 0, "mixed_same_run": 0}])

    def test_agreement(self):
        r = bs.analyse(bs.judgments(AGREE)[0])
        self.assertEqual((r["repeated_groups"], r["repeated_groups_all_agree"]), (2, 1))
        self.assertEqual((r["repeated_judgment_pairs"], r["repeated_pairs_agree"]), (4, 2))
        self.assertEqual(r["repeated_pair_agreement"], 0.5)
        self.assertEqual(r["repeated_pair_confusion"], {"contradicts|supports": 2})
        self.assertEqual(r["repeated_pair_matrix"], {"contradicts|supports": 2, "neutral|neutral": 1,
                                                     "supports|supports": 1})
        self.assertEqual(r["specific_agreement"], {"supports": 0.5, "contradicts": 0.0,
                                                   "neutral": 1.0, "notrelevant": None})
        self.assertEqual(r["repeated_pair_scotts_pi"], 0.2)  # po 0.5, pe 0.375
        self.assertEqual((r["repeated_across_run_pairs"], r["repeated_across_run_agreement"]), (4, 0.5))
        self.assertEqual((r["mixed_pairs"], r["mixed_same_text"], r["mixed_same_run"],
                          r["mixed_across_only"], r["mixed_same_text_within_one_run"]), (1, 1, 0, 0, 0))
        self.assertEqual(r["per_topic"][0]["contradicts_judgments"], 1)

    def test_within_run(self):
        r = bs.analyse(bs.judgments(WITHIN)[0])
        self.assertEqual((r["repeated_groups"], r["repeated_judgment_pairs"], r["repeated_pairs_agree"]),
                         (1, 6, 3))
        self.assertEqual(r["repeated_pair_matrix"], {"contradicts|supports": 3, "supports|supports": 3})
        self.assertEqual((r["repeated_within_run_pairs"], r["repeated_within_run_agree"],
                          r["repeated_across_run_pairs"], r["repeated_across_run_agree"]), (3, 1, 3, 2))
        self.assertEqual((r["repeated_within_run_agreement"], r["repeated_across_run_agreement"]),
                         (0.3333, 0.6667))
        self.assertEqual(r["specific_agreement"]["supports"], 0.6667)
        self.assertEqual(r["repeated_pair_scotts_pi"], -0.3333)  # po 0.5, pe 0.625
        self.assertEqual((r["mixed_same_text"], r["mixed_same_run"], r["mixed_same_text_within_one_run"]),
                         (1, 1, 1))


class Files(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data = os.path.join(self.tmp.name, "data")
        self.out = os.path.join(self.tmp.name, "out")
        self.raw = json.dumps(FAKE).encode("utf-8")
        self.sha = hashlib.sha256(self.raw).hexdigest()

    def tearDown(self):
        self.tmp.cleanup()

    def put(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(self.raw)

    def result(self):
        with open(os.path.join(self.out, "stance.json"), encoding="utf-8") as f:
            return f.read()

    def test_main_ok_writes_no_text(self):
        self.put(os.path.join(self.data, "assessments.json"))
        self.assertEqual(bs.main(["--data-dir", self.data, "--out-dir", self.out, "--sha256", self.sha]), 0)
        text = self.result()
        r = json.loads(text)
        self.assertIsNone(r["problem"])
        self.assertEqual(r["version"], "0.2.0")
        self.assertTrue(r["file"]["cached"])
        self.assertEqual((r["mixed_pairs"], r["unknown_relations"]), (3, {"Weird Label": 1}))
        self.assertNotIn("sentinel", text.lower())

    def test_main_wrong_sha(self):
        self.put(os.path.join(self.data, "assessments.json"))
        self.assertEqual(bs.main(["--data-dir", self.data, "--out-dir", self.out, "--sha256", "0" * 64]), 1)
        self.assertIn("sha256", json.loads(self.result())["problem"])

    def test_main_downloads(self):
        src = os.path.join(self.tmp.name, "src", "collection.json")
        self.put(src)
        url = pathlib.Path(src).as_uri()
        self.assertEqual(bs.main(["--data-dir", self.data, "--out-dir", self.out, "--url", url,
                                  "--sha256", self.sha]), 0)
        r = json.loads(self.result())
        self.assertEqual((r["file"]["cached"], r["file"]["bytes"]), (False, len(self.raw)))
        self.assertTrue(os.path.exists(os.path.join(self.data, "assessments.json")))

    def test_main_missing(self):
        url = pathlib.Path(os.path.join(self.tmp.name, "missing.json")).as_uri()
        self.assertEqual(bs.main(["--data-dir", self.data, "--out-dir", self.out, "--url", url]), 1)
        self.assertTrue(json.loads(self.result())["problem"].startswith("URLError"))


if __name__ == "__main__":
    unittest.main()
