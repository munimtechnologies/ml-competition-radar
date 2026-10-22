"""Tests for the frozen R dev-set questions and their rule checker. MV2 of Munim, Inc. Apache-2.0."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_titles  # noqa: E402
import rq_rules  # noqa: E402


class RuleTest(unittest.TestCase):
    def test_shared_runs(self):
        title = "Kinetics of the hemerythrin-oxygen interaction."
        self.assertEqual(rq_rules.shared_runs("the study of the hemerythrin oxygen rates", title),
                         ["of the hemerythrin", "the hemerythrin oxygen"])
        self.assertEqual(rq_rules.shared_runs("the study of hemerythrin and oxygen", title), [])
        self.assertEqual(rq_rules.shared_runs("KINETICS OF THE worm", title), ["kinetics of the"])

    def test_problems_on_fake_set(self):
        titles = [{"pmid": 1, "title": "Alpha beta gamma delta."}, {"pmid": 2, "title": "One two three."}]
        good = [{"pmid": 1, "question": "the study of alpha and gamma"},
                {"pmid": 2, "question": "the study of one, then two"}]
        self.assertEqual(rq_rules.problems(good, titles), [])
        bad = [{"pmid": 1, "question": "the study of alpha beta gamma"},
               {"pmid": 1, "question": "study on delta"}]
        found = rq_rules.problems(bad, titles)
        self.assertEqual(len(found), 4)
        self.assertTrue(any("shares title words ['alpha beta gamma']" in f for f in found))
        self.assertTrue(any("duplicate pmid" in f for f in found))
        self.assertTrue(any("does not start" in f for f in found))
        self.assertTrue(any("no question for [2]" in f for f in found))

    def test_compare_with_official_titles(self):
        titles = [{"pmid": 1, "title": "Alpha beta gamma."}, {"pmid": 2, "title": "One two three."},
                  {"pmid": 3, "title": "Red blue."}]
        questions = [{"pmid": 1, "question": "the study of alpha"}, {"pmid": 2, "question": "the two three four"},
                     {"pmid": 3, "question": "the study"}]
        s = check_titles.compare(questions, titles, {1: "Alpha-beta gamma", 2: "One two three four."})
        self.assertEqual((s["records"], s["found"], s["same_words"]), (3, 2, 1))
        self.assertEqual(s["missing"], [3])
        self.assertEqual([r["pmid"] for r in s["differs"]], [2])
        self.assertEqual(s["official_rule_breaks"][0]["official_runs"], ["two three four"])


class FrozenSetTest(unittest.TestCase):
    def setUp(self):
        self.questions = rq_rules.load("r_questions.jsonl")
        self.titles = rq_rules.load("r_titles.jsonl")

    def test_ninety_records_in_pool_order(self):
        self.assertEqual(len(self.questions), 90)
        self.assertEqual(len(self.titles), 90)
        self.assertEqual([q["pmid"] for q in self.questions], [t["pmid"] for t in self.titles])
        self.assertEqual(len(set(q["pmid"] for q in self.questions)), 90)

    def test_titles_file_has_no_abstracts(self):
        for t in self.titles:
            self.assertEqual(set(t), {"pmid", "title"})

    def test_every_question_keeps_the_rules(self):
        self.assertEqual(rq_rules.problems(self.questions, self.titles), [])


if __name__ == "__main__":
    unittest.main()
