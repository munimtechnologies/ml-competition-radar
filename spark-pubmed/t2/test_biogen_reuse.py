"""Tests for biogen_reuse.py (MV2 of Munim, Inc.; made with AI agents working in his name). Apache-2.0."""
import unittest

import biogen_reuse as br


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


class TestBiogenReuse(unittest.TestCase):
    def test_content_strips_citations_and_stop_words(self):
        self.assertEqual(br.content("The drug reduced blood pressure [PMID: 12345678]."),
                         frozenset({"drug", "reduced", "blood", "pressure"}))
        self.assertEqual(br.content(None), frozenset())

    def test_dice(self):
        self.assertEqual(br.dice(frozenset("ab"), frozenset("bc")), 0.5)
        self.assertEqual(br.dice(frozenset(), frozenset("bc")), 0.0)

    def test_kendall(self):
        self.assertEqual(br.kendall([1, 2, 3], [1, 2, 3]), 1.0)
        self.assertEqual(br.kendall([1, 2, 3], [3, 2, 1]), -1.0)
        self.assertAlmostEqual(br.kendall([1, 1, 2], [1, 2, 3]), 2 / 6 ** 0.5)

    def test_auroc_with_ties(self):
        self.assertAlmostEqual(br.auroc([0.9, 0.5], [0.5, 0.1]), 0.875)
        self.assertIsNone(br.auroc([], [0.1]))

    def test_load_runs_and_questions(self):
        data = br.load_runs(ASSESS)
        self.assertEqual(sorted(data), ["1"])
        self.assertEqual(data["1"]["A"][0], ("required", frozenset({"aspirin", "lowers", "fever", "adults"})))
        self.assertEqual(data["1"]["A"][2], (None, frozenset()))
        self.assertEqual(len(data["1"]["B"]), 1)
        self.assertEqual(br.load_questions(TOPICS), {"1": frozenset({"aspirin", "lower", "fever"})})

    def test_score_topic_team_out_vs_run_out(self):
        data = br.load_runs(ASSESS)
        topic = dict(data["1"])
        topic["A2"] = [data["1"]["A"][0]]  # a team mate repeating A's Required sentence
        by_sent, by_item, n = br.score_topic(topic, "A", {"A", "A2"})
        self.assertEqual((by_sent, by_item, n), ([0.75, 0.0], [0.75], 1))
        by_sent, _, n = br.score_topic(topic, "A", {"A"})
        self.assertEqual((by_sent, n), ([1.0, 0.0], 2))

    def test_clusters(self):
        items = [frozenset("abcd"), frozenset("abce"), frozenset("xyz")]
        self.assertEqual(br.clusters(items, 0.5), 2)

    def test_analyse_small(self):
        res, per = br.analyse(br.load_runs(ASSESS), br.load_questions(TOPICS), OFFICIAL)
        self.assertEqual((res["topics"], res["runs"], res["runs_matched_official"]), (1, 2, 2))
        self.assertEqual((res["sentences"], res["labelled"], res["scored_sentences"]), (4, 3, 3))
        self.assertEqual(res["sentence_auroc"]["team_out"], 1.0)
        self.assertEqual(per["A"]["recall_team"]["0.5"], 100.0)
        self.assertEqual(per["A"]["precision_team"]["0.5"], 33.3333)  # the ".." sentence counts, unmatched
        self.assertEqual(per["B"]["precision_team"]["0.5"], 100.0)
        self.assertEqual(per["A"]["repro_precision_all"], 33.3333)
        self.assertEqual(per["A"]["repro_precision_answered"], 33.3333)
        self.assertEqual(per["A"]["repro_precision_labelled"], 50.0)
        self.assertEqual(res["repro_precision"]["within_1_labelled"], 2)
        self.assertEqual(res["greedy_clusters_per_topic"]["median"], 1)


if __name__ == "__main__":
    unittest.main()
