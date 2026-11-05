# horizon-shield-idp-bind-v0-google-491eb46e

Run of `ogasurfproject-jpg/horizon-shield`,
`workers/hs-ledger/nenrin/idp-bind-v0/real-issuers/google-2026-10-15`, at
`491eb46e44578ea096e61cc7de78a773aa3c7dcc`, handed over in
aeoess/agent-governance-vocabulary#177, comment 6203988067. Made in the working directory
`/tmp/mt-runs/repro-177/`. Results, deviations and limits are in `run-summary.md`.

## Reproduce

```
WORK=/some/empty/dir PY=python3.12 PYCRYPTO=/path/to/python-with-cryptography ./run.sh
```

`run.sh` clones the repository, checks out the pin, records digests of every input file it
reads, runs our reader, then the project's `node real-issuers/check.mjs` from `idp-bind-v0/`,
and, if `PYCRYPTO` is set, the project's Python reader. Only the clone uses the network.

## What is published

`run.sh`, `common.sh`, our reader (`reader/hs_reader.py`), the input digests and checkout
record (`inputs/`), and the run outputs (`runs/`). The foreign code is not copied. The two
binding files contain real, expired Google ID tokens. They are not copied, and no part of a
token appears in any file here: the run records only file digests, `token_sha256`, token
length, `kid` and findings. `runs/token-leak-check.txt` records a search of all outputs for
a JWT prefix: 0 files.

## Scan

All files in this directory were searched with `/usr/bin/grep -a` for personal name, the
home-directory path prefixes of macOS and Linux, host names and e-mail addresses: 0 files.

## Binary files

None.
