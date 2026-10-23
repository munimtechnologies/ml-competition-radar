"""Fake-data tests for biogen_census.py (standard library only). Apache-2.0."""
import hashlib
import json
import os
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import biogen_census as bc  # noqa: E402

SENTINEL = "SENTINEL answer sentence that must never be copied anywhere"
PHRASE = "first topic words here"

# layout 1: {"topics": [topic, ...]}, citation records with a pmid field
A = {"topics": [
    {"id": 116, "topic": PHRASE, "answers": [{"run": "r1", "sentences": [
        {"text": SENTINEL, "label": "Required", "citations": [
            {"pmid": "101", "label": "Supports"}, {"pmid": "102", "label": "Contradicts"}]},
        {"text": SENTINEL, "label": "Borderline", "citations": [
            {"pmid": "101", "label": "Not Relevant"}]}]}]},
    {"id": 117, "topic": "second", "answers": [{"run": "r1", "sentences": [
        {"text": SENTINEL, "label": "unnecessary", "citations": [
            {"pmid": 103, "label": "NEUTRAL"}, {"pmid": "PMID: 104", "label": "supports"}]}]}]}]}

# layout 2: dict keyed by topic, labels keyed by PMID
B = {"116": {"sentences": [{"label": "Required", "judgments": {"201": "Supports",
                                                             "202": {"label": "Contradicts"}}}]},
     "117": {"sentences": [{"label": "Inappropriate", "judgments": {"201": "Contradicts"}},
                           {"label": "Required", "judgments": {"201": "Supports"}}]}}

# layout 3: one record per run answer, grouped by topic_id
C = [{"id": "a1", "topic_id": 116, "citations": [{"doc_id": 5, "label": "Neutral"}]},
     {"id": "a2", "topic_id": 116, "citations": [{"doc_id": 6, "label": "Supports"}]},
     {"id": "a3", "topic_id": 117, "citations": [{"doc_id": 5, "label": "Supports"}, {"label": "Supports"}]}]


class Labels(unittest.TestCase):
    def test_label_of(self):
        self.assertEqual(bc.label_of("Not Relevant"), ("cite", "notrelevant"))
        self.assertEqual(bc.label_of("not_relevant"), ("cite", "notrelevant"))
        self.assertEqual(bc.label_of(" SUPPORTS "), ("cite", "supports"))
        self.assertEqual(bc.label_of("Borderline"), ("sent", "borderline"))
        self.assertIsNone(bc.label_of("supported"))
        self.assertIsNone(bc.label_of(3))

    def test_pmid_of(self):
        self.assertEqual(bc.pmid_of(123), 123)
        self.assertEqual(bc.pmid_of(" 123 "), 123)
        self.assertEqual(bc.pmid_of("PMID: 123"), 123)
        self.assertEqual(bc.pmid_of("pmid123"), 123)
        for bad in (True, 0, "0", "12a", "", None, 1.5, [1]):
            self.assertIsNone(bc.pmid_of(bad), bad)


class Schema(unittest.TestCase):
    def test_paths_and_values(self):
        s = bc.schema(A)
        self.assertEqual(s["$.topics"]["types"], {"list": 1})
        self.assertEqual(s["$.topics[]"]["count"], 2)
        self.assertEqual((s["$.topics[].id"]["min"], s["$.topics[].id"]["max"]), (116, 117))
        self.assertEqual(s["$.topics[].topic"]["values"], ["second"])  # 4-word phrase not kept
        self.assertEqual(s["$.topics[].answers[].sentences[].citations[].label"]["values"],
                         ["Contradicts", "NEUTRAL", "Not Relevant", "Supports", "supports"])
        self.assertIsNone(s["$.topics[].answers[].sentences[].text"]["values"])

    def test_folding(self):
        s = bc.schema(B)
        self.assertIn("$.{n}", s)
        self.assertEqual(s["$.{n}.sentences[].judgments.{n}"]["types"], {"str": 3, "dict": 1})
        self.assertIn("$.{text}", bc.schema({"a phrase key": 1}))

    def test_many_values(self):
        s = bc.schema({"x": ["%da" % i for i in range(25)]})
        self.assertTrue(s["$.x[]"]["many_values"])
        self.assertIsNone(s["$.x[]"]["values"])


class Census(unittest.TestCase):
    def test_records(self):
        c, gold = bc.census(A, [116, 117])
        self.assertEqual((c["units"], c["topics"], c["units_per_topic_max"]), (2, 2, 1))
        self.assertEqual(c["sentence_labels"],
                         {"required": 1, "unnecessary": 1, "borderline": 1, "inappropriate": 0})
        self.assertEqual(c["citation_labels"],
                         {"supports": 2, "contradicts": 1, "neutral": 1, "notrelevant": 1})
        self.assertEqual(c["citation_label_share"]["supports"], 0.4)
        self.assertEqual(c["pmid_pattern"], {"record": 5})
        self.assertEqual(c["citations_without_pmid"], 0)
        self.assertEqual(c["topics_with_contradicts"], 1)
        self.assertEqual(c["contradicts_per_topic_median"], 0.5)
        self.assertEqual(c["distinct_pmids"], 4)
        self.assertEqual(c["distinct_pmids_by_label"],
                         {"supports": 2, "contradicts": 1, "neutral": 1, "notrelevant": 1})
        self.assertEqual(c["topic_pmid_pairs_supports_and_contradicts"], 0)
        self.assertEqual((c["pmid_min"], c["pmid_max"], c["pmids_over_spark_max"]), (101, 104, 0))
        self.assertEqual(c["topic_keys_matching_topic_ids"], 2)
        self.assertEqual([g["topic"] for g in gold], ["116", "117"])
        self.assertEqual((gold[0]["supports"], gold[0]["contradicts"], gold[0]["notrelevant"]),
                         ([101], [102], [101]))
        self.assertEqual(gold[1]["supports"], [104])

    def test_keyed(self):
        c, gold = bc.census(B)
        self.assertEqual(c["pmid_pattern"], {"keyed": 4})
        self.assertEqual(c["topics_with_contradicts"], 2)
        self.assertEqual(c["contradicts_per_topic_median"], 1)
        self.assertEqual(c["distinct_pmids_by_label"]["contradicts"], 2)
        self.assertEqual(c["topic_pmid_pairs_supports_and_contradicts"], 1)
        self.assertEqual(c["sentence_labels"]["inappropriate"], 1)
        self.assertNotIn("topic_keys_matching_topic_ids", c)
        self.assertEqual(gold[1], {"topic": "117", "supports": [201], "contradicts": [201],
                                   "neutral": [], "notrelevant": [],
                                   "sentence_labels": {"required": 1, "unnecessary": 0,
                                                       "borderline": 0, "inappropriate": 1},
                                   "citations_without_pmid": 0})

    def test_grouped_by_topic_id(self):
        c, gold = bc.census(C, [116, 117])
        self.assertEqual((c["units"], c["topics"], c["units_per_topic_max"]), (3, 2, 2))
        self.assertEqual(c["citation_labels"]["supports"], 3)
        self.assertEqual(c["citations_without_pmid"], 1)
        self.assertEqual(c["pmid_pattern"], {"record": 3})
        self.assertEqual(c["topic_keys_matching_topic_ids"], 2)
        self.assertEqual(gold[0]["supports"], [6])

    def test_phrase_keys_never_become_topics(self):
        _, gold = bc.census({"a phrase key": {"label": "Required"}, "x": {"label": "Required"}})
        self.assertEqual([g["topic"] for g in gold], ["0", "x"])


class Files(unittest.TestCase):
    def test_download_and_cache(self):
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "src.bin")
            with open(src, "wb") as f:
                f.write(b"x" * 1000)
            url = pathlib.Path(src).as_uri()
            r = bc.download(url, os.path.join(d, "dl", "a.bin"), 5000)
            self.assertEqual((r["bytes"], r["cached"]), (1000, False))
            self.assertEqual(r["sha256"], hashlib.sha256(b"x" * 1000).hexdigest())
            r2 = bc.download(url, os.path.join(d, "dl", "a.bin"), 5000)
            self.assertEqual((r2["sha256"], r2["cached"]), (r["sha256"], True))
            with self.assertRaises(ValueError):
                bc.download(url, os.path.join(d, "dl", "b.bin"), 3)
            self.assertFalse(os.path.exists(os.path.join(d, "dl", "b.bin")))

    def test_main_writes_no_text(self):
        with tempfile.TemporaryDirectory() as d:
            tp, ap_ = os.path.join(d, "t.json"), os.path.join(d, "a.json")
            with open(tp, "w", encoding="utf-8") as f:
                json.dump({"topics": [{"id": i, "topic": PHRASE, "question": SENTINEL,
                                       "narrative": SENTINEL} for i in (116, 117)]}, f)
            with open(ap_, "w", encoding="utf-8") as f:
                json.dump(A, f)
            out = os.path.join(d, "out")
            rc = bc.main(["--data-dir", os.path.join(d, "data"), "--out-dir", out,
                          "--topics-url", pathlib.Path(tp).as_uri(),
                          "--assess-url", pathlib.Path(ap_).as_uri()])
            self.assertEqual(rc, 0)
            with open(os.path.join(out, "census.json"), encoding="utf-8") as f:
                c = json.load(f)
            self.assertIsNone(c["problem"])
            self.assertEqual(c["topics"], 2)
            with open(os.path.join(out, "topics.json"), encoding="utf-8") as f:
                t = json.load(f)
            self.assertEqual((t["topics"], t["id_min"], t["id_max"], t["contiguous"]), (2, 116, 117, True))
            with open(os.path.join(out, "gold_t2.jsonl"), encoding="utf-8") as f:
                self.assertEqual(len([ln for ln in f if ln.strip()]), 2)
            for name in sorted(os.listdir(out)):
                with open(os.path.join(out, name), encoding="utf-8") as f:
                    body = f.read()
                self.assertNotIn("SENTINEL", body, name)
                self.assertNotIn(PHRASE, body, name)

    def test_main_records_problem(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "out")
            rc = bc.main(["--data-dir", os.path.join(d, "data"), "--out-dir", out,
                          "--topics-url", pathlib.Path(os.path.join(d, "missing.json")).as_uri()])
            self.assertEqual(rc, 1)
            with open(os.path.join(out, "census.json"), encoding="utf-8") as f:
                self.assertIn("URLError", json.load(f)["problem"])


if __name__ == "__main__":
    unittest.main()
