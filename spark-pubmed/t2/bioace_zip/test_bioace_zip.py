# Copyright 2026 Munim, Inc. (MV2). Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Offline tests for bioace_zip.py: a zip built in memory stands in for the remote archive."""
import io
import json
import os
import struct
import tempfile
import unittest
import zipfile

import bioace_zip as bz

NUGGETS = [{"question_id": 1, "nuggets": ["alpha bravo charlie", "delta echo"]},
           {"question_id": "2", "nuggets": ["foxtrot golf"]}]
ANSWERS = '{"id": 7, "answer_sentences": [{"text": "hotel india"}]}\n{"id": 8, "answer_sentences": []}\n'


def bundle():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("resources/", "")
        z.writestr("resources/data/task_b_gt_nuggets_test.json", json.dumps(NUGGETS))
        z.writestr("resources/data/answers.jsonl", ANSWERS, compress_type=zipfile.ZIP_STORED)
        z.writestr("resources/models/model.bin", b"\0" * 5000)
        z.comment = b"bundle"
    return buf.getvalue()


class Fake:
    def __init__(self, blob):
        self.blob = blob

    def probe(self):
        return len(self.blob)

    def read(self, start, n):
        return self.blob[start:start + n] if n > 0 else b""


class TestZip(unittest.TestCase):
    def run_survey(self):
        res = {}
        with tempfile.TemporaryDirectory() as root:
            bz.survey(Fake(bundle()), root, res)
            saved = {e["saved"]: open(os.path.join(root, *e["saved"].split("/")), "rb").read()
                     for e in res["picked"] if "saved" in e}
        return res, saved

    def test_lists_every_member(self):
        res, _ = self.run_survey()
        self.assertFalse(res["zip64"])
        self.assertEqual((res["members_expected"], res["members_total"], res["files"]), (4, 4, 3))
        sizes = {i.filename: i.file_size for i in zipfile.ZipFile(io.BytesIO(bundle())).infolist()}
        self.assertEqual({m["name"]: m["size"] for m in res["members"]}, sizes)
        self.assertEqual(res["folders"]["resources/models"], {"files": 1, "bytes": 5000})

    def test_unpacks_only_data_files_intact(self):
        res, saved = self.run_survey()
        self.assertEqual([e["name"] for e in res["picked"]],
                         ["resources/data/task_b_gt_nuggets_test.json", "resources/data/answers.jsonl"])
        self.assertEqual(saved["resources/data/task_b_gt_nuggets_test.json"], json.dumps(NUGGETS).encode())
        self.assertEqual(saved["resources/data/answers.jsonl"], ANSWERS.encode())

    def test_describes_nuggets_without_text(self):
        res, _ = self.run_survey()
        d = res["picked"][0]["describe"]
        self.assertEqual((d["format"], d["records"]), ("json", 2))
        self.assertEqual(d["ids"]["list"], [1, 2])
        self.assertEqual(d["list_fields"]["nuggets"],
                         {"records": 2, "total": 3, "median": 1.5, "min": 1, "max": 2, "empty": 0, "mean_words": 2.33})
        self.assertIn("nuggets: list[str]", d["shape"])
        j = res["picked"][1]["describe"]
        self.assertEqual((j["format"], j["records"], j["ids"]["list"]), ("jsonl", 2, [7, 8]))
        self.assertEqual(j["list_fields"]["answer_sentences"]["empty"], 1)
        text = json.dumps(res)
        for word in ("alpha", "foxtrot", "hotel"):
            self.assertNotIn(word, text)

    def test_size_caps_skip(self):
        old = bz.MAX_MEMBER
        bz.MAX_MEMBER = 1
        try:
            res, saved = self.run_survey()
        finally:
            bz.MAX_MEMBER = old
        self.assertEqual(saved, {})
        self.assertTrue(all(e.get("skipped") for e in res["picked"]))


class TestParts(unittest.TestCase):
    def test_zip64_extra(self):
        extra = struct.pack("<HH", 0x5455, 5) + b"\x01abcd" + struct.pack("<HHQQ", 1, 16, 5000000000, 4000000000)
        self.assertEqual(bz.zip64_extra(extra, 0xFFFFFFFF, 0xFFFFFFFF, 123), (5000000000, 4000000000, 123))
        self.assertEqual(bz.zip64_extra(b"", 10, 9, 8), (10, 9, 8))

    def test_zip64_eocd(self):
        rec = struct.pack("<IQHHIIQQQQ", 0x06064B50, 44, 45, 45, 0, 0, 3, 3, 777, 10)
        blob = b"X" * 10 + rec + struct.pack("<IIQI", 0x07064B50, 0, 10, 1)
        self.assertEqual(bz.zip64_eocd(lambda s, n: blob[s:s + n], len(blob)), (3, 777, 10))

    def test_save_stays_inside_root(self):
        with tempfile.TemporaryDirectory() as root:
            rel = bz.save(root, "../../x/y.json", b"{}")
            self.assertEqual(rel, "x/y.json")
            self.assertTrue(os.path.exists(os.path.join(root, "x", "y.json")))

    def test_shapes_and_records(self):
        self.assertEqual(bz.shape({"1": ["a"], "2": ["b"]}), "dict{<2 numeric ids>: list[str]}")
        d = bz.describe("n.json", json.dumps({"1": ["alpha one", "b c"], "3": ["d e f"]}).encode())
        self.assertEqual((d["records"], d["ids"]["list"], d["list_fields"]["_items"]["total"]), (2, [1, 3], 3))
        w = bz.describe("w.json", json.dumps({"version": "1", "questions": NUGGETS}).encode())
        self.assertEqual(w["records"], 2)

    def test_medaesqa_keys(self):
        items = [{"question_id": "1", "expert_curated_nuggets": None,
                  "machine_generated_answers": {"M1": {"answer": "x", "answer_sentences": []}}},
                 {"question_id": "2", "machine_generated_answers": {}}]
        k = bz.medaesqa_keys(items)
        self.assertEqual(k["items"], 2)
        self.assertEqual(k["fields"]["expert_curated_nuggets"], {"present": 1, "null": 1, "empty": 0, "shapes": {"NoneType": 1}})
        self.assertEqual(k["fields"]["machine_generated_answers"]["empty"], 1)
        self.assertEqual(k["machine_answer_fields"], {"answer": 1, "answer_sentences": 1})


if __name__ == "__main__":
    unittest.main()
