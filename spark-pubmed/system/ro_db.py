"""Open the SPARK corpus index read-only, even when its folder cannot be written.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

The whole-corpus FTS5 index was built in SQLite's WAL journal mode. SQLite (3.22.0 and later)
can read a WAL-mode database without write access only if its -shm and -wal files already
exist, or its folder is writable so they can be created, or the connection uses the
`immutable` URI parameter (sqlite.org/wal.html, section 5). The challenge's no-network Docker
image may mount the corpus read-only, so `connect(path, immutable=True)` opens it with
`mode=ro&immutable=1`: no locks, no -shm or -wal files, no writes. An immutable connection
ignores any -wal file, so a non-empty one is refused here (any pages in it that were never
checkpointed would be skipped without a word); open the database once with write access first.

    python ro_db.py DB        # journal mode, -wal/-shm sizes and SQLite version, as JSON

Python standard library only.
"""
import json
import os
import pathlib
import sqlite3
import sys

VERSION = "0.1.0"
MAGIC = b"SQLite format 3\x00"


def journal_mode(path):
    """'wal' or 'rollback', from header bytes 18-19 (the file format write/read versions)."""
    with open(path, "rb") as f:
        head = f.read(20)
    if len(head) < 20 or head[:16] != MAGIC:
        raise ValueError("not an SQLite database: %s" % path)
    if head[18] == 2 and head[19] == 2:
        return "wal"
    if head[18] == 1 and head[19] == 1:
        return "rollback"
    raise ValueError("unknown file format versions %d/%d: %s" % (head[18], head[19], path))


def side_files(path):
    """Bytes in the -wal and -shm files beside the database (None when a file is absent)."""
    out = {}
    for suffix in ("-wal", "-shm"):
        p = path + suffix
        out[suffix[1:]] = os.path.getsize(p) if os.path.exists(p) else None
    return out


def uri(path, immutable=True):
    """file: URI for a read-only (by default also immutable) connection; the path is %-quoted."""
    u = pathlib.Path(os.path.abspath(path)).as_uri() + "?mode=ro"
    return u + "&immutable=1" if immutable else u


def connect(path, immutable=False):
    """sqlite3 connection; immutable=True opens read-only with no locks and no -shm/-wal files."""
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    if not immutable:
        return sqlite3.connect(path)
    wal = side_files(path)["wal"]
    if wal:
        raise ValueError("%s-wal holds %d bytes that may not be checkpointed; an immutable connection "
                         "would ignore them (open the database once with write access first)" % (path, wal))
    return sqlite3.connect(uri(path), uri=True)


def describe(path):
    """What the Docker image needs to know before mounting the index read-only."""
    return {"version": VERSION, "path": path, "bytes": os.path.getsize(path),
            "journal_mode": journal_mode(path), "side_files": side_files(path),
            "sqlite_version": sqlite3.sqlite_version}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("usage: python ro_db.py DB", file=sys.stderr)
        return 2
    print(json.dumps(describe(argv[0]), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
