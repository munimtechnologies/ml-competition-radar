"""Run the published compose.py unchanged, but open the corpus index read-only and immutable.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

compose.py 0.2.0 (SPARK Task 2) opens the index with a plain sqlite3.connect. The index is in
WAL mode, so a plain open creates -wal and -shm files beside it while it runs; another job
reading the same shared volume with `immutable=1` (spark48 checks that no side file exists)
could see them, and the challenge image will mount the index read-only, where a plain open
fails. This wrapper loads compose.py from --code and swaps the sqlite3 name inside it for an
object whose connect() is ro_db.connect(path, immutable=True) (ro_db.py 0.1.0, which refuses a
non-empty -wal). compose.py's code and outputs are otherwise untouched, so its 0.2.0 results
stay comparable. Standard library only.

  python compose_ro.py --code DIR COMMAND [compose.py arguments]
"""
import os
import sys

VERSION = "0.1.0"


class ReadOnly:
    """Stands in for the sqlite3 module inside compose.py: connect() opens immutable."""

    def __init__(self, ro_db):
        self.ro_db = ro_db

    def connect(self, path):
        return self.ro_db.connect(path, immutable=True)


def load(code):
    """compose module from the folder `code` (which also holds ro_db.py), patched read-only."""
    code = os.path.abspath(code)
    if code not in sys.path:
        sys.path.insert(0, code)
    import compose
    import ro_db
    compose.sqlite3 = ReadOnly(ro_db)
    return compose


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) < 3 or argv[0] != "--code":
        print("usage: compose_ro.py --code DIR COMMAND [arguments]", file=sys.stderr)
        return 2
    return load(argv[1]).main(argv[2:])


if __name__ == "__main__":
    sys.exit(main())
