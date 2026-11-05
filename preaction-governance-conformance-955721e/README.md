# preaction-governance-conformance-955721e

Run of `babyblueviper1/preaction-governance-conformance`,
`examples/resolution-payment-pair-v0`, at `955721e77059a4d51db047ed1b09db4396cf486f`,
made in the working directory `/tmp/mt-runs/repro-177/`. The artifact under test is the
fixture `exhibit-3-nonce-is-decision-ref` (a Base mainnet USDC payment by EIP-3009
`transferWithAuthorization`, tx `0x2afb35e2…c4a7`, block 52345856), handed over in
aeoess/agent-governance-vocabulary#177, comment 6202044334. Results, deviations and limits
are in `run-summary.md`.

## Reproduce

```
WORK=/some/empty/dir PY=python3.12 ./run.sh
```

`run.sh` clones the repository, checks out the pin, records digests of every input file it
reads (`inputs/input-files.sha256`), runs our reader (`reader/`) and then the project's
`check.py`, and writes all outputs to `runs/`. It needs Python 3.10 or later and network
access to GitHub and to `https://mainnet.base.org` for the live re-read.

## What is published

`run.sh`, `common.sh`, our reader (`reader/bb_reader.py`, `reader/jcs.py`), the input
digests and checkout record (`inputs/`), and the run outputs (`runs/`). The foreign code and
fixtures are not copied; they are identified by commit, tree and the SHA-256 of each file read.

## Scan

All files in this directory were searched with `/usr/bin/grep -a` for personal name, the
home-directory path prefixes of macOS and Linux, host names and e-mail addresses: 0 files.

## Binary files

None.
