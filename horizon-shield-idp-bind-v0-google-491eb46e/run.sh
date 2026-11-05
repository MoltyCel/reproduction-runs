#!/usr/bin/env bash
# Run of ogasurfproject-jpg/horizon-shield workers/hs-ledger/nenrin/idp-bind-v0/real-issuers/google-2026-10-15 at 491eb46e.
# Network: GitHub (clone) only. The runs themselves read no network and no clock.
# The two binding files contain real, expired Google ID tokens; they are read from the checkout and never copied here.
. "$(cd "$(dirname "$0")" && pwd)/common.sh"
PYCRYPTO=${PYCRYPTO:-}   # optional: a Python with the 'cryptography' package for the project's Python reader
record_env
SRC=$(checkout https://github.com/ogasurfproject-jpg/horizon-shield.git 491eb46e44578ea096e61cc7de78a773aa3c7dcc horizon-shield)
N=workers/hs-ledger/nenrin; X=$N/idp-bind-v0; G=$X/real-issuers/google-2026-10-15
( cd "$SRC" && shasum -a 256 $X/SPEC.md $N/provenance-v0/VERIFIER.md $N/task-execution-bind-v0/SPEC.md $N/musubi-v0/canonical_vectors.json \
    $X/real-issuers/check.mjs $X/real-issuers/SHA256SUMS $G/binding_a.json $G/binding_b.json $G/jwks.json $G/bundle.json ) > "$HERE/inputs/input-files.sha256"
( cd "$SRC/$X/real-issuers" && grep google SHA256SUMS | shasum -a 256 -c ) > "$HERE/inputs/sha256sums-check-google.txt" 2>&1
( cd "$SRC" && git diff --stat "$(git ls-remote origin HEAD | cut -f1)" HEAD -- $X ) > "$HERE/inputs/pin-vs-head-diffstat.txt" 2>&1
run_capture our-reader.txt "$PY" -I "$HERE/reader/hs_reader.py" "$SRC/$G" "$SRC/$N/musubi-v0/canonical_vectors.json"
( cd "$SRC/$X" && run_capture project-check-mjs.txt node real-issuers/check.mjs )
if [ -n "$PYCRYPTO" ]; then
  echo "python_with_cryptography: $($PYCRYPTO --version 2>&1), cryptography $($PYCRYPTO -c 'import cryptography;print(cryptography.__version__)')" >> "$HERE/runs/environment.txt"
  ( cd "$SRC/$X/real-issuers" && run_capture project-reader-py.txt "$PYCRYPTO" -I ../demo/reader.py google-2026-10-15 )
fi
# No token content may appear in any output of this directory.
grep -rl 'eyJ' "$HERE/runs" "$HERE/inputs" > "$HERE/runs/token-leak-check.txt"; echo "files containing a JWT prefix: $(grep -c . "$HERE/runs/token-leak-check.txt")" >> "$HERE/runs/token-leak-check.txt"
echo "run_finished_utc: $(date -u +%FT%TZ)" >> "$HERE/runs/environment.txt"
