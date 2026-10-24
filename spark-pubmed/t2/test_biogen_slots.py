"""Fake-data tests for biogen_slots.py (standard library only). Apache-2.0.

The fake file uses biogen_collection_v3.json's real layout (schema.json of job biogen-census-v2):
each citation_assessment entry has cited_pmid, evidence_relation and evidence_support. Expected
values are worked out by hand in the comments."""
import hashlib
import json
import os
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import biogen_slots as bsl  # noqa: E402


def s(text, cites):
    return {"answer_sentence": text, "answer_sentence_id": "1",
            "answer_sentence_relevance": "required", "citation_assessment": cites}


def c(p, rel, ev):
    return {"cited_pmid": p, "evidence_relation": rel, "evidence_support": ev}


def ans(*sents):
    return {"answer": "SENTINEL answer", "answer_sentences": list(sents), "is_answer_accurate": "yes"}


# S1 rA/0/12345678: two distinct passages, Supports + Contradicts (all_distinct, conflicting)
# S2 rA/0/22222222: one entry, no passage
# S3 rA/1/22222222: the identical passage twice, Neutral + Supports (exact_copies, conflicting)
# S4 rB/0/12345678: one entry; same sentence text as S1 after normalising
# S5 rB/1/33333333: two Not relevant entries without passages (with_null); PMID printed twice
FAKE = [{"question_id": "1", "machine_generated_answers": {
    "rA": ans(s("Alpha claim [12345678].", [c("12345678", "supporting", "pass one SENTINEL"),
                                            c("12345678", "contradicting", "pass two SENTINEL"),
                                            c("22222222", "supporting", None)]),
              s("Beta claim SENTINEL.", [c("22222222", "neutral", "same SENTINEL"),
                                         c("22222222", "supporting", "same  sentinel")])),
    "rB": ans(s("alpha  CLAIM [12345678].", [c("12345678", "supporting", "pass three SENTINEL")]),
              s("Gamma [33333333] and [33333333].", [c("33333333", "not relevant", None),
                                                     c("33333333", "not relevant", None),
                                                     c("44444444", "Weird Label", "x")])),
    "rC": ans(s("No citations SENTINEL.", None))}}]

OVER = [{"question_id": "9", "machine_generated_answers": {
    "r": ans(s("Q.", [c(str(p), "supporting", None) for p in (51, 52, 53, 54)]),
             s("R.", [c("55", "invalid citation", None), c("55", "invalid citation", None)]))}}]


def run(records):
    return bsl.analyse(bsl.entries(records), bsl.shape(records))


class Parts(unittest.TestCase):
    def test_collapse(self):
        self.assertEqual(bsl.collapse({"supports", "contradicts"}), "contradicts")
        self.assertEqual(bsl.collapse({"supports", "neutral"}), "supports")
        self.assertEqual(bsl.collapse({"neutral", "notrelevant"}), "neutral")
        self.assertEqual(bsl.collapse({"invalid", "notrelevant"}), "notrelevant")
        self.assertEqual(bsl.collapse({"invalid"}), "invalid")

    def test_kendall(self):
        self.assertEqual(bsl.kendall([1, 2, 3], [1, 2, 3]), 1.0)
        self.assertEqual(bsl.kendall([1, 2, 3], [3, 2, 1]), -1.0)
        self.assertEqual(bsl.kendall([1, 2, 3], [1, 1, 2]), 0.8165)  # 2 / sqrt(2 * 3)
        self.assertIsNone(bsl.kendall([1], [1]))

    def test_label_pmid_text(self):
        self.assertEqual(bsl.label("not  relevant"), "notrelevant")
        self.assertIsNone(bsl.label("Weird Label"))
        self.assertEqual(bsl.pmid(" 123 "), 123)
        self.assertIsNone(bsl.pmid("0"))
        self.assertEqual(bsl.text_key("same SENTINEL"), bsl.text_key("same  sentinel"))
        self.assertIsNone(bsl.text_key(None))

    def test_entries(self):
        es = bsl.entries(FAKE)
        self.assertEqual(len(es), 8)  # the Weird Label entry is skipped
        self.assertEqual([e[7] for e in es], [1, 1, 0, 0, 0, 1, 2, 2])
        self.assertEqual(es[0][3], es[5][3])  # same sentence text after normalising
        self.assertIsNone(es[2][6])


class Census(unittest.TestCase):
    def test_analyse(self):
        r = run(FAKE)
        self.assertEqual(r["entries"], 8)
        self.assertEqual(r["entry_key_sets"], {"cited_pmid,evidence_relation,evidence_support": 9})
        self.assertEqual(r["cited_sentences"], 4)
        self.assertEqual(r["entries_per_cited_sentence"], {"1": 1, "2": 1, "3": 2})
        self.assertEqual(r["pmids_per_cited_sentence"], {"1": 2, "2": 2})
        self.assertEqual((r["sentences_over_3_entries"], r["sentences_over_3_pmids"]), (0, 0))
        self.assertEqual((r["slots"], r["duplicate_slots"], r["duplicate_slots_conflicting"]), (5, 3, 2))
        self.assertEqual((r["duplicate_slot_sizes"], r["entries_in_duplicate_slots"]), ({"2": 3}, 6))
        self.assertEqual(r["duplicate_slot_passages"], {"all_distinct": 1, "with_null": 1, "exact_copies": 1})
        self.assertEqual(r["conflicting_slot_passages"], {"all_distinct": 1, "with_null": 0, "exact_copies": 1})
        self.assertEqual((r["same_passage_pairs"], r["same_passage_pairs_differ"]), (1, 1))
        self.assertEqual(r["pmid_shown_duplicate_slots"], {"0": 1, "1": 1, "2": 1})
        self.assertEqual(r["pmid_shown_single_slots"], {"0": 1, "1": 1})
        self.assertEqual(r["conflicting_slot_label_sets"], {"contradicts+supports": 1, "neutral+supports": 1})
        self.assertEqual(r["conflicting_slot_paper_label"], {"contradicts": 1, "supports": 1})
        self.assertEqual((r["runs_with_entries"], r["runs_with_duplicate_slots"]), (2, 2))
        self.assertEqual(r["largest_run_share_of_duplicate_slots"], 0.6667)
        # rA: entries 5 (3 S, 1 C); slots 3, weighted S 0.5 + 1 + 0.5, C 0.5; papers C, S, S
        # rB: entries 3 (1 S); slots 2, weighted S 1; papers S, Not relevant
        self.assertEqual(r["per_run"], {
            "rA": {"questions": 1, "entries": 5, "slots": 3, "support_rate_entries": 0.6,
                   "support_rate_slots": 0.6667, "support_rate_papers": 0.6667,
                   "contradict_rate_entries": 0.2, "contradict_rate_slots": 0.1667,
                   "contradict_rate_papers": 0.3333},
            "rB": {"questions": 1, "entries": 3, "slots": 2, "support_rate_entries": 0.3333,
                   "support_rate_slots": 0.5, "support_rate_papers": 0.5,
                   "contradict_rate_entries": 0.0, "contradict_rate_slots": 0.0,
                   "contradict_rate_papers": 0.0}})
        self.assertEqual(r["rank_compare"], {
            "support_entries_vs_slots": {"kendall_tau_b": 1.0, "max_abs_change": 0.1667, "runs_rank_changed": 0},
            "support_entries_vs_papers": {"kendall_tau_b": 1.0, "max_abs_change": 0.1667, "runs_rank_changed": 0},
            "contradict_entries_vs_papers": {"kendall_tau_b": 1.0, "max_abs_change": 0.1333,
                                             "runs_rank_changed": 0}})
        # S1 (Contradicts) and S4 (Supports) share topic, sentence text and PMID
        self.assertEqual((r["paper_level_pairs"], r["paper_level_agree"], r["paper_level_agreement"]), (1, 0, 0.0))
        self.assertEqual(r["paper_level_pair_matrix"], {"contradicts|supports": 1})
        self.assertEqual(r["paper_level_specific_agreement"], {"supports": 0.0, "contradicts": 0.0,
                                                               "neutral": None, "notrelevant": None})
        self.assertEqual(r["paper_level_scotts_pi"], -1.0)  # po 0, pe 0.5

    def test_over_three(self):
        r = run(OVER)
        self.assertEqual((r["sentences_over_3_entries"], r["sentences_over_3_pmids"]), (1, 1))
        # the doubled Invalid slot counts in the rates but not in the slot audit (as biogen_stance)
        self.assertEqual((r["slots"], r["slots_without_invalid"], r["duplicate_slots"],
                          r["largest_run_share_of_duplicate_slots"]), (5, 4, 0, None))
        self.assertEqual((r["per_run"]["r"]["support_rate_entries"], r["per_run"]["r"]["support_rate_slots"],
                          r["per_run"]["r"]["support_rate_papers"]), (0.6667, 0.8, 0.8))  # 4/6, 4/5, 4/5
        self.assertEqual(r["rank_compare"]["support_entries_vs_slots"],
                         {"kendall_tau_b": None, "max_abs_change": 0.1333, "runs_rank_changed": 0})
        self.assertEqual((r["paper_level_pairs"], r["paper_level_agreement"], r["paper_level_scotts_pi"]),
                         (0, None, None))


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
        with open(os.path.join(self.out, "slots.json"), encoding="utf-8") as f:
            return f.read()

    def test_main_ok_writes_no_text(self):
        self.put(os.path.join(self.data, "assessments.json"))
        self.assertEqual(bsl.main(["--data-dir", self.data, "--out-dir", self.out, "--sha256", self.sha]), 0)
        text = self.result()
        r = json.loads(text)
        self.assertIsNone(r["problem"])
        self.assertEqual((r["version"], r["file"]["cached"], r["duplicate_slots"]), ("0.1.0", True, 3))
        self.assertNotIn("sentinel", text.lower())
        self.assertNotIn("claim", text.lower())

    def test_main_wrong_sha(self):
        self.put(os.path.join(self.data, "assessments.json"))
        self.assertEqual(bsl.main(["--data-dir", self.data, "--out-dir", self.out, "--sha256", "0" * 64]), 1)
        self.assertIn("sha256", json.loads(self.result())["problem"])

    def test_main_downloads(self):
        src = os.path.join(self.tmp.name, "src", "collection.json")
        self.put(src)
        url = pathlib.Path(src).as_uri()
        self.assertEqual(bsl.main(["--data-dir", self.data, "--out-dir", self.out, "--url", url,
                                   "--sha256", self.sha]), 0)
        self.assertEqual(json.loads(self.result())["file"]["cached"], False)


if __name__ == "__main__":
    unittest.main()
