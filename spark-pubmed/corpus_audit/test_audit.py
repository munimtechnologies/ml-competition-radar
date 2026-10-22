"""Fake-data tests for audit.py (no network). MV2 of Munim, Inc. Apache-2.0."""
import gzip
import hashlib
import io
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audit  # noqa: E402


def art(pmid, pubdate, extra="", elec="", pmc=False, abstract=True, ptype="D016428"):
    return ("<PubmedArticle><MedlineCitation><PMID Version=\"1\">%d</PMID><Article><Journal><JournalIssue>"
            "<PubDate>%s</PubDate></JournalIssue></Journal><ArticleTitle>T%d</ArticleTitle>%s%s"
            "<PublicationTypeList><PublicationType UI=\"%s\">X</PublicationType></PublicationTypeList>"
            "</Article>%s</MedlineCitation><PubmedData><History><PubMedPubDate PubStatus=\"pubmed\">"
            "<Year>2026</Year><Month>8</Month><Day>2</Day></PubMedPubDate></History><ArticleIdList>"
            "<ArticleId IdType=\"pubmed\">%d</ArticleId>%s</ArticleIdList></PubmedData></PubmedArticle>"
            % (pmid, pubdate, pmid, "<Abstract><AbstractText>A</AbstractText></Abstract>" if abstract else "",
               elec, ptype, extra, pmid, "<ArticleId IdType=\"pmc\">PMC%d</ArticleId>" % pmid if pmc else ""))


def elec(y, m, d):
    return "<ArticleDate DateType=\"Electronic\"><Year>%d</Year><Month>%02d</Month><Day>%02d</Day></ArticleDate>" % (y, m, d)


FILE1 = ("<PubmedArticleSet>" + art(1, "<MedlineDate>1975 Jan-Feb</MedlineDate>", pmc=True)
         + art(2, "<Year>1950</Year>", abstract=False)
         + art(3, "<Year>2026</Year><Month>Sep</Month>", elec=elec(2026, 6, 10),
               extra="<MeshHeadingList><MeshHeading><DescriptorName>M</DescriptorName></MeshHeading></MeshHeadingList>")
         + "</PubmedArticleSet>")
FILE2 = ("<PubmedArticleSet>" + art(4, "<Year>2026</Year><Month>Aug</Month>", elec=elec(2026, 8, 5),
                                      ptype=audit.PREPRINT)
         + art(3, "<Year>2026</Year><Month>Sep</Month>")
         + art(5, "<Year>2026</Year><Season>Summer</Season>")
         + "<DeleteCitation><PMID Version=\"1\">7</PMID><PMID Version=\"1\">8</PMID></DeleteCitation>"
         + "</PubmedArticleSet>")


def gz(text):
    return gzip.compress(text.encode("utf-8"))


def site(files, bad_md5=()):
    """URL -> bytes for a fake .pubmed-spark directory."""
    pages = {}
    links = []
    for name, body in files.items():
        data = gz(body)
        md5 = "0" * 32 if name in bad_md5 else hashlib.md5(data).hexdigest()
        pages[audit.BASE + name] = data
        pages[audit.BASE + name + ".md5"] = ("MD5(%s)= %s\n" % (name, md5)).encode()
        links.append('<a href="%s">%s</a> <a href="%s.md5">%s.md5</a>' % (name, name, name, name))
    pages[audit.BASE] = ("<html>" + "\n".join(links) + "</html>").encode()
    return pages


def opener_for(pages, calls=None):
    def opener(url, timeout=120):
        if calls is not None:
            calls.append(url)
        if url not in pages:
            raise OSError("no such url")
        return io.BytesIO(pages[url])
    return opener


class UnitTest(unittest.TestCase):
    def test_list_and_pick(self):
        names = ["pubmed27n%04d.xml.gz" % i for i in range(1, 6)]
        pages = site({n: "<PubmedArticleSet/>" for n in names})
        self.assertEqual(audit.list_files(opener_for(pages)), names)
        self.assertEqual([n[9:13] for n in audit.pick(names, 2, ["0004"])], ["0001", "0003", "0004", "0005"])
        self.assertEqual(audit.pick(names, 0, []), names)

    def test_dates(self):
        el = audit.ET.fromstring("<D><MedlineDate>1975 Jan-Feb</MedlineDate></D>")
        self.assertEqual(audit.ymd(el), (1975, 1, None))
        el = audit.ET.fromstring("<D><Year>2026</Year><Month>07</Month><Day>31</Day></D>")
        self.assertEqual(audit.ymd(el), (2026, 7, 31))
        self.assertIs(audit.after_end((2026, 7, 31)), False)
        self.assertIs(audit.after_end((2026, 8, 1)), True)
        self.assertIsNone(audit.after_end((2026, None, None)))
        self.assertIs(audit.after_end((2027, None, None)), True)
        self.assertIsNone(audit.ymd(None))

    def test_scan_counts(self):
        st, pmids, ex, years = audit.scan(io.BytesIO(FILE2.encode()))
        self.assertEqual(list(pmids), [4, 3, 5])
        self.assertEqual(st["records"], 3)
        self.assertEqual(st["preprint"], 1)
        self.assertEqual(st["deleted_pmids"], 2)
        self.assertEqual(st["journal_after_2026_07"], 2)
        self.assertEqual(st["journal_2026_no_month"], 1)
        self.assertEqual(st["electronic_after_2026_07"], 1)
        self.assertEqual(st["pubmed_after_2026_07"], 3)
        self.assertEqual(st["no_date_on_or_before_end"], 2)  # 4 (Aug + Aug) and 3 (Sep only)
        self.assertEqual(ex["preprint"], [[4, None]])
        self.assertEqual(years, {"2026": 3})


class RunTest(unittest.TestCase):
    def test_run_resume_and_crosscheck(self):
        files = {"pubmed27n0001.xml.gz": FILE1, "pubmed27n0002.xml.gz": FILE2,
                 "pubmed27n0003.xml.gz": FILE1.replace(">1<", ">11<").replace(">2<", ">12<").replace(">3<", ">13<")}
        with tempfile.TemporaryDirectory() as d:
            data, base = os.path.join(d, "data"), os.path.join(d, "base")
            os.makedirs(base)
            with open(os.path.join(base, "pubmed26n0001.jsonl"), "w", encoding="utf-8") as f:
                for pmid, year in (("1", 1975), ("2", 1950), ("99", 1980)):
                    f.write(json.dumps({"pmid": pmid, "year": year}) + "\n")
            pages = site(files, bad_md5={"pubmed27n0003.xml.gz"})
            s = audit.run(data, os.path.join(d, "out"), 1, [], 1, base, opener_for(pages))
            self.assertEqual(s["listing_files"], 3)
            self.assertGreater(s["data_disk_gb"]["total"], 0)
            self.assertEqual(s["files_ok"], 2)
            self.assertEqual(s["files_failed"], ["pubmed27n0003.xml.gz"])
            self.assertIn("1 file(s) failed", s["problem"])
            self.assertEqual(s["totals"]["records"], 6)
            self.assertEqual(s["totals"]["journal_before_1959"], 1)
            self.assertEqual(s["totals"]["with_pmcid"], 1)
            self.assertEqual(s["totals"]["with_mesh"], 1)
            self.assertEqual(s["duplicate_pmids"], 1)
            self.assertEqual((s["pmid_min"], s["pmid_max"]), (1, 5))
            self.assertEqual(s["records_per_file"], [3])
            self.assertIsNone(s["last_file_records"])  # the last file failed its md5
            self.assertEqual(s["examples"]["journal_before_1959"], [[2, [1950, None, None]]])
            cc = s["baseline_crosscheck"]["0001"]["same_numbered_file"]
            self.assertEqual(cc["before_1959"], {"records": 1, "in_spark_file": 1})
            self.assertEqual(cc["1959_on"], {"records": 2, "in_spark_file": 1})
            self.assertEqual(len(open(os.path.join(d, "out", "files.jsonl")).read().splitlines()), 3)
            self.assertFalse(os.path.exists(audit.paths(data, "pubmed27n0003.xml.gz")[0]))

            calls = []
            pages = site(files)
            s2 = audit.run(data, os.path.join(d, "out2"), 1, [], 1, base, opener_for(pages, calls))
            self.assertIsNone(s2["problem"])
            self.assertEqual(s2["totals"]["records"], 9)
            self.assertEqual(s2["last_file_records"], 3)
            fetched = [c for c in calls if c.endswith(".xml.gz")]
            self.assertEqual(fetched, [audit.BASE + "pubmed27n0003.xml.gz"])  # 0001/0002 resumed


if __name__ == "__main__":
    unittest.main()
