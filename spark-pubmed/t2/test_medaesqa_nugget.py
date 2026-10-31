"""Tests for medaesqa_nugget.py (MV2 of Munim, Inc.; made with AI agents working in his name). Apache-2.0."""
import unittest

import biogen_reuse as br
import medaesqa_nugget as mn


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
ITEMS = [
    {"question_id": "7", "question": "Does aspirin lower fever?",
     "expert_curated_answer": " Aspirin lowers fever in adults [123, 456]. It also eases pain.",
     "expert_curated_nuggets": ["Aspirin lowers fever", "eases pain"],
     "machine_generated_answers": {
         "M1": {"answer": "x", "is_answer_accurate": "yes",
                "answer_sentences": [sent("Aspirin lowers fever in adults [PMID: 12345678].", "required")]}}},
]
# the shape medaesqa_v1.json has (bioace-zip-v1): `nuggets`, a list of strings
ITEMS2 = [
    {"question_id": "8", "question": "Does aspirin lower fever?", "expert_curated_nuggets": None,
     "nuggets": ["Aspirin lowers fever", "aspirin"]},
    {"question_id": "9", "question": "Does aspirin lower fever?"},
]
OFFICIAL = {"A": {"team": "X", "precision": 50.0, "completeness_r": 30.0, "completeness_rb": 31.0},
            "B": {"team": "Y", "precision": 100.0, "completeness_r": 20.0, "completeness_rb": 21.0}}


class TestMedaesqaNugget(unittest.TestCase):
    def test_cover(self):
        self.assertEqual(mn.cover(frozenset("ab"), frozenset("abc")), 1.0)
        self.assertEqual(mn.cover(frozenset("abcd"), frozenset("ab")), 0.5)
        self.assertEqual(mn.cover(frozenset(), frozenset("a")), 0.0)

    def test_nugget_texts_shapes(self):
        self.assertEqual(mn.nugget_texts(["a b", " ", "c d"]), ["a b", "c d"])
        self.assertEqual(mn.nugget_texts("x y\n\nz w"), ["x y", "z w"])
        self.assertEqual(mn.nugget_texts([{"text": "a b", "pmids": ["1"]}]), ["a b"])
        self.assertEqual(mn.nugget_texts({"n1": "a b", "n2": "c d"}), ["a b", "c d"])
        self.assertEqual(mn.nugget_texts(None), [])

    def test_shape(self):
        self.assertEqual(mn.shape(["a", "b"]), "list[str]")
        self.assertEqual(mn.shape([{"nugget": "x", "pmids": [1]}]), "list[dict{nugget,pmids}]")
        self.assertEqual(mn.shape({"a long key with spaces": 1}), "dict(1 keys)")
        self.assertEqual(mn.shape(None), "NoneType")

    def test_sentences(self):
        self.assertEqual(mn.sentences("First one. Second one? Third"), ["First one.", "Second one?", "Third"])
        self.assertEqual(mn.sentences(None), [])

    def test_partial_tau(self):
        self.assertEqual(mn.partial_tau(0.5, 0.0, 0.0), 0.5)
        self.assertAlmostEqual(mn.partial_tau(0.6, 0.5, 0.5), 0.35 / 0.75)
        self.assertIsNone(mn.partial_tau(0.8, 0.8, 1.0))
        self.assertIsNone(mn.partial_tau(None, 0.0, 0.0))

    def test_run_scores(self):
        nuggets = [frozenset("ab"), frozenset("cd")]
        rows = [("required", frozenset("abx")), ("unnecessary", frozenset("cyz")), (None, frozenset("q"))]
        rec, prec, soft, by_sent = mn.run_scores(rows, nuggets)
        self.assertEqual((rec[0.6], rec[0.5]), (0.5, 1.0))
        self.assertAlmostEqual(prec[0.6], 1 / 3)
        self.assertEqual((soft, by_sent), (0.75, [1.0, 0.5]))
        self.assertEqual(mn.run_scores([], nuggets)[0][0.6], 0.0)
        self.assertIsNone(mn.run_scores(rows, [])[0][0.6])
        self.assertEqual(mn.run_scores(rows, [])[1][0.6], 0.0)

    def test_load_expert_and_match(self):
        expert, shapes, fields = mn.load_expert(ITEMS)
        self.assertEqual((shapes, fields), ({"list[str]": 1}, {"expert_curated_nuggets": 1}))
        e = expert["7"]
        self.assertEqual(e["nuggets"], [frozenset({"aspirin", "lowers", "fever"}), frozenset({"eases", "pain"})])
        self.assertEqual(e["expert"], [frozenset({"aspirin", "lowers", "fever", "adults"})])  # 2nd: 2 words
        data, tq = br.load_runs(ASSESS), mn.topic_questions(TOPICS)
        self.assertEqual(mn.match_questions(expert, data, tq),
                         ({"7": "1"}, {"by_id": 0, "by_text": 1, "unmatched": 0, "id_text_differs": 0}))
        self.assertEqual(mn.match_questions({"1": {"question": frozenset({"cats"})}}, data, tq),
                         ({}, {"by_id": 0, "by_text": 0, "unmatched": 1, "id_text_differs": 1}))

    def test_nuggets_field(self):
        expert, shapes, fields = mn.load_expert(ITEMS2)
        self.assertEqual(fields, {"nuggets": 1, "None": 1})
        self.assertEqual(shapes, {"list[str]": 1, "NoneType": 1})
        self.assertEqual(expert["8"]["nuggets"], [frozenset({"aspirin", "lowers", "fever"})])  # 1 word: dropped
        self.assertEqual(expert["8"]["nugget_texts"], 2)
        self.assertEqual((expert["9"]["nuggets"], expert["9"]["expert"]), ([], []))
        self.assertEqual(mn.nugget_field({"Nuggets": ["a"]}), ("nuggets", ["a"]))
        self.assertEqual(mn.nugget_field({}), (None, None))

    def test_map_runs_and_labels(self):
        med, data = br.load_runs(ITEMS), br.load_runs(ASSESS)
        runmap = mn.map_runs(med, data, {"7": "1"})
        self.assertEqual(runmap, {"M1": {"run": "A", "share": 1.0, "runner_up_share": 0.0}})
        self.assertEqual(mn.label_agreement(med, data, {"7": "1"}, runmap),
                         {"same": 1, "differ": 0, "medaesqa_null_biogen_labelled": 0,
                          "biogen_null_medaesqa_labelled": 0})

    def test_analyse_small(self):
        expert = mn.load_expert(ITEMS)[0]
        res, per = mn.analyse(expert, {"7": "1"}, br.load_runs(ASSESS), OFFICIAL)
        self.assertEqual((res["questions"], res["runs"], res["nuggets"]), (1, 2, 2))
        self.assertEqual(res["control_expert_recall"], 50.0)
        self.assertEqual(per["A"]["recall"]["0.6"], 50.0)
        self.assertEqual(per["A"]["precision"]["0.6"], 33.3333)  # the ".." sentence counts, unmatched
        self.assertEqual(per["B"]["precision"]["0.6"], 100.0)
        self.assertEqual(per["A"]["sentences_per_question"], 3.0)
        self.assertEqual(res["sentence_auroc"]["nugget"], 1.0)
        self.assertEqual(res["run_tau"]["length_vs_completeness_r"], 1.0)
        self.assertIsNone(res["run_tau"]["0.6"]["recall_vs_completeness_r"])  # equal recall: no order
        self.assertIsNone(res["run_tau"]["partial_recall_vs_completeness_r_given_length"])


if __name__ == "__main__":
    unittest.main()
