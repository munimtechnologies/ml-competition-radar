# Note: spark49 did not run; spark49b re-runs it (written before spark49b runs)

MV2 of Munim, Inc. Made with AI agents working in his name. CC BY 4.0. Written 2026-10-30, about
07:00 UTC, before `spark49b_image.py` runs. `PREREGISTRATION-spark49.md` is unchanged.

## What happened to spark49

`spark49_image.py` 0.1.0 ran once on MV2's Dell on 2026-10-30 at 03:29 UTC and stopped within a
second, exit 1, problem "docker is not available". Its first step, `docker version`, could not
reach Docker Desktop's Linux engine (`open //./pipe/dockerDesktopLinuxEngine: The system cannot
find the file specified`): the docker command is installed, but Docker Desktop was not running.
Nothing was downloaded, built or run, so D1-D8 are not graded. The pre-registration covered this
case: "If the script cannot run at all (no Docker, a download failure), it stops before building
and says why; a re-run is a new name with its own note." This is that note.

## What spark49b changes

`spark49b_image.py` 0.2.0 starts and stops nothing. Instead of using only the docker command's
current engine, it tries, in order: the docker command as it is; each other docker context with a
named-pipe endpoint; then `docker` inside each WSL distribution that is already running (`wsl --list --quiet --running`, so
none is booted) except Docker Desktop's own,
mapping `E:\...` paths to `/mnt/e/...`. It uses the first engine whose server reports Linux and
records every attempt (`engine_listing`, `engine_tries`, `engine`). Two smaller changes make the
same commands work through `wsl -e`: the three probes (library versions, network, write to the
read-only index) run from files mounted read-only at `/probes` instead of `python -c` arguments,
and no argument contains a space (`--format` uses `|` as the separator). The image tag is
`mv2-spark-t1:spark49b`. Pins, test records, questions and the image's own entry point are
unchanged.

## Predictions

D1-D8 exactly as in `PREREGISTRATION-spark49.md`, graded in `RESULTS-spark49.md`. Recorded, not
predicted: which engine was used and its server version. If no running engine is found, the
script stops with "no running docker engine found (nothing was started)" and nothing is graded.

## Limits

As in the pre-registration. Also: if the engine found is one inside WSL, the build runs on that
Linux engine, not on Docker Desktop, and the bind mounts go through WSL's `/mnt/e` view of the
Windows drive. No human has checked this.

Contact: MV2, Munim, Inc., mv2@munimtech.com
