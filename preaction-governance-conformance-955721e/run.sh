#!/usr/bin/env bash
# Run of babyblueviper1/preaction-governance-conformance examples/resolution-payment-pair-v0 at 955721e.
# Network: GitHub (clone) and the public Base RPC https://mainnet.base.org (live re-read only).
. "$(cd "$(dirname "$0")" && pwd)/common.sh"
record_env
SRC=$(checkout https://github.com/babyblueviper1/preaction-governance-conformance.git 955721e77059a4d51db047ed1b09db4396cf486f preaction-governance-conformance)
X=examples/resolution-payment-pair-v0
( cd "$SRC" && shasum -a 256 $X/README.md $X/vectors.json $X/fixtures/real.json $X/check.py tools/_rfc8785.py _bip340_nostr.py ) > "$HERE/inputs/input-files.sha256"
( cd "$SRC" && git diff --stat "$(git ls-remote origin HEAD | cut -f1)" HEAD -- $X; echo "(empty above = no change under $X between pin and default-branch head)" ) > "$HERE/inputs/pin-vs-head-diffstat.txt" 2>&1
# Our reader, built from the README; offline over the pinned receipts, then with the live re-read.
run_capture our-reader-pinned.txt "$PY" -I "$HERE/reader/bb_reader.py" "$SRC/$X/vectors.json"
run_capture our-reader-live.txt   "$PY" -I "$HERE/reader/bb_reader.py" "$SRC/$X/vectors.json" --live https://mainnet.base.org
# The project's own checker, run separately.
( cd "$SRC/$X" && run_capture project-check-mutants.txt "$PY" -I check.py --mutants )
( cd "$SRC/$X" && run_capture project-check-live.txt    "$PY" -I check.py --live )
echo "run_finished_utc: $(date -u +%FT%TZ)" >> "$HERE/runs/environment.txt"
