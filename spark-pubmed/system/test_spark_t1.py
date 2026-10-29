import itertools
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spark_t1  # noqa: E402

# A tiny real FTS5 index in build_index.py's schema (rowid = PMID). Q1 reaches 101, 102 and 104 by
# BM25; the fake cross-encoder scores "zeta" texts higher, so 102 goes first after the rerank.
DOCS = [(101, "aspirin heart attack prevention", "aspirin reduces heart attack risk"),
        (102, "aspirin dosing", "zeta trial of aspirin in heart disease"),
        (103, "statin therapy", "statins lower cholesterol"),
        (104, "heart failure", "heart failure outcomes"),
        (105, "kidney", "renal function zeta")]
QUESTIONS = [{"info_need_id": "Q1", "info_need": "Does aspirin prevent heart attack?"},
             {"metadata": {"team_id": "T", "info_need_id": 7, "info_need": "statin cholesterol"}},
             {"info_need_id": "Q3", "info_need": "the of and", "extra": 1}]


class FakeScorer:
    def __init__(self):
        self.calls = 0

    def score(self, query, docs):
        self.calls += 1
        return [float(d.count("zeta")) for d in docs]


def make_db(path):
    con = spark_t1.t1.build_index.open_db(path, "full")
    with con:
        for pmid, title, abstract in DOCS:
            con.execute("INSERT INTO docs(rowid, title, abstract, mesh) VALUES (?,?,?,?)", (pmid, title, abstract, ""))
            con.execute("INSERT INTO meta VALUES (?,?,?,?,?)", (pmid, 2020, "J", None, "f"))
    con.close()


def write_lines(path, lines):
    with open(path, "w", encoding="utf-8") as f:
        f.write("".join(line + "\n" for line in lines))


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = self.tmp.name
        self.db, self.q, self.out = os.path.join(d, "x.db"), os.path.join(d, "q.jsonl"), os.path.join(d, "out")
        make_db(self.db)
        write_lines(self.q, [json.dumps(o) for o in QUESTIONS])

    def tearDown(self):
        self.tmp.cleanup()

    def sub(self, name):
        return {r["metadata"]["info_need_id"]: r["response"] for r in read_jsonl(os.path.join(self.out, name))}


class Questions(Base):
    def test_forms(self):
        self.assertEqual([n["info_need_id"] for n in spark_t1.read_questions(self.q)], ["Q1", 7, "Q3"])
        p = os.path.join(self.tmp.name, "list.json")
        with open(p, "w", encoding="utf-8-sig") as f:
            json.dump(QUESTIONS[:2], f)
        self.assertEqual(spark_t1.read_questions(p)[1], {"info_need_id": 7, "info_need": "statin cholesterol"})

    def test_bad(self):
        for rows in ([QUESTIONS[0], QUESTIONS[0]], [{"info_need_id": "A"}], [{"info_need_id": True, "info_need": "x"}],
                     [["not", "an", "object"]]):
            write_lines(self.q, [json.dumps(o) for o in rows])
            with self.assertRaises(ValueError):
                spark_t1.read_questions(self.q)


class Pipeline(Base):
    def test_bm25_only(self):
        s = spark_t1.run(self.db, self.q, self.out)
        self.assertEqual((s["complete"], s["answered_this_run"], s["resumed"], s["rerank_depth"]), (True, 3, 0, 0))
        self.assertEqual((s["no_candidates"], s["problems"], s["scorer"], s["immutable"]), (1, [], "none", False))
        top5 = self.sub("submission_top5.jsonl")
        self.assertEqual(sorted(top5["Q1"]), ["101", "102", "104"])
        self.assertEqual((top5[7], top5["Q3"]), (["103"], []))
        self.assertEqual([len(v) for v in self.sub("submission_top1.jsonl").values()], [1, 1, 0])
        rows = read_jsonl(os.path.join(self.out, "ranked.jsonl"))
        self.assertNotIn("logits", rows[0])
        self.assertTrue(all(r["total_ms"] >= r["bm25_ms"] >= 0 for r in rows))
        self.assertEqual(s["submissions"]["submission_top1.jsonl"]["validate"]["empty_responses"], 1)

    def test_rerank(self):
        fake = FakeScorer()
        s = spark_t1.run(self.db, self.q, self.out, fake, "fake", depth=50, submission_ids=["a", "b"], team_id="MV2")
        self.assertEqual((s["rerank_depth"], fake.calls, s["problems"]), (50, 2, []))  # Q3 has no candidates
        self.assertEqual(self.sub("submission_top1.jsonl"), {"Q1": ["102"], 7: ["103"], "Q3": []})
        self.assertEqual(self.sub("submission_top5.jsonl")["Q1"][0], "102")
        meta = read_jsonl(os.path.join(self.out, "submission_top1.jsonl"))[0]["metadata"]
        self.assertEqual((meta["team_id"], meta["submission_id"]), ("MV2", "b"))
        row = read_jsonl(os.path.join(self.out, "ranked.jsonl"))[0]
        self.assertEqual((row["scorer"], row["rerank_depth"], row["logits"][0]), ("fake", 50, 1.0))

    def test_resume(self):
        spark_t1.run(self.db, self.q, self.out)
        ranked = os.path.join(self.out, "ranked.jsonl")
        q1 = dict(read_jsonl(ranked)[0], kept=True)
        stale = dict(read_jsonl(ranked)[1], info_need="old text")
        write_lines(ranked, [json.dumps(q1), json.dumps(stale), '{"info_need_id": "Q'])
        s = spark_t1.run(self.db, self.q, self.out)
        self.assertEqual((s["resumed"], s["answered_this_run"], s["complete"]), (1, 2, True))
        rows = read_jsonl(ranked)
        self.assertEqual(([r["info_need_id"] for r in rows], rows[0].get("kept")), (["Q1", 7, "Q3"], True))
        s = spark_t1.run(self.db, self.q, self.out, FakeScorer(), "fake")  # other settings: nothing reused
        self.assertEqual((s["resumed"], s["answered_this_run"]), (0, 3))

    def test_time_budget(self):
        s = spark_t1.run(self.db, self.q, self.out, max_minutes=1, clock=itertools.count(0, 30).__next__)
        self.assertEqual((s["complete"], s["stopped"], s["answered_this_run"], s["submissions"]),
                         (False, "time budget", 1, {}))
        self.assertEqual(s["ms"]["total"]["median"], 60000)
        self.assertFalse(os.path.exists(os.path.join(self.out, "submission_top5.jsonl")))
        s = spark_t1.run(self.db, self.q, self.out)
        self.assertEqual((s["resumed"], s["answered_this_run"], s["complete"]), (1, 2, True))

    def test_errors(self):
        with self.assertRaises(FileNotFoundError):
            spark_t1.run(os.path.join(self.tmp.name, "none.db"), self.q, self.out)
        with self.assertRaises(ValueError):
            spark_t1.run(self.db, self.q, self.out, policies=["top:9"])
        with self.assertRaises(ValueError):
            spark_t1.run(self.db, self.q, self.out, submission_ids=["only-one"])

    def test_main(self):
        self.assertEqual(spark_t1.main(["--db", self.db, "--questions", self.q, "--out-dir", self.out,
                                        "--scorer", "none", "--policies", "top:3"]), 0)
        self.assertEqual(sorted(os.listdir(self.out)), ["ranked.jsonl", "run.json", "submission_top3.jsonl"])
        with open(os.path.join(self.out, "run.json"), encoding="utf-8") as f:
            self.assertEqual({k: v for k, v in json.load(f).items() if k in ("version", "depth", "immutable")},
                             {"version": "0.2.0", "depth": 150, "immutable": False})
        with self.assertRaises(SystemExit):
            spark_t1.main(["--db", self.db, "--questions", self.q, "--out-dir", self.out])  # medcpt needs --model-dir


class Immutable(Base):
    def test_same_files_as_plain(self):
        plain = spark_t1.run(self.db, self.q, self.out, FakeScorer(), "fake")
        out2 = os.path.join(self.tmp.name, "out2")
        imm = spark_t1.run(self.db, self.q, out2, FakeScorer(), "fake", immutable=True)
        self.assertEqual((imm["immutable"], imm["complete"], imm["problems"]), (True, True, []))
        self.assertEqual(plain["immutable"], False)
        for name in ("submission_top5.jsonl", "submission_top1.jsonl"):
            self.assertEqual(read_bytes(os.path.join(self.out, name)), read_bytes(os.path.join(out2, name)))
        self.assertEqual(spark_t1.ro_db.side_files(self.db), {"wal": None, "shm": None})

    def test_refuses_unchecked_wal(self):
        with open(self.db + "-wal", "wb") as f:
            f.write(b"\0" * 32)
        with self.assertRaises(ValueError):
            spark_t1.run(self.db, self.q, self.out, immutable=True)

    def test_main_flag(self):
        self.assertEqual(spark_t1.main(["--db", self.db, "--questions", self.q, "--out-dir", self.out,
                                        "--scorer", "none", "--immutable"]), 0)
        with open(os.path.join(self.out, "run.json"), encoding="utf-8") as f:
            self.assertEqual(json.load(f)["immutable"], True)
        self.assertEqual(sorted(self.sub("submission_top5.jsonl")["Q1"]), ["101", "102", "104"])


if __name__ == "__main__":
    unittest.main()
