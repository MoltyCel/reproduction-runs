#!/usr/bin/env bash
# Phase 2, after phase 1 was committed: the reference checker of the vectors repository at
# the same pin, then our comparison. Our checker is not changed or re-run here.
. "$(cd "$(dirname "$0")" && pwd)/common.sh"
record_env environment-reference.txt
SRC=$(checkout "$VECTORS_URL" "$VECTORS_PIN" verdict-record-test-vectors checkout-vectors-phase2.txt)
( cd "$SRC" && shasum -a 256 vrcheck.py run_all.py held/test_suite.py held/appendix_a2_rule.py held/appendix_a2_hops_parse_only.py held/appendix_a2_hops_signature_required.py ) > "$HERE/inputs/reference-files.sha256"
( cd "$SRC" && run_capture reference-run_all.txt "$PY" -I run_all.py )
( cd "$SRC" && run_capture reference-vrcheck.txt "$PY" -I vrcheck.py $(ls [a-h][0-9][0-9]-*.json) )
( cd "$HERE/checker" && shasum -a 256 compare.py ) > "$HERE/inputs/compare-files.sha256"
run_capture comparison.txt "$PY" -I "$HERE/checker/compare.py" "$SRC" "$HERE/runs/ours-vectors.jsonl" "$HERE/runs/reference-vrcheck.txt" "$HERE/runs/comparison.json"
echo "run_finished_utc: $(date -u +%FT%TZ)" >> "$HERE/runs/environment-reference.txt"
