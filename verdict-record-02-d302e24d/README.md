# verdict-record-02-d302e24d

An independent checker for `draft-wright-verdict-record-02`, run against the published
test vectors `diggertydog/verdict-record-test-vectors` at
`d302e24d2114f0a397496cdec37e9fac8a14816d`, then compared with the reference checker of
that repository at the same commit. Appendix B of the draft asks for a checker written by a
party other than the author; this is one. Made in the working directory
`/tmp/mt-runs/vr-crossrun/`. Results, deviations and limits are in `run-summary.md`.

`run.json` records the run's pins: the draft and the SHA-256 of its fetched bytes, the vectors
commit, `receiver_provenance`, the digest of our checker and the digest of our own policy
for Appendix A.2.

## Order of work

1. Phase 1, commit `64c0c1d997ba85f372c2c653d7247b2791814775` (committed 2026-11-11T17:41:02Z,
   pushed to GitHub 2026-11-11T17:41:04Z): our checker, written from the draft text alone,
   and its result for every case. `PHASE1.md` lists exactly what was read from the vectors
   repository before that commit.
2. Phase 2, the next commit: the reference checker run at the same pin
   (`runs/environment-reference.txt`, last run started 2026-11-11T17:43:40Z), and our comparison.
   Phase 1 files are unchanged by phase 2.

## Reproduce

```
WORK=/some/empty/dir PY=python3.12 ./run-ours.sh        # phase 1
WORK=/some/empty/dir PY=python3.12 ./run-reference.sh   # phase 2
```

Both clone the vectors repository and check out the pin; `run-ours.sh` also fetches the
draft. Python 3.10 or later, standard library only, network access to GitHub and
`www.ietf.org`.

## What is published

`run-ours.sh`, `run-reference.sh`, `common.sh`; our checker and its scripts (`checker/`);
input records (`inputs/`): checkouts, the draft digest, the SHA-256 of each vector file and
of each reference file run; outputs (`runs/`). The vectors and the reference checker are not
copied; they are identified by commit, tree and file digests.

`receiver_provenance`: `clean_room`, in the sense of the CROSSRUN convention: written from
the specification text and the vectors' guide alone (README lines 1-82: file format,
test-only formats and rules), without the source code of the vectors repository.

## Scan

All files in this directory were searched with `/usr/bin/grep -a` for personal name, the
home-directory path prefixes of macOS and Linux, host names and e-mail addresses: 0 files.

## Binary files

None.
