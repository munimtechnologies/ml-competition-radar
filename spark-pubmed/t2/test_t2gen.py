"""Tests for t2gen.py (standard library only; no model is loaded).
MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0."""
import hashlib
import json
import os
import tempfile
import unittest

import t2gen as g

SHOWN = ["Statins lower LDL cholesterol in adults with diabetes by thirty percent overall",
         "Exercise improves blood pressure control in older adults"]
OTHER = ["Vitamin D supplements did not prevent fractures"]
TEXT = ("Statins lower LDL cholesterol in adults with diabetes by thirty percent overall [1]. Exercise helps [2]. "
        "Exercise improves blood pressure in older adults [9].")
XML = (b'<?xml version="1.0" ?>\n<!DOCTYPE PubmedArticleSet PUBLIC "-//NLM//DTD PubMedArticle, 1st January 2025//EN" '
       b'"https://dtd.nlm.nih.gov/ncbi/pubmed/out/pubmed_250101.dtd">\n<PubmedArticleSet>'
       b'<PubmedArticle><MedlineCitation><PMID Version="1">111111</PMID><Article><ArticleTitle>A <i>trial</i> of X.'
       b'</ArticleTitle><Abstract><AbstractText Label="BACKGROUND">Back  ground.</AbstractText>'
       b'<AbstractText Label="RESULTS">X worked.</AbstractText></Abstract></Article></MedlineCitation></PubmedArticle>'
       b'<PubmedArticle><MedlineCitation><PMID Version="1">222222</PMID><Article><ArticleTitle>No abstract'
       b'</ArticleTitle></Article></MedlineCitation></PubmedArticle></PubmedArticleSet>')


def article(pmid, title, abstract):
    return ("<PubmedArticle><MedlineCitation><PMID Version=\"1\">%s</PMID><Article><ArticleTitle>%s</ArticleTitle>"
            "<Abstract><AbstractText>%s</AbstractText></Abstract></Article></MedlineCitation></PubmedArticle>"
            % (pmid, title, abstract))


class T2genTest(unittest.TestCase):
    def test_split_moves_leading_citations(self):
        self.assertEqual(g.split_sentences("Statins lower LDL. [1] They also cut events [2][3]. Done."),
                         ["Statins lower LDL. [1]", "They also cut events [2][3].", "Done."])

    def test_split_bullets_and_lines(self):
        self.assertEqual(g.split_sentences("- First point here [1].\n\n2. Second **point** [9]."),
                         ["First point here [1].", "Second point [9]."])

    def test_cites_valid_and_invalid(self):
        self.assertEqual(g.cites("They cut events [2][3, 9].", 8), ([2, 3], [9]))
        self.assertEqual(g.cites("No citation.", 8), ([], []))

    def test_content_and_clean(self):
        self.assertEqual(g.content(g.clean("The LDL-cholesterol fell by 30% in 2 trials [1].")),
                         {"ldl-cholesterol", "fell", "30", "2", "trials"})
        self.assertEqual(g.clean("x (PMID: 12345678) y").split(), ["x", "(PMID:", ")", "y"])

    def test_ground(self):
        self.assertEqual(g.ground({"x", "y", "z", "w"}, {"x", "y", "q"}), 0.5)
        self.assertIsNone(g.ground(set(), {"x"}))

    def test_expert_pmids(self):
        text = "Statins help [12345678, 23456789]. Also PMID:34567890 and (n=1,234,567) in 2019 [12345678,45678901]. 1234567.5"
        self.assertEqual(g.expert_pmids(text), ["12345678", "23456789", "34567890", "45678901"])

    def test_supported_pmids(self):
        unit = {"machine_generated_answers": {
            "M1": {"answer_sentences": [{"citation_assessment": [
                {"cited_pmid": "111", "evidence_relation": "Supports"},
                {"cited_pmid": "222", "evidence_relation": "Contradicts"}]}]},
            "M2": {"answer_sentences": [{"citation_assessment": [
                {"cited_pmid": "333", "evidence_relation": "Supports"},
                {"cited_pmid": "111", "evidence_relation": "supports"}]}, {"citation_assessment": None}]}}}
        self.assertEqual(g.supported_pmids(unit), ["111", "333"])

    def test_analyse_answer(self):
        res = g.analyse_answer(TEXT, SHOWN, OTHER)
        self.assertEqual(res["sentences"], 3)
        self.assertEqual(res["words"], 21)
        self.assertFalse(res["declines"])
        r0, r1, r2 = res["rows"]
        self.assertEqual(r0["valid"], [1])
        self.assertEqual(r0["content_words"], 9)
        self.assertEqual(r0["ground_cited"], 1.0)
        self.assertTrue(r0["cites_best"])
        self.assertTrue(r0["verbatim"])
        self.assertEqual(r0["ground_other"], 0.0)
        self.assertFalse(r1["scored"])
        self.assertEqual(r1["valid"], [2])
        self.assertEqual(r2["invalid"], 1)
        self.assertNotIn("ground_cited", r2)
        self.assertEqual(r2["ground_any"], 1.0)
        self.assertFalse(r2["verbatim"])

    def test_aggregate(self):
        q1 = {"id": "1", "seconds": 10.0, "prompt_tokens": 100, "new_tokens": 50, "truncated": False,
              **g.analyse_answer(TEXT, SHOWN, OTHER)}
        q2 = {"id": "2", "seconds": 30.0, "prompt_tokens": 300, "new_tokens": 150, "truncated": True,
              **g.analyse_answer("I cannot answer this from the abstracts.", SHOWN, OTHER)}
        a = g.aggregate([q1, q2, {"id": "3", "skipped": True}])
        self.assertEqual((a["answers"], a["skipped"], a["empty"]), (2, 1, 0))
        self.assertEqual(a["seconds_median"], 20.0)
        self.assertEqual(a["tokens_per_second"], 5.0)
        self.assertEqual(a["truncated"], 1)
        self.assertEqual(a["within_limit"], 2)
        self.assertEqual((a["sentences"], a["scored"], a["cited"]), (4, 3, 1))
        self.assertEqual(a["cited_share"], 0.3333)
        self.assertEqual(a["ground_cited_mean"], 1.0)
        self.assertEqual(a["ground_any_mean"], 0.6667)
        self.assertEqual(a["ground_other_mean"], 0.0)
        self.assertEqual(a["verbatim_share"], 0.3333)
        self.assertEqual(a["invalid_citation_sentences"], 1)
        self.assertEqual(a["answers_without_valid_citation"], 1)
        self.assertEqual(a["declines"], 1)

    def test_parse_pubmed(self):
        self.assertEqual(g.parse_pubmed(XML), {"111111": {"title": "A trial of X.", "abstract": "Back ground. X worked."},
                                               "222222": {"title": "No abstract", "abstract": ""}})

    def test_evidence(self):
        abstracts = {"1": {"title": "T1", "abstract": "a b c d"}, "2": {"title": "T2", "abstract": ""},
                     "3": {"title": "T3", "abstract": "e f g"}}
        self.assertEqual(g.evidence(["1", "2", "3", "4"], abstracts, k=2, abstract_words=2),
                         [("1", "T1 a b"), ("3", "T3 e f")])

    def test_messages(self):
        msgs = g.messages("Q?", [("1", "T1 a b")], 200)
        self.assertEqual([m["role"] for m in msgs], ["system", "user"])
        self.assertIn("[1] T1 a b", msgs[1]["content"])
        self.assertIn("at most 200 words", msgs[1]["content"])

    def test_load_items(self):
        obj = [{"question_id": "10", "question": "Q10?", "expert_curated_answer": "A [12345678]."},
               {"question_id": "9", "question": "Q9?", "expert_curated_answer": "B."}, {"x": 1}]
        items = g.load_items(obj)
        self.assertEqual([it["id"] for it in items], ["9", "10"])
        self.assertEqual(items[1]["pmids"], ["12345678"])
        self.assertEqual(items[1]["candidates"], ["12345678"])
        self.assertEqual(items[0]["pmids"], [])

    def test_expert_reference(self):
        items = g.load_items([
            {"question_id": "1", "question": "Q?",
             "expert_curated_answer": "Aspirin reduces stroke risk in patients [12345678]. "
                                      "Unrelated claim without citation here."},
            {"question_id": "2", "question": "Q2?", "expert_curated_answer": "B."}])
        abstracts = {"12345678": {"title": "Aspirin trial", "abstract": "Aspirin reduces stroke risk in older patients."}}
        ref = g.expert_reference(items, abstracts)
        self.assertEqual((ref["sentences"], ref["scored"], ref["scored_without_fetched_pmid"]), (3, 1, 1))
        self.assertEqual(ref["ground_mean"], 1.0)
        self.assertEqual(ref["verbatim_share"], 0.0)
        self.assertEqual(ref["words_median"], 6.0)
        self.assertEqual(ref["questions_with_pmid"], 1)

    def _fixture(self, d):
        med = json.dumps([
            {"question_id": "1", "question": "Does aspirin reduce stroke?",
             "expert_curated_answer": "Aspirin reduces stroke risk in patients [12345678]."},
            {"question_id": "2", "question": "Does exercise help?",
             "expert_curated_answer": "Exercise lowers blood pressure in adults [23456789]."}]).encode()
        xml = ("<PubmedArticleSet>%s%s</PubmedArticleSet>" % (
            article("12345678", "Aspirin trial", "Aspirin reduces stroke risk in older patients."),
            article("23456789", "Exercise trial", "Exercise lowers blood pressure in adults."))).encode()

        def get(url, timeout=None):
            return med if "osf.io" in url else xml

        def factory(model_dir, threads, max_new):
            return (lambda msgs: ("Aspirin reduces stroke risk [1].", 120, 10)), {"fake": True}

        return med, get, factory

    def test_run_end_to_end(self):
        with tempfile.TemporaryDirectory() as d:
            med, get, factory = self._fixture(d)
            res = g.run(d, d, os.path.join(d, "out"), writer_factory=factory, get=get,
                        sha=hashlib.sha256(med).hexdigest(), pause=0)
            self.assertIsNone(res["problem"])
            self.assertEqual(res["items"], 2)
            self.assertEqual(res["pmids"], {"requested": 2, "returned": 2, "with_abstract": 2})
            self.assertEqual(res["answers"]["answers"], 2)
            self.assertEqual(res["answers"]["cited_share"], 1.0)
            self.assertEqual(res["expert"]["scored"], 2)
            self.assertEqual(res["expert"]["ground_mean"], 1.0)
            with open(os.path.join(d, "out", "answers.jsonl"), encoding="utf-8") as f:
                self.assertEqual(len(f.read().splitlines()), 2)
            with open(os.path.join(d, "out", "t2gen.json"), encoding="utf-8") as f:
                self.assertNotIn("Aspirin", f.read())

    def test_run_probe_stops(self):
        with tempfile.TemporaryDirectory() as d:
            med, get, factory = self._fixture(d)
            res = g.run(d, d, os.path.join(d, "out"), writer_factory=factory, get=get,
                        sha=hashlib.sha256(med).hexdigest(), pause=0, probe=1, max_hours=-1.0)
            self.assertTrue(res["problem"].startswith("Stop: probe"))
            self.assertEqual(res["answers"]["answers"], 1)

    def test_run_wrong_sha(self):
        with tempfile.TemporaryDirectory() as d:
            med, get, factory = self._fixture(d)
            res = g.run(d, d, os.path.join(d, "out"), writer_factory=factory, get=get, sha="0" * 64, pause=0)
            self.assertTrue(res["problem"].startswith("ValueError: MedAESQA sha256"))
            self.assertEqual(res["answers"]["answers"], 0)

    def test_check_model_dir(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "a"), "wb") as f:
                f.write(b"abc")
            self.assertEqual(g.check_model_dir(d, {"a": 3, "b": 5}), ["b: missing"])
            self.assertEqual(g.check_model_dir(d, {"a": 4}), ["a: 3 bytes, expected 4"])


if __name__ == "__main__":
    unittest.main()
