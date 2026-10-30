"""spark49: build MV2's SPARK Task 1 Docker image for the first time and run it with no network on a
five-paper test index mounted read-only. Run once, on a machine with Docker (MV2's Dell).

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

Everything it writes stays in this script's folder: ctx/ (the build context), fx/ (the test
index), io/ (questions and the system's output) and out/report.json. It downloads the six code
files and the Dockerfile from munimtechnologies/ml-competition-radar at pinned commits and the
MedCPT cross-encoder (public domain, NCBI) from Hugging Face at a pinned revision, and checks
every sha256 against the values spark48-image-v1 measured in /app. Then it builds the image as
mv2-spark-t1:spark49, runs it only with --network none, and removes that image at the end. It
uploads nothing, and touches no other image, container or volume. Standard library only.

  python spark49_image.py
"""
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request

VERSION = "0.1.0"
HERE = os.path.dirname(os.path.abspath(__file__))
TAG = "mv2-spark-t1:spark49"
RAW = "https://raw.githubusercontent.com/munimtechnologies/ml-competition-radar/%s/spark-pubmed/%s"
HF = "https://huggingface.co/ncbi/MedCPT-Cross-Encoder/resolve/71caf65d4927987813984f54c284405a13fcca49/%s"
USER_AGENT = "MV2-Munim-Inc-research (mv2@munimtech.com)"
T1, RR, SY = ("ce37c206eb600473223b7773a9b11381dc7fb76b", "99ade99976454f499af8f1ea2092083fd6d14b0f",
              "9a64c8e345ff47113391636475c1ae32c56df00e")
CODE = {  # build-context path: (commit, sha256 spark48 measured in /app)
    "t1_runner/t1.py": (T1, "eff77a880cae9916504f55a7a25d16183460d1338319ea2d3d52aaf52aa3d9b4"),
    "t1_runner/build_index.py": (T1, "595909e16b0a3b1638530eb70a712f4df34809d842503d73f40066f76550f1be"),
    "rerank/rerank.py": (RR, "2b5ccfa9c4a1663f3eabd9454a202e7960b51016ee0d7d0b8d96f00cc3cfe2c6"),
    "rerank/rerank_run.py": (RR, "25867eaf4fe1b8ff320caf0d18cd7d90ce8a8d0d7f71bd53d5bfb1c98686fae9"),
    "system/spark_t1.py": (SY, "33de48845f75a7e453881d67b7dadcfe52e2159dbfed9640e9dffe04c7b37b73"),
    "system/ro_db.py": (SY, "2ca63c2a17d936e7bdb2fed4ad7583e009c66eff7a3aca24f0d5d3346a95a75c"),
}
DOCKERFILE_COMMIT = "3db1432e6aca14857ead625e19b34508c5cdb65b"
DOCKERFILE_MUST = ("FROM python:3.12-slim",
                   'ENTRYPOINT ["python", "/app/spark_t1.py", "--db", "/index/spark_full.db", '
                   '"--model-dir", "/app/model", "--immutable"]')
MODEL = {
    "README.md": "8ab1ceed3beea346789e0b9cd7e04d6373dcf8b738fb63b996c7d97bb25df2ec",
    "added_tokens.json": "691a5ce0135045c12b8410af8d472ff8de864094df40ac9af418d6c644c7588d",
    "config.json": "1f375c7e8081f043c99fdb9c80059c44ed757cce7b05d333b7f3c81b1b713a42",
    "pytorch_model.bin": "61d5ccd48869e03500544525fc231641d7daa9ba267b202c82724750038dc1e0",
    "special_tokens_map.json": "cb63d0cbbf45160dc9cd786a257759593b798ae0c72957011016dbc3972df4e4",
    "tokenizer.json": "6e046044df8a2fcedb10607075dca187cae61d806c0d80a96c5b81017edc90c9",
    "tokenizer_config.json": "25e63abb25f637aa24981117b13394370693dd7bc140903d95008599b3abc1a9",
    "vocab.txt": "79489a52be45e6fa033521e8ce8e4f62aedc0a742ee2aa6fc04667e5b0b1454d",
}
# Five made-up test records (not PubMed text), and two questions whose best record is clear.
DOCS = [(101, "Aspirin for prevention of heart attack",
         "Low-dose aspirin reduced the risk of a first heart attack in adults at high cardiovascular risk."),
        (102, "Aspirin use in children", "Aspirin is avoided in children because of the risk of Reye syndrome."),
        (103, "How statins lower cholesterol",
         "Statins inhibit HMG-CoA reductase in the liver and lower LDL cholesterol in the blood."),
        (104, "Readmission after heart failure", "Hospital readmission within 30 days of heart failure was common."),
        (105, "Kidney function over time", "Renal function declined slowly over five years in older adults.")]
QUESTIONS = [{"info_need_id": "S1", "info_need": "Does aspirin prevent heart attacks?"},
             {"info_need_id": "S2", "info_need": "How do statins lower cholesterol?"}]
WANT_TOP = {"S1": 101, "S2": 103}
FIXTURE = '''import os, shutil, sqlite3, sys
sys.path.insert(0, "/app")
import build_index
DOCS = %r
tmp = "/tmp/fx.db"
con = build_index.open_db(tmp, "full")
with con:
    for pmid, title, abstract in DOCS:
        con.execute("INSERT INTO docs(rowid, title, abstract, mesh) VALUES (?,?,?,?)", (pmid, title, abstract, ""))
        con.execute("INSERT INTO meta VALUES (?,?,?,?,?)", (pmid, 2020, "J", None, "spark49-fixture"))
con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
con.close()
os.makedirs("/fx/index", exist_ok=True)
shutil.copyfile(tmp, "/fx/index/spark_full.db")
print(sorted(os.listdir("/fx/index")), sqlite3.sqlite_version)
''' % (DOCS,)
VERSIONS = ("import json, sys, sqlite3, numpy, torch, transformers; print(json.dumps({'python': sys.version.split()[0], "
            "'sqlite': sqlite3.sqlite_version, 'numpy': numpy.__version__, 'torch': torch.__version__, "
            "'transformers': transformers.__version__}))")
NET = ("import json, socket\nr = {}\ntry:\n    socket.getaddrinfo('pypi.org', 443); r['dns'] = True\n"
       "except OSError as e:\n    r['dns'] = False; r['dns_error'] = repr(e)\ntry:\n"
       "    socket.create_connection(('1.1.1.1', 443), 5).close(); r['connect'] = True\n"
       "except OSError as e:\n    r['connect'] = False; r['connect_error'] = repr(e)\nprint(json.dumps(r))")
WRITE = ("import json\ntry:\n    open('/index/spark49-write-probe.txt', 'w').write('x'); r = {'wrote': True}\n"
         "except OSError as e:\n    r = {'wrote': False, 'errno': e.errno, 'error': repr(e)}\nprint(json.dumps(r))")


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def download(url, path, want):
    """Fetch url to path unless path already has sha256 want; return a record of the file."""
    if os.path.isfile(path) and sha256_file(path) == want:
        return {"bytes": os.path.getsize(path), "sha256": want, "ok": True, "kept": True}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as r, open(path + ".part", "wb") as f:
        shutil.copyfileobj(r, f, 1 << 20)
    os.replace(path + ".part", path)
    got = sha256_file(path)
    return {"bytes": os.path.getsize(path), "sha256": got, "ok": want is None or got == want, "kept": False}


def tail(text, n=25):
    return (text or "").splitlines()[-n:]


def docker(args, timeout):
    """Run one docker command; the record of its exit code, time and output tails."""
    t0 = time.time()
    try:
        p = subprocess.run(["docker"] + args, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout)
        rec = {"exit": p.returncode, "stdout": tail(p.stdout), "stderr": tail(p.stderr)}
    except FileNotFoundError:
        rec = {"exit": None, "error": "docker command not found"}
    except subprocess.TimeoutExpired:
        rec = {"exit": None, "error": "timed out after %d s" % timeout}
    rec["cmd"] = "docker " + " ".join(args)
    rec["seconds"] = round(time.time() - t0, 1)
    return rec


def last_json(rec):
    for line in reversed(rec.get("stdout") or []):
        line = line.strip()
        if line.startswith("{"):
            try:
                return json.loads(line)
            except ValueError:
                return None
    return None


def side_files(index_dir):
    return sorted(os.listdir(index_dir)) if os.path.isdir(index_dir) else None


def main():
    ctx, fx, io, out = (os.path.join(HERE, n) for n in ("ctx", "fx", "io", "out"))
    index_dir = os.path.join(fx, "index")
    rep = {"version": VERSION, "started_utc": now(), "tag": TAG, "steps": {}, "problem": None}

    def finish(problem=None):
        rep["problem"] = problem
        rep["finished_utc"] = now()
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, "report.json"), "w", encoding="utf-8") as f:
            json.dump(rep, f, indent=1)
        print(json.dumps(rep, indent=1))
        return 1 if problem else 0

    s = rep["steps"]
    s["docker_version"] = docker(["version", "--format", "{{.Server.Version}} {{.Server.Os}}"], 60)
    if s["docker_version"]["exit"] != 0:
        return finish("docker is not available")

    files = {}
    try:
        for path, (commit, want) in sorted(CODE.items()):
            files[path] = download(RAW % (commit, path), os.path.join(ctx, *path.split("/")), want)
        files["system/Dockerfile"] = download(RAW % (DOCKERFILE_COMMIT, "system/Dockerfile"),
                                              os.path.join(ctx, "system", "Dockerfile"), None)
        for name, want in sorted(MODEL.items()):
            files["system/model/" + name] = download(HF % name, os.path.join(ctx, "system", "model", name), want)
    except OSError as e:
        rep["files"] = files
        return finish("download failed: %r" % (e,))
    rep["files"] = files
    with open(os.path.join(ctx, "system", "Dockerfile"), encoding="utf-8") as f:
        dockerfile = f.read()
    missing = [m for m in DOCKERFILE_MUST if m not in dockerfile]
    bad = [p for p, r in files.items() if not r["ok"]]
    if bad or missing:
        return finish("files differ from their pins: %s; Dockerfile lacks: %s" % (bad, missing))

    s["build"] = docker(["build", "--progress=plain", "-f", os.path.join(ctx, "system", "Dockerfile"),
                         "-t", TAG, ctx], 3600)
    if s["build"]["exit"] != 0:
        return finish("docker build failed")
    try:
        problem = use_image(rep, fx, io, index_dir)
    except Exception as e:  # report it; the image is still removed below
        problem = "stopped: %r" % (e,)
    s["remove_image"] = docker(["image", "rm", TAG], 300)
    return finish(problem)


def use_image(rep, fx, io, index_dir):
    """Every check on the built image; the problem found, or None."""
    s = rep["steps"]
    s["inspect"] = docker(["image", "inspect", TAG, "--format", "{{.Id}} {{.Size}}"], 60)
    try:
        image_id, size = s["inspect"]["stdout"][-1].split()
        rep["image"] = {"id": image_id, "bytes": int(size), "gb": round(int(size) / 1e9, 2)}
    except (IndexError, ValueError):
        rep["image"] = None

    py = ["run", "--rm", "--network", "none", "--entrypoint", "python"]
    s["versions"] = docker(py + [TAG, "-c", VERSIONS], 300)
    rep["runtime"] = last_json(s["versions"])
    s["net"] = docker(py + [TAG, "-c", NET], 300)
    rep["net"] = last_json(s["net"])

    if os.path.isdir(index_dir):  # a fixture left by an earlier attempt of this script only
        shutil.rmtree(index_dir)
    os.makedirs(fx, exist_ok=True)
    with open(os.path.join(fx, "make_fixture.py"), "w", encoding="utf-8") as f:
        f.write(FIXTURE)
    s["fixture"] = docker(py + ["--mount", "type=bind,source=%s,target=/fx" % fx, TAG, "/fx/make_fixture.py"], 600)
    if s["fixture"]["exit"] != 0 or not os.path.isfile(os.path.join(index_dir, "spark_full.db")):
        return "the test index was not built"
    rep["index_before"] = side_files(index_dir)

    ro = ["--mount", "type=bind,source=%s,target=/index,readonly" % index_dir]
    s["write_probe"] = docker(py + ro + [TAG, "-c", WRITE], 300)
    rep["write_probe"] = last_json(s["write_probe"])

    if os.path.isdir(os.path.join(io, "out")):
        shutil.rmtree(os.path.join(io, "out"))
    os.makedirs(io, exist_ok=True)
    with open(os.path.join(io, "questions.jsonl"), "w", encoding="utf-8") as f:
        for q in QUESTIONS:
            f.write(json.dumps(q) + "\n")
    s["entrypoint"] = docker(["run", "--rm", "--network", "none"] + ro +
                             ["--mount", "type=bind,source=%s,target=/io" % io, TAG,
                              "--questions", "/io/questions.jsonl", "--out-dir", "/io/out", "--team-id", "MV2"], 1800)
    rep["index_after"] = side_files(index_dir)
    run_json = os.path.join(io, "out", "run.json")
    if os.path.isfile(run_json):
        with open(run_json, encoding="utf-8") as f:
            rep["run"] = json.load(f)
    top = {}
    ranked = os.path.join(io, "out", "ranked.jsonl")
    if os.path.isfile(ranked):
        with open(ranked, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    row = json.loads(line)
                    c = row.get("candidates") or []
                    top[str(row.get("info_need_id"))] = [x[0] if isinstance(x, list) else x for x in c[:5]]
    rep["top5"] = top
    rep["top1_as_expected"] = {k: (str(top[k][0]) == str(v) if top.get(k) else None) for k, v in WANT_TOP.items()}
    rep["out_files"] = side_files(os.path.join(io, "out"))
    if s["entrypoint"]["exit"] != 0:
        return "the image's entry point exited %s" % s["entrypoint"]["exit"]
    return None


if __name__ == "__main__":
    sys.exit(main())
