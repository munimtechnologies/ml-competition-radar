"""probe.py 0.1.0 - record what an installed kickmix offers (Apache-2.0).

MV2 of Munim, Inc. (AI agents working in his name), for the Google Quantum AI "Verifiable
Quantum Circuit Compilation" Kaggle competition. Imports kickmix, walks its public names and
writes their kinds, signatures and docstrings to api.json and api.txt, so the next circuit
code can be written against the real API. Reads no competition data.

  python probe.py --out-dir D [--src-dir S]

--src-dir: a Qualtran checkout's kickmix/src; its .py files are listed with sizes and first
docstring lines (examples of how circuits are built).
"""
import argparse
import inspect
import json
import os
import platform
import sys
import time

VERSION = "0.1.0"


def first_line(doc):
    doc = (doc or "").strip()
    return doc.splitlines()[0] if doc else ""


def describe(obj):
    try:
        sig = str(inspect.signature(obj))
    except (TypeError, ValueError):
        sig = ""
    return {"kind": type(obj).__name__, "signature": sig, "doc": (inspect.getdoc(obj) or "")[:4000]}


def walk(mod):
    out = {}
    for name in sorted(dir(mod)):
        if name.startswith("_"):
            continue
        obj = getattr(mod, name)
        entry = describe(obj)
        if inspect.isclass(obj):
            entry["members"] = {}
            for m in sorted(dir(obj)):
                if m.startswith("_") and m not in ("__init__", "__call__"):
                    continue
                try:
                    entry["members"][m] = describe(getattr(obj, m))
                except Exception as e:  # some pybind11 properties raise on the class
                    entry["members"][m] = {"kind": "error", "signature": "", "doc": repr(e)}
        out[name] = entry
    return out


def list_sources(src_dir):
    rows = []
    for root, _, files in os.walk(src_dir):
        for f in sorted(files):
            if f.endswith(".py"):
                p = os.path.join(root, f)
                with open(p, encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
                doc = ""
                if text.lstrip().startswith(('"""', "'''")):
                    doc = first_line(text.lstrip()[3:].split('"""')[0].split("'''")[0])
                rows.append({"path": os.path.relpath(p, src_dir).replace(os.sep, "/"),
                             "bytes": len(text.encode("utf-8")), "lines": text.count("\n"), "doc": doc})
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--src-dir", default="")
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    t0 = time.time()
    import kickmix
    api = walk(kickmix)
    report = {"version": VERSION, "python": sys.version.split()[0], "machine": platform.machine(),
              "kickmix_file": getattr(kickmix, "__file__", ""),
              "kickmix_version": getattr(kickmix, "__version__", ""),
              "public_names": len(api), "api": api}
    if a.src_dir:
        report["sources"] = list_sources(a.src_dir)
    report["seconds"] = round(time.time() - t0, 2)
    with open(os.path.join(a.out_dir, "api.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)
    with open(os.path.join(a.out_dir, "api.txt"), "w", encoding="utf-8") as f:
        for name, e in api.items():
            f.write("== %s (%s) %s\n%s\n" % (name, e["kind"], e["signature"], e["doc"]))
            for m, me in e.get("members", {}).items():
                f.write("  -- %s.%s %s: %s\n" % (name, m, me["signature"], first_line(me["doc"])))
            f.write("\n")
    print(json.dumps({"public_names": len(api), "names": sorted(api)[:80],
                      "sources": len(report.get("sources", [])), "seconds": report["seconds"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
