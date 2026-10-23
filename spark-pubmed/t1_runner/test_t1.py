"""Fake-data tests for t1.py (no network). MV2 of Munim, Inc. Apache-2.0."""
import gzip
import json
import os
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_index  # noqa: E402
import t1  # noqa: E402

DOCS = [(1, "Zebrafish heart regeneration", "Cardiomyocytes proliferate after cryoinjury."),
        (2, "Mouse liver regeneration", "Hepatocytes divide after partial hepatectomy."),
        (3, "Zebrafish fin growth", "Bone rays regrow quickly."),
        (4, "Kidney stone crystals", "Calcium oxalate deposits.")] + \
       [(p, "Alpha beta w%d" % p, "Gamma delta w%d epsilon." % p) for p in range(5, 11)]


def art(pmid, title, abstract):
    return ("<PubmedArticle><MedlineCitation><PMID Version=\"1\">%d</PMID><Article><Journal>"
            "<JournalIssue><PubDate><Year>2000</Year></PubDate></JournalIssue><ISOAbbreviation>J Fake"
            "</ISOAbbreviation></Journal><ArticleTitle>%s</ArticleTitle><Abstract><AbstractText>%s"
            "</AbstractText></Abstract></Article><MeshHeadingList><MeshHeading><DescriptorName>Animals"
            "</DescriptorName></MeshHeading></MeshHeadingList></MedlineCitation><PubmedData><ArticleIdList>"
            "<ArticleId IdType=\"pubmed\">%d</ArticleId></ArticleIdList></PubmedData></PubmedArticle>"
            % (pmid, title, abstract, pmid))


def index(d):
    raw = os.path.join(d, "raw")
    os.makedirs(raw)
    name = "pubmed27n0001.xml.gz"
    with open(os.path.join(raw, name), "wb") as f:
        f.write(gzip.compress(("<PubmedArticleSet>%s</PubmedArticleSet>"
                               % "".join(art(*doc) for doc in DOCS)).encode("utf-8")))
    with open(os.path.join(raw, name + ".md5ok"), "w", encoding="ascii") as f:
        f.write("x")
    db = os.path.join(d, "idx", "spark.db")
    s = build_index.run(raw, db, os.path.join(d, "build"))
    assert s["docs"] == 10, s
    return db


def dump(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write((r if isinstance(r, str) else json.dumps(r)) + "\n")


def inputs(d):
    rq, rt, lm = (os.path.join(d, n) for n in ("rq.jsonl", "rt.jsonl", "lm.json"))
    dump(rq, [{"pmid": 1, "question": "the study of zebrafish heart regeneration cardiomyocytes"},
              {"pmid": 4, "question": "the work on calcium oxalate kidney deposits"}])
    dump(rt, [{"pmid": 1, "title": "Zebrafish heart regeneration"},
              {"pmid": 4, "title": "Kidney stone crystals"}])
    base = {"status": "verified", "in_window": True, "contested": False, "control": None,
            "excluded_types": []}
    items = [dict(base, id="L01", question="the zebrafish fin bone rays", pmid="3"),
             dict(base, id="L02", question="q2", pmid="2", contested=True),
             dict(base, id="L03", question="q3", pmid="5", in_window=False),
             dict(base, id="L04", question="q4", pmid="6", excluded_types=["Editorial"]),
             dict(base, id="C01", question="q5", pmid="7", control="pre-1959", in_window=False),
             {"id": "L37", "question": "the liver hepatectomy hepatocytes", "status": "not_found"}]
    with open(lm, "w", encoding="utf-8") as f:
        json.dump(items, f)
    return rq, rt, lm


SYN = [{"info_need_id": "A", "info_need": "a",
        "candidates": [[11, 10.0], [12, 9.0], [13, 5.0], [14, 4.9], [15, 1.0], [16, 0.5]]},
       {"info_need_id": "B", "info_need": "b", "candidates": [[21, 3.0], [22, 2.9]]},
       {"info_need_id": "C", "info_need": "c", "candidates": []},
       {"info_need_id": "D", "info_need": "d", "candidates": [[41, 1.0]]}]
SYN_GOLD = [{"info_need_id": "A", "gold": ["13"]}, {"info_need_id": "B", "gold": ["21"]},
            {"info_need_id": "C", "gold": ["31"]}]


class T1Test(unittest.TestCase):
    def test_candidates(self):
        with tempfile.TemporaryDirectory() as d:
            con = sqlite3.connect(index(d))
            c = t1.candidates(con, "zebrafish heart regeneration cardiomyocytes")
            self.assertEqual(c[0][0], 1)
            self.assertEqual({p for p, _ in c}, {1, 2, 3})
            self.assertEqual([s for _, s in c], sorted((s for _, s in c), reverse=True))
            self.assertTrue(all(s > 0 for _, s in c))
            one = t1.candidates(con, "zebrafish", depth=1)  # docs 1 and 3 may tie: either is fine
            self.assertEqual((len(one), one[0][0] in (1, 3)), (1, True))
            self.assertEqual(t1.candidates(con, "the of and"), [])
            con.close()

    def test_policies(self):
        a = SYN[0]["candidates"]
        self.assertEqual(t1.cut(a, "top:3"), [11, 12, 13])
        self.assertEqual(t1.cut(a, "ratio:0.8"), [11, 12])
        self.assertEqual(t1.cut(a, "ratio:0"), [11, 12, 13, 14, 15])
        self.assertEqual(t1.cut([], "top:2"), [])
        for bad in ("top:0", "top:6", "top:2.5", "ratio:1.5", "ratio:x", "foo"):
            with self.assertRaises(ValueError):
                t1.parse_policy(bad)

    def test_score(self):
        s = t1.score(SYN, SYN_GOLD)
        self.assertEqual((s["needs"], s["no_gold"]), (3, ["D"]))
        self.assertEqual(s["recall_at"], {"1": 0.3333, "5": 0.6667})
        self.assertEqual(s["policies"]["top:5"], {"mrr": 0.4444, "hit": 0.6667, "mean_returned": 2.333,
                                                  "mean_wrong": 1.667})
        self.assertEqual(s["policies"]["ratio:0.8"], {"mrr": 0.3333, "hit": 0.3333, "mean_returned": 1.333,
                                                      "mean_wrong": 1.0})
        self.assertEqual(s["policies"]["top:1"], {"mrr": 0.3333, "hit": 0.3333, "mean_returned": 0.667,
                                                  "mean_wrong": 0.333})
        self.assertEqual(t1.score(SYN, [])["needs"], 0)

    def test_validate(self):
        meta = {"team_id": "T", "submission_id": "s1", "info_need": "q"}
        rows = [{"metadata": dict(meta, info_need_id="1"), "response": ["1", "PMC2"]},
                {"metadata": dict(meta, info_need_id="2"), "response": ["1", "2", "3", "4", "5", "6"]},
                {"metadata": dict(meta, info_need_id="3"), "response": ["5", "5"]},
                {"metadata": dict(meta, info_need_id="4"), "response": ["abc", "0123", 7]},
                {"metadata": dict(meta, info_need_id="1"), "response": ["9"]},
                {"metadata": {"team_id": "T"}, "response": ["9"]},
                "{",
                {"metadata": dict(meta, info_need_id="8"), "response": []},
                {"metadata": dict(meta, info_need_id="9"), "response": "1"}]
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "sub.jsonl")
            dump(p, rows)
            v = t1.validate(p)
        self.assertEqual((v["lines"], v["empty_responses"]), (9, 1))
        self.assertEqual([x.split(":")[0] for x in v["problems"]],
                         ["line 2", "line 3", "line 4", "line 5", "line 6", "line 7", "line 9"])
        self.assertIn("6 items > 5", v["problems"][0])
        self.assertIn("'abc', '0123', 7", v["problems"][2])

    def test_devsets(self):
        with tempfile.TemporaryDirectory() as d:
            rq, rt, lm = inputs(d)
            c = t1.devsets(rq, os.path.join(d, "dev"), rt, lm)
            self.assertEqual(c, {"r": 2, "rt": 2, "l": 2, "duplicate_ids": []})
            needs_l = t1.load_jsonl(os.path.join(d, "dev", "needs_l.jsonl"))
            self.assertEqual([n["info_need_id"] for n in needs_l], ["L01", "L37"])
            gold = {g["info_need_id"]: g["gold"] for g in t1.load_jsonl(os.path.join(d, "dev", "gold.jsonl"))}
            self.assertEqual(gold, {"R-1": ["1"], "R-4": ["4"], "RT-1": ["1"], "RT-4": ["4"],
                                    "L01": ["3"], "L37": ["8458085"]})

    def test_end_to_end(self):
        with tempfile.TemporaryDirectory() as d:
            db = index(d)
            rq, rt, lm = inputs(d)
            dev, out = os.path.join(d, "dev"), os.path.join(d, "out")
            self.assertEqual(t1.main(["devsets", "--r-questions", rq, "--r-titles", rt, "--landmarks", lm,
                                      "--out-dir", dev]), 0)
            gold = os.path.join(dev, "gold.jsonl")
            self.assertEqual(t1.main(["run", "--db", db, "--needs", os.path.join(dev, "needs_r.jsonl"),
                                      "--out-dir", out, "--gold", gold, "--team-id", "MV2"]), 0)
            with open(os.path.join(out, "run.json"), encoding="utf-8") as f:
                r = json.load(f)
            self.assertEqual((r["needs"], r["index_docs"], r["no_candidates"]), (2, 10, 0))
            self.assertEqual(r["gold_missing_from_index"], ["8458085"])
            self.assertEqual(r["validate"], {"lines": 2, "empty_responses": 0, "problems": []})
            ranked = t1.load_jsonl(os.path.join(out, "ranked.jsonl"))
            self.assertEqual([x["candidates"][0][0] for x in ranked], [1, 4])
            self.assertEqual([len(x["candidates"]) for x in ranked], [3, 1])
            sub = t1.load_jsonl(os.path.join(out, "submission.jsonl"))
            self.assertEqual(sub[1], {"metadata": {"team_id": "MV2", "submission_id": "dev",
                                                   "info_need_id": "R-4",
                                                   "info_need": "the work on calcium oxalate kidney deposits"},
                                      "response": ["4"]})
            self.assertEqual(t1.main(["score", "--ranked", os.path.join(out, "ranked.jsonl"), "--gold", gold,
                                      "--out-dir", out]), 0)
            with open(os.path.join(out, "scores.json"), encoding="utf-8") as f:
                s = json.load(f)
            self.assertEqual(s["recall_at"], {"1": 1.0, "5": 1.0, "10": 1.0, "20": 1.0})
            self.assertEqual(s["policies"]["top:5"], {"mrr": 1.0, "hit": 1.0, "mean_returned": 2.0,
                                                      "mean_wrong": 1.0})
            self.assertEqual(s["policies"]["top:1"]["mean_wrong"], 0.0)
            self.assertEqual(t1.main(["validate", os.path.join(out, "submission.jsonl")]), 0)
            with self.assertRaises(FileNotFoundError):
                t1.run(os.path.join(d, "none.db"), os.path.join(dev, "needs_r.jsonl"), out)
            with self.assertRaises(ValueError):
                t1.run(db, os.path.join(dev, "needs_r.jsonl"), out, policy="top:9")


if __name__ == "__main__":
    unittest.main()
