import json
import math
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import llm_judge  # noqa: E402
import nli_check  # noqa: E402

SENT = "Drug X lowers blood pressure."
NEG = "Drug X did not lower blood pressure in adults."
POS = "Drug X lowered blood pressure significantly."


def fake_clock(step=10):
    t = [-step]

    def clock():
        t[0] += step
        return t[0]
    return clock


class Judge(unittest.TestCase):
    def test_letter_probs_and_order(self):
        self.assertEqual(llm_judge.LETTERS, ("B", "A", "C"))
        self.assertEqual(nli_check.NLI, ("contradiction", "entailment", "neutral"))
        for p in llm_judge.letter_probs([0.0, 0.0, 0.0]):
            self.assertAlmostEqual(p, 1 / 3)
        for got, want in zip(llm_judge.letter_probs([math.log(2), 0.0, 0.0]), (0.5, 0.25, 0.25)):
            self.assertAlmostEqual(got, want)

    def test_messages_and_clip(self):
        msgs, cut = llm_judge.messages("one two three four", "S.", max_words=2)
        self.assertTrue(cut)
        self.assertEqual([m["role"] for m in msgs], ["system", "user"])
        self.assertTrue(msgs[1]["content"].startswith("Passage from a cited paper:\none two\n\nStatement:\nS.\n\n"))
        self.assertTrue(msgs[1]["content"].endswith("C = neither."))
        self.assertFalse(llm_judge.messages("a b", "S.", 5)[1])

    def test_gated_scorer(self):
        seen = []

        def judge(msgs):
            seen.append(msgs[1]["content"])
            return (0.7, 0.2, 0.1), 0.9
        out, rep = llm_judge.gated_scorer([(NEG, SENT), (POS, SENT)], judge, log=lambda *a: None)
        self.assertEqual(out, [(0.7, 0.2, 0.1), llm_judge.OUTSIDE])
        self.assertEqual(len(seen), 1)
        self.assertIn(NEG, seen[0])
        self.assertEqual((rep["pairs"], rep["judged"], rep["clipped"]), (2, 1, 0))
        self.assertEqual((rep["letter_mass_mean"], rep["letter_mass_below_half"]), (0.9, 0))
        self.assertIsNone(rep["probe_s_per_pair"])

    def test_probe(self):
        pairs = [("no effect %d" % i, SENT) for i in range(3)]

        def judge(msgs):
            return (0.1, 0.1, 0.8), 0.4
        with self.assertRaises(SystemExit):
            llm_judge.gated_scorer(pairs, judge, probe=2, max_hours=0.001, clock=fake_clock(),
                                   log=lambda *a: None)
        out, rep = llm_judge.gated_scorer(pairs, judge, probe=2, max_hours=1.0, clock=fake_clock(),
                                          log=lambda *a: None)
        self.assertEqual(out, [(0.1, 0.1, 0.8)] * 3)
        self.assertEqual((rep["seconds"], rep["letter_mass_below_half"]), (20.0, 3))
        self.assertEqual(rep["probe_s_per_pair"], 5.0)

    def test_check_model(self):
        rep = {"files": {"a": {"bytes": 3}, "b": {"bytes": 5}}}
        self.assertEqual(llm_judge.check_model(rep, {"a": 3, "b": 4, "c": 1}),
                         ["b: 5 bytes, expected 4", "c: missing"])
        full = {"files": {n: {"bytes": s} for n, s in llm_judge.MODEL_FILES.items()}}
        self.assertEqual(llm_judge.check_model(full), [])
        self.assertEqual(llm_judge.MODEL_FILES["model.safetensors"], 3087467144)
        self.assertEqual(len(llm_judge.MODEL_REV), 40)

    def test_models_and_cpu_limit(self):
        self.assertEqual(sorted(llm_judge.MODELS), ["qwen2.5-0.5b", "qwen2.5-1.5b"])
        self.assertEqual(llm_judge.MODELS["qwen2.5-1.5b"][0], llm_judge.MODEL_ID)
        model_id, rev, files = llm_judge.MODELS["qwen2.5-0.5b"]
        self.assertEqual((model_id, rev), ("Qwen/Qwen2.5-0.5B-Instruct", "7ae557604adf67be50417f59c2c2f167def9a775"))
        self.assertEqual((files["model.safetensors"], files["config.json"], len(files)), (988097824, 659, 8))
        self.assertEqual(llm_judge.DTYPES, ("float32", "bfloat16"))
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "cpu.max")
            with open(path, "w", encoding="ascii") as f:
                f.write("200000 100000\n")
            self.assertEqual(llm_judge.cpu_limit(path), 2.0)
            with open(path, "w", encoding="ascii") as f:
                f.write("max 100000\n")
            self.assertIsNone(llm_judge.cpu_limit(path))
            self.assertIsNone(llm_judge.cpu_limit(os.path.join(d, "missing")))

    def test_run_end_to_end(self):
        records = [{"question_id": "1", "machine_generated_answers": {"r1": {"answer_sentences": [
            {"answer_sentence": SENT, "citation_assessment": [
                {"cited_pmid": "123", "evidence_relation": "contradicting", "evidence_support": NEG},
                {"cited_pmid": "456", "evidence_relation": "supporting", "evidence_support": POS}]}]}}}]
        asked = []

        def factory(model_dir, threads, dtype):
            asked.append((threads, dtype))
            return (lambda msgs: ((0.8, 0.1, 0.1), 0.95)), {"dtype": "fake"}
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "assessments.json"), "w", encoding="utf-8") as f:
                json.dump(records, f)
            res = llm_judge.run(d, "unused", judge_factory=factory, sha=None)
            small = llm_judge.run(d, "unused", judge_factory=factory, sha=None, model="qwen2.5-0.5b")
        self.assertEqual(asked, [(2, "float32"), (2, "float32")])
        self.assertEqual(res["problems"], [])
        self.assertEqual(res["model"], llm_judge.MODEL_ID)
        self.assertEqual(small["model"], "Qwen/Qwen2.5-0.5B-Instruct")
        self.assertEqual(res["llm_judge_version"], "0.2.0")
        self.assertEqual(res["counts"]["scored"], 2)
        self.assertEqual((res["scoring"]["judged"], res["scoring"]["dtype"]), (1, "fake"))
        arg = res["entry"]["contradicts_vs_rest"]["argmax"]
        self.assertEqual((arg["tp"], arg["fp"], arg["fn"]), (1, 0, 0))
        self.assertEqual(res["gate"]["judgments"], 1)
        self.assertEqual(res["gate"]["labels"]["contradicts"], 1)


if __name__ == "__main__":
    unittest.main()
