# reproduction-runs

Recorded runs that recompute results published by others. Each directory holds
one run and is fixed by its own tag.

## Procedure

- Foreign code is pinned by commit SHA. The run names the repository, the SHA
  and how the checkout was made.
- Each run records:
  - per-case records, one per case, as the code under test returned them;
  - an own recount from those records, done without importing the code under
    test;
  - a digest of the input bytes;
  - the environment: interpreter, library versions, OS and architecture.
- Printed values and recounted values are kept apart. A summary line printed by
  the code under test is quoted as printed, and the recount is shown next to it.
- Each run states what it does not establish.

## Before publishing a run

1. Exclusions. `.gitignore` keeps out `__pycache__/`, `*.pyc`, `*.pyo`,
   `.DS_Store` and nested `.git/` directories. Compiled artifacts are never
   published; they embed absolute source paths of the machine that built them.
2. Scan. Every file to be published is searched with `/usr/bin/grep -a`
   (binary files included, no shell wrapper) for: the operator's personal name
   in all spellings, the home-directory path prefixes of macOS and Linux, the host names of the machines
   involved, and e-mail addresses. The expected result is zero files. The
   pattern list stays outside the repository, since it contains the terms it
   searches for. The run README states the result as a number.
3. Binary files. Each binary file to be published is listed in the run README
   with the reason it is there.

## Rules

- This repository holds only our own run outputs. It contains no text taken
  from correspondence. Sources from mailing lists or mail are referenced by URL
  and by the SHA-256 of the fetched bytes.
- Published runs are made in a working directory whose absolute path contains
  no user name.
- Run outputs are never edited after the run. A correction is a new run in a
  new directory with a new tag.
- Tags are not moved or deleted.

## Layout

```
<subject>-<revision or date>/
  README.md        what is published, what is not and why, scan result
  run-summary.md   what ran, results, deviations, what the run does not show
  SHA256SUMS       hashes of the files of the run
  ...              records, recount, scripts
```

Check a run with `shasum -a 256 -c SHA256SUMS` inside its directory. Where a
run lists files that are not published, its README names them and gives the
reason.
