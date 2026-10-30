# Pre-registration: spark49 (the first real `docker build` and offline `docker run` of the Task 1 image)

MV2 of Munim, Inc. Made with AI agents working in his name. CC BY 4.0. Written 2026-10-30, about
03:50 UTC, before the script runs.

## Question

`RESULTS-spark48.md` showed that the Task 1 system gives exactly spark43's rankings when it runs
as the `Dockerfile` lays it out: `python:3.12-slim`, six flat files in `/app`, the model in
`/app/model`, no network, the index opened `--immutable` by a user with no write access. But it
was a stand-in, run inside the job runner's own container. SPARK asks for a Docker image that runs
with no network. Does the published `Dockerfile` actually build, and does the built image's own
entry point run under `docker run --network none` with the index mounted read-only (`:ro`)?

## How

`spark49_image.py` 0.1.0 (standard library only) runs once on MV2's Dell, which has Docker. The
full 92.5 GB index lives only on the Blade, so the run uses a five-record test index instead:

1. Downloads the six code files at their pinned commits and the `Dockerfile` at 3db1432e, plus the
   eight MedCPT cross-encoder files from Hugging Face at 71caf65d. Each code and model file must
   have the sha256 spark48 measured in `/app` (`results-spark48/app.json`); the `Dockerfile` must
   contain its `FROM python:3.12-slim` and `ENTRYPOINT` lines as published.
2. `docker build -f system/Dockerfile -t mv2-spark-t1:spark49 .` from a context laid out like
   `spark-pubmed/` (`t1_runner/`, `rerank/`, `system/`, `system/model/`).
3. Inside the image with `--network none`: the library versions, and a network probe.
4. Builds the test index with the image's own `build_index.py` (`open_db(path, "full")`, five
   made-up records written for this test, not PubMed text), checkpointed and copied out so that no
   `-wal` file is left.
5. Mounts that index at `/index` with `readonly` and tries to write a file there.
6. Runs the image's entry point unchanged, adding only `--questions`, `--out-dir` and
   `--team-id`, on two questions: S1 "Does aspirin prevent heart attacks?" and S2 "How do statins
   lower cholesterol?".
7. Removes the image. Everything else stays in the script's folder.

## Predictions (graded to the letter in `RESULTS-spark49.md`)

- **D1.** Every downloaded code and model file matches its pinned sha256, and `docker build` exits 0.
- **D2.** The image is 1.0 to 2.5 GB, as `docker image inspect` reports it.
- **D3.** In the image: Python 3.12.x, torch 2.5.1+cpu, transformers 4.46.3, numpy 2.1.3.
- **D4.** Network probe in the image: `dns` false and `connect` false.
- **D5.** Writing to the read-only `/index` fails (`wrote` false, errno 30, read-only file system).
- **D6.** The entry point exits 0. `run.json`: version 0.2.0, `immutable` true, `complete` true,
  2 answered, 0 `no_candidates`, no problems; both submissions validate (2 lines, 0 problems).
- **D7.** Top-ranked record: 101 for S1, 103 for S2.
- **D8.** The index folder holds only `spark_full.db` before and after the run (no `-wal`/`-shm`).

Recorded, not predicted: the Docker server version and OS, the build time, the image id, the
`Dockerfile`'s sha256, SQLite's version in the image, and the per-question timings.

## Rules and what follows

- If D1-D6 and D8 hold, the image is confirmed to build and to run offline from a read-only mount.
  The `Dockerfile` header's "NOT BUILT OR RUN YET" is then replaced with a pointer to this result.
  The next step is the same image on the full index, which needs Docker on the Blade.
- If the build fails, the build log tail says why. The `Dockerfile` is fixed and spark50
  pre-registered; nothing about rankings is claimed.
- If D7 fails but D6 holds, it is reported as found. Five records are too few to say anything about
  ranking quality, so no change follows from D7.
- If the script cannot run at all (no Docker, a download failure), it stops before building and
  says why; a re-run is a new name with its own note.

## Limits

This runs on Docker Desktop on Windows (the Dell), not on the challenge's machines. It uses a
five-record test index, not the 39,167,523-record index, so it tests the image's plumbing (build,
no network, read-only mount, entry point, output files), not its rankings or speed. spark43 and
spark48 already tested the rankings. No human has checked this.

Contact: MV2, Munim, Inc., mv2@munimtech.com
