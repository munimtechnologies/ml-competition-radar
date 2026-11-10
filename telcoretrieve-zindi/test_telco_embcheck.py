"""Offline tests for telco_embcheck (no network, no torch). MV2 of Munim, Inc. Apache-2.0."""
import io
import os
import pickle
import sqlite3
import struct
import subprocess
import sys
import types
import unittest

import numpy as np

import telco_embcheck as tc


def make_header(**over):
    v = dict(version=1, offset_level0=0, max_elements=1064960, cur_element_count=1064000,
             size_data_per_element=4236, label_offset=4228, offset_data=132, maxlevel=4,
             enterpoint_node=7, maxM=16, maxM0=32, M=16, mult=0.36, ef_construction=100)
    v.update(over)
    return struct.pack(tc.HEADER_FMT, *[v[n] for n in tc.HEADER_NAMES]), v


class TestLayout(unittest.TestCase):
    def test_header_size_and_roundtrip(self):
        self.assertEqual(struct.calcsize(tc.HEADER_FMT), 100)
        b, v = make_header()
        h = tc.parse_header(b)
        self.assertEqual(h, v)
        self.assertEqual(tc.header_dim(h), 1024)
        with self.assertRaises(ValueError):
            tc.parse_header(b[:99])

    def test_element(self):
        h = tc.parse_header(make_header()[0])
        b = bytearray(4236)
        struct.pack_into("<H", b, 0, 5)
        b[2] = 1
        b[132:4228] = np.arange(1024, dtype="<f4").tobytes()
        struct.pack_into("<Q", b, 4228, 77)
        el = tc.parse_element(bytes(b), h)
        self.assertEqual(el["links"], 5)
        self.assertTrue(el["deleted"])
        self.assertEqual(el["label"], 77)
        self.assertEqual(el["vector"].shape, (1024,))
        self.assertEqual(el["vector"][3], 3.0)
        b[2] = 0
        self.assertFalse(tc.parse_element(bytes(b), h)["deleted"])
        with self.assertRaises(ValueError):
            tc.parse_element(bytes(b[:-1]), h)


class TestPickle(unittest.TestCase):
    def test_chroma_class_is_stubbed(self):
        fake = types.ModuleType("chromadb")

        class PersistentData:
            def __init__(self):
                self.dimensionality = 1024
                self.total_elements_added = 2
                self.max_seq_id = 9
                self.id_to_label = {"a": 1, "b": 2}
                self.label_to_id = {1: "a", 2: "b"}
                self.id_to_seq_id = {"a": 5, "b": 6}
        PersistentData.__module__ = "chromadb"
        PersistentData.__qualname__ = "PersistentData"
        fake.PersistentData = PersistentData
        old = sys.modules.get("chromadb")
        sys.modules["chromadb"] = fake
        try:
            blob = pickle.dumps(PersistentData(), pickle.HIGHEST_PROTOCOL)
        finally:
            if old is None:
                del sys.modules["chromadb"]
            else:
                sys.modules["chromadb"] = old
        obj, seen = tc.safe_load(io.BytesIO(blob))
        self.assertIsInstance(obj, tc.Stub)
        self.assertEqual(seen, ["chromadb.PersistentData"])
        m, src = tc.find_label_map(obj)
        self.assertEqual(src, "label_to_id")
        self.assertEqual(m, {1: "a", 2: "b"})
        s = tc.pickle_summary(obj)
        self.assertEqual(s["total_elements_added"], 2)
        self.assertEqual(s["label_to_id_len"], 2)

    def test_foreign_global_refused(self):
        blob = pickle.dumps(subprocess.Popen)
        with self.assertRaises(pickle.UnpicklingError):
            tc.safe_load(io.BytesIO(blob))

    def test_plain_dict_inverted(self):
        obj = {"dimensionality": 3, "id_to_label": {"x": 5}, "id_to_seq_id": {"x": 9}}
        obj2, _ = tc.safe_load(io.BytesIO(pickle.dumps(obj)))
        m, src = tc.find_label_map(obj2)
        self.assertEqual(m, {5: "x"})
        self.assertEqual(src, "id_to_label (inverted)")
        with self.assertRaises(ValueError):
            tc.find_label_map({"id_to_seq_id": {"x": 9}})


class TestLookup(unittest.TestCase):
    def make(self):
        conn = sqlite3.connect(":memory:")
        try:
            conn.execute("CREATE VIRTUAL TABLE chunks USING fts5(chunk_id UNINDEXED, text, source UNINDEXED)")
        except sqlite3.OperationalError:
            conn.execute("CREATE TABLE chunks (chunk_id TEXT, text TEXT, source TEXT)")
        conn.executemany("INSERT INTO chunks VALUES (?, ?, ?)", [
            ("id-1", "hello world long text", "a.pdf"),
            ("id-2", "second chunk text here", "b.pdf"),
            ("id-3", "third", "c.pdf")])
        return conn

    def test_found(self):
        found, how = tc.lookup_texts(self.make(), ["id-9", "id-2"])
        self.assertEqual(found, {"id-2": "second chunk text here"})
        self.assertEqual((how["table"], how["id_column"], how["text_column"]), ("chunks", "chunk_id", "text"))

    def test_not_found_reports_schema(self):
        with self.assertRaises(LookupError) as cm:
            tc.lookup_texts(self.make(), ["zzz"])
        self.assertIn("chunk_id", str(cm.exception))


class TestGrading(unittest.TestCase):
    def test_classify(self):
        self.assertEqual(tc.classify(0.995, 0.90), "document")
        self.assertEqual(tc.classify(0.90, 0.999), "query")
        self.assertEqual(tc.classify(0.991, 0.992), "both")
        self.assertEqual(tc.classify(0.5, 0.6), "neither")

    def test_grade(self):
        h = tc.parse_header(make_header()[0])
        q = [{"verdict": "query", "cos_doc": 0.9, "cos_query": 0.999, "cos_doc_vs_query": 0.9}] * 95 + [{}] * 5
        d = [{"verdict": "document", "cos_doc": 0.999, "cos_query": 0.9, "cos_doc_vs_query": 0.9}] * 40
        res = {"otel": {"header": h, "summary": tc.cell_summary(q)}, "control": {"summary": tc.cell_summary(d)}}
        self.assertEqual(res["otel"]["summary"]["resolved"], 95)
        self.assertEqual(tc.grade(res), {"E1": True, "E2": True, "E3": True, "E4": True, "E5": True})
        bad = dict(h, max_elements=1072821)
        res["otel"]["header"] = bad
        self.assertFalse(tc.grade(res)["E1"])
        self.assertEqual(tc.grade({}), {"E1": False, "E2": False, "E3": False, "E4": False, "E5": False})


if __name__ == "__main__":
    unittest.main()
