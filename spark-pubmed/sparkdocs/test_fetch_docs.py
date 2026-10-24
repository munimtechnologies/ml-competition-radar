import io
import json
import os
import sys
import tempfile
import unittest
import zipfile
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch_docs  # noqa: E402

BASE = "https://repo.example/challenges/166"
PAGE = ('<a href="/files/a.pdf">a</a>'
        '<a href="https://b.s3.amazonaws.com/x/Rules%20One.docx?X-Amz-Date=1&amp;X-Amz-Signature=z">r</a>'
        '<a href="/page.html">p</a>'
        r'<script>{"u": "https:\/\/b.s3.amazonaws.com\/x\/Ann.pdf?X-Amz-Date=2&X-Amz-Signature=y"}</script>'
        ' see https://b.s3.amazonaws.com/x/Rules%20One.docx?X-Amz-Date=3 again')


def make_docx(paras):
    body = "".join('<w:p><w:r><w:t>%s</w:t></w:r><w:r><w:tab/><w:t xml:space="preserve">%s</w:t></w:r></w:p>' % p
                   for p in paras)
    xml = ('<?xml version="1.0"?><w:document xmlns:w="http://schemas.openxmlformats.org/'
           'wordprocessingml/2006/main"><w:body>%s</w:body></w:document>' % body)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("word/document.xml", xml)
    return buf.getvalue()


class FetchDocs(unittest.TestCase):
    def test_doc_links(self):
        self.assertEqual(fetch_docs.doc_links(PAGE, BASE), [
            ("https://repo.example/files/a.pdf", "/files/a.pdf"),
            ("https://b.s3.amazonaws.com/x/Rules%20One.docx?X-Amz-Date=1&X-Amz-Signature=z", "/x/Rules One.docx"),
            ("https://b.s3.amazonaws.com/x/Ann.pdf?X-Amz-Date=2&X-Amz-Signature=y", "/x/Ann.pdf")])
        self.assertEqual(fetch_docs.scrub("bad https://s/x.pdf?X-Amz-Signature=q here"),
                         "bad https://s/x.pdf?<signed> here")

    def test_docx_text(self):
        self.assertEqual(fetch_docs.docx_text(make_docx([("Scoring", "MRR"), ("Penalty", "none")])),
                         "Scoring\tMRR\nPenalty\tnone\n")
        self.assertEqual(fetch_docs.safe_name("/d/Rules A (v2).docx"), "Rules_A__v2_.docx")

    def test_fetch(self):
        page = ('<a href="https://s3.example/d/Rules%20A.docx?X-Amz-Signature=s">r</a>'
                '<a href="/d/Ann.pdf">a</a><a href="/d/Gone.pdf">g</a>')
        files = {"https://repo.example/c/166": page.encode(),
                 "https://s3.example/d/Rules%20A.docx?X-Amz-Signature=s": make_docx([("Rule", "one")]),
                 "https://repo.example/d/Ann.pdf": b"%PDF-not-really"}

        def read(url):
            if url not in files:
                raise OSError("HTTP Error 403: Forbidden")
            return files[url]

        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(fetch_docs, "pdf_text", side_effect=ValueError("bad pdf")):
            rep = fetch_docs.fetch(["https://repo.example/c/166", "https://repo.example/c/none"], d, read)
            self.assertEqual(sorted(os.listdir(os.path.join(d, "docs"))),
                             ["p0_Ann.pdf", "p0_Rules_A.docx", "p0_Rules_A.docx.txt"])
            with open(os.path.join(d, "fetch_docs.json"), encoding="utf-8") as f:
                saved = f.read()
        self.assertEqual(json.loads(saved), rep)
        self.assertNotIn("X-Amz", saved)
        entry = rep["pages"][0]
        self.assertEqual((len(rep["pages"]), entry["doc_links"], entry["signed_links"]), (1, 3, 1))
        docs = entry["docs"]
        self.assertEqual((docs[0]["file"], docs[0]["text_chars"]), ("p0_Rules_A.docx", 9))
        self.assertEqual(docs[1]["text_error"], "ValueError: bad pdf")
        self.assertEqual(docs[2]["error"], "OSError: HTTP Error 403: Forbidden")
        self.assertEqual(rep["problems"], ["/d/Ann.pdf: no text", "/d/Gone.pdf: download failed",
                                           "https://repo.example/c/none: OSError: HTTP Error 403: Forbidden"])


if __name__ == "__main__":
    unittest.main()
