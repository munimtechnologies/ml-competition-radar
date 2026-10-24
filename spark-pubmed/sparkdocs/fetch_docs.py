"""Fetch the SPARK challenge pages' attached documents (rules .docx, announcement .pdf) and extract
their text (job spark-docs-v1).

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

The challenge pages at repository.niddk.nih.gov link their documents through pre-signed S3 URLs
that expire 10 minutes after the page is served, so a link cannot be handed to another tool. This
reads each page, follows every .docx/.pdf link at once, saves the file and its text, and records
only the link's path, never its signed query string. Standard library, plus pypdf for PDFs.

  python fetch_docs.py --page URL [--page URL ...] --out-dir D
"""
import argparse
import hashlib
import html
import io
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

VERSION = "0.1.0"
USER_AGENT = "MV2-Munim-Inc-research (mv2@munimtech.com)"
HREF_RX = re.compile(r'href\s*=\s*["\']([^"\']+)["\']', re.I)
URL_RX = re.compile(r'https?://[^\s"\'<>\\]+')
SIGNED_RX = re.compile(r"\?[^\s'\"]*X-Amz-[^\s'\"]*")
DOC_EXT = (".docx", ".pdf")
MAX_BYTES = 20 * 2**20
MAX_DOCS = 20  # per page
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def read_url(url, limit=MAX_BYTES):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read(limit + 1)
    if len(data) > limit:
        raise ValueError("over %d bytes" % limit)
    return data


def scrub(text):
    """Drop any signed query string from a message."""
    return SIGNED_RX.sub("?<signed>", text)


def doc_links(page_html, base):
    """[(absolute url, unquoted path)] of links to .docx or .pdf files: href values first, then
    bare URLs (JSON-escaped slashes and ampersands undone), one per path, first seen first."""
    text = page_html.replace("\\/", "/").replace("\\u0026", "&")
    cands = [urllib.parse.urljoin(base, html.unescape(h)) for h in HREF_RX.findall(text)]
    cands += [html.unescape(u) for u in URL_RX.findall(text)]
    out, seen = [], set()
    for url in cands:
        path = urllib.parse.unquote(urllib.parse.urlsplit(url).path)
        if path.lower().endswith(DOC_EXT) and path not in seen:
            seen.add(path)
            out.append((url, path))
    return out


def docx_text(data):
    """Paragraph text of a .docx (word/document.xml), one paragraph per line; tabs and breaks kept."""
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    lines = []
    for p in root.iter(W + "p"):
        parts = []
        for el in p.iter():
            if el.tag == W + "t" and el.text:
                parts.append(el.text)
            elif el.tag == W + "tab":
                parts.append("\t")
            elif el.tag in (W + "br", W + "cr"):
                parts.append("\n")
        lines.append("".join(parts))
    return "\n".join(lines).strip() + "\n"


def pdf_text(data):
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(data))
    return "\n\f".join((page.extract_text() or "") for page in reader.pages)


def safe_name(path):
    return re.sub(r"[^A-Za-z0-9._-]", "_", os.path.basename(path)) or "file"


def fetch(pages, out_dir, read=read_url):
    """Save every linked document of every page under out_dir/docs, with a .txt beside it;
    write fetch_docs.json (paths, sizes, sha256, text length; no signed URLs)."""
    docs_dir = os.path.join(out_dir, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    rep = {"version": VERSION, "pages": [], "problems": []}
    for i, page in enumerate(pages):
        try:
            body = read(page).decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001 - recorded, next page
            rep["problems"].append("%s: %s" % (page, scrub("%s: %s" % (type(e).__name__, e))))
            continue
        links = doc_links(body, page)
        entry = {"page": page, "page_chars": len(body), "doc_links": len(links),
                 "signed_links": sum(1 for u, _ in links if "X-Amz-" in u), "docs": []}
        for url, path in links[:MAX_DOCS]:
            name = "p%d_%s" % (i, safe_name(path))
            d = {"path": path, "file": name}
            entry["docs"].append(d)
            try:
                data = read(url)
            except Exception as e:  # noqa: BLE001
                d["error"] = scrub("%s: %s" % (type(e).__name__, e))
                rep["problems"].append("%s: download failed" % path)
                continue
            d.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
            with open(os.path.join(docs_dir, name), "wb") as f:
                f.write(data)
            try:
                text = docx_text(data) if path.lower().endswith(".docx") else pdf_text(data)
            except Exception as e:  # noqa: BLE001
                d["text_error"] = scrub("%s: %s" % (type(e).__name__, e))
                rep["problems"].append("%s: no text" % path)
                continue
            with open(os.path.join(docs_dir, name + ".txt"), "w", encoding="utf-8") as f:
                f.write(text)
            d["text_chars"] = len(text)
        rep["pages"].append(entry)
    with open(os.path.join(out_dir, "fetch_docs.json"), "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=1)
    return rep


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--page", action="append", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)
    rep = fetch(a.page, a.out_dir)
    print(json.dumps(rep, indent=1))
    texts = sum(1 for p in rep["pages"] for d in p["docs"] if "text_chars" in d)
    return 0 if texts and not rep["problems"] else 1


if __name__ == "__main__":
    sys.exit(main())
