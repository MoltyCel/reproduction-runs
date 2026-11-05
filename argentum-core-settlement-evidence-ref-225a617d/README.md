# argentum-core-settlement-evidence-ref-225a617d

Run of `giskard09/argentum-core`, `examples/conformance/settlement-evidence-ref`, at
`225a617d4b21e47ed4f37d06177275f76dfb7e46`, plus the inline settlement artifact posted in
aeoess/agent-governance-vocabulary#177, comment 6202120269. Made in the working directory
`/tmp/mt-runs/repro-177/`. Results, deviations and limits are in `run-summary.md`.

## Reproduce

```
WORK=/some/empty/dir PY=python3.12 PY39=/usr/bin/python3 ./run.sh
```

`run.sh` clones the repository, checks out the pin, records digests of every input file it
reads, fetches the comment from the public GitHub API and extracts the JSON block into
`$WORK`, runs our reader, and then runs the project's `verify.py` under each interpreter
given. `PY` must be Python 3.10 or later; `PY39` is optional.

## What is published

`run.sh`, `common.sh`, our reader (`reader/gk_reader.py`, `reader/jcs.py`), the input digests,
the checkout record and the provenance of the inline artifact (`inputs/`), and the run
outputs (`runs/`). The foreign code is not copied. The inline artifact is not copied either.
It is identified by the comment URL and the SHA-256 of the fetched comment body and of the
extracted block.

## Scan

All files in this directory were searched with `/usr/bin/grep -a` for personal name, the
home-directory path prefixes of macOS and Linux, host names and e-mail addresses: 0 files.

## Binary files

None.
