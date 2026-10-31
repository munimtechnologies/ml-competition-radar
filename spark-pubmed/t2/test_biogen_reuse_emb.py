"""Tests for biogen_reuse_emb.py (MV2 of Munim, Inc.; made with AI agents working in his name). Apache-2.0.

No model is loaded: embeddings are given as fixed unit vectors."""
import os
import tempfile
import unittest

import biogen_reuse as br
import biogen_reuse_emb as be


def sent(text, lab):
    return {"answer_sentence": text, "answer_sentence_relevance": lab, "citation_assessment": None}


ASSESS = [
    {"question_id": "1", "machine_generated_answers": {
        "A": {"answer": "x", "answer_sentences": [sent("Aspirin lowers fever in adults [PMID: 12345678].", "required"),
                                                 sent("The weather is sunny this morning.", "unnecessary"),
                                                 sent("..", None)]},
        "B": {"answer": "y", "answer_sentences": [sent("Aspirin lowers fever in children.", "required")]}}},
]
TOPICS = [{"id": 1, "topic": "fever", "question": "Does aspirin lower fever?", "narrative": ""}]
OFFICIAL = {"A": {"team": "X", "precision": 50.0, "completeness_r": 30.0},
            "B": {"team": "Y", "precision": 100.0, "completeness_r": 20.0}}
KA = frozenset({"aspirin", "lowers", "fever", "adults"})
KB = frozenset({"aspirin", "lowers", "fever", "children"})
KW = frozenset({"weather", "sunny", "morning"})
VECS = [[1.0, 0.0], [0.6, 0.8], [0.0, 1.0]]  # KA, KB, KW: cos(KA, KB) 0.6, cos(KB, KW) 0.8, cos(KA, KW) 0


def sims_for(data):
    out = {"lex": {}, "emb": {}}
    for t in data:
        keys, _ = be.keys_of(data[t])
        index = {w: i for i, w in enumerate(keys)}
        out["lex"][t] = (index, be.lex_matrix(keys))
        out["emb"][t] = (index, be.cos_matrix(VECS))
    return out


class TestBiogenReuseEmb(unittest.TestCase):
    def test_load_texts_words_match_load_runs(self):
        data, ref = be.load_texts(ASSESS), br.load_runs(ASSESS)
        self.assertEqual(data["1"]["A"][0], ("required", KA, "Aspirin lowers fever in adults ."))
        self.assertEqual(data["1"]["A"][2], (None, frozenset(), ".."))
        for run in ("A", "B"):
            self.assertEqual([(lab, w) for lab, w, _ in data["1"][run]], ref["1"][run])

    def test_keys_of_order_and_text(self):
        keys, texts = be.keys_of(be.load_texts(ASSESS)["1"])
        self.assertEqual(keys, [KA, KB, KW])
        self.assertEqual(texts[2], "The weather is sunny this morning.")

    def test_score_matches_biogen_reuse(self):
        topic = dict(be.load_texts(ASSESS)["1"])
        topic["A2"] = [topic["A"][0]]  # a team mate repeating A's Required sentence
        ref = dict(br.load_runs(ASSESS)["1"])
        ref["A2"] = [ref["A"][0]]
        keys, _ = be.keys_of(topic)
        index, sim = {w: i for i, w in enumerate(keys)}, be.lex_matrix(keys)
        for exclude in ({"A", "A2"}, {"A"}):
            self.assertEqual(be.score(topic, index, sim, "A", exclude), br.score_topic(ref, "A", exclude))

    def test_cos_matrix(self):
        m = be.cos_matrix(VECS)
        self.assertAlmostEqual(m[0][1], 0.6)
        self.assertAlmostEqual(m[1][2], 0.8)
        self.assertAlmostEqual(m[0][2], 0.0)

    def test_analyse_small(self):
        data = be.load_texts(ASSESS)
        res, per = be.analyse(data, sims_for(data), OFFICIAL, n_boot=20)
        ref, _ = br.analyse(br.load_runs(ASSESS), br.load_questions(TOPICS), OFFICIAL)
        self.assertEqual((res["topics"], res["runs"], res["sentences"], res["distinct_keys"]), (1, 2, 4, 3))
        self.assertEqual(res["sentence_auroc"]["lex"]["team_out"], ref["sentence_auroc"]["team_out"])
        self.assertEqual(res["sentence_auroc"]["emb"]["team_out"], 0.0)  # the unnecessary sentence sits nearer B
        self.assertEqual(per["A"]["emb"]["recall_team"]["0.7"], 100.0)
        self.assertEqual(per["A"]["emb"]["precision_team"]["0.7"], 33.3333)
        self.assertEqual(per["B"]["emb"]["recall_team"]["0.7"], 0.0)
        self.assertEqual(per["A"]["emb"]["soft"], {"recall_team": 80.0, "precision_team": 46.6667})
        self.assertEqual(per["A"]["lex"]["precision_team"]["0.5"], 33.3333)
        self.assertEqual(res["run_tau"]["emb"]["0.7"]["recall_team"], 1.0)
        self.assertEqual(res["run_tau"]["emb"]["0.7"]["precision_team"], -1.0)
        self.assertEqual(res["run_tau"]["baseline_sentences_vs_completeness_r"],
                         ref["run_tau"]["baseline_sentences_vs_completeness_r"])
        self.assertEqual(res["sentence_auroc_n"], ref["sentence_auroc_n"])

    def test_boot_diff(self):
        b = be.boot_diff([("1", "required", 0.75, 0.6), ("1", "unnecessary", 0.0, 0.8),
                          ("2", "required", 0.5, 0.9), ("2", "borderline", 0.1, 0.2)], ["1", "2"], n=50)
        self.assertEqual(b["n"], 50)
        self.assertLessEqual(b["lo_2_5"], b["median"])
        self.assertLessEqual(b["median"], b["hi_97_5"])
        same = be.boot_diff([("1", "required", 0.7, 0.7), ("1", "unnecessary", 0.1, 0.1)], ["1"], n=10)
        self.assertEqual((same["lo_2_5"], same["hi_97_5"], same["share_above_0"]), (0.0, 0.0, 0.0))

    def test_fetch_model_checks_the_pin(self):
        with tempfile.TemporaryDirectory() as d:
            for name in be.MODEL_FILES:
                with open(os.path.join(d, name), "wb") as f:
                    f.write(b"x")
            rep = be.fetch_model(d)  # every file present: nothing is downloaded
        self.assertIn("pinned", rep["problem"])
        self.assertEqual(rep["files"]["config.json"]["bytes"], 1)


if __name__ == "__main__":
    unittest.main()
