#!/usr/bin/env bash
# Phase 1: our checker only, written from the text of draft-wright-verdict-record-02.
# The reference checker of the vectors repository is neither read nor run here.
. "$(cd "$(dirname "$0")" && pwd)/common.sh"
record_env environment-ours.txt
SRC=$(checkout "$VECTORS_URL" "$VECTORS_PIN" verdict-record-test-vectors checkout-vectors.txt)
curl -sS -o "$WORK/src/draft-wright-verdict-record-02.txt" "$DRAFT_URL"
{ echo "url: $DRAFT_URL"; echo "sha256: $(shasum -a 256 "$WORK/src/draft-wright-verdict-record-02.txt" | cut -d' ' -f1)"; } > "$HERE/inputs/draft.txt"
( cd "$SRC" && shasum -a 256 [a-h][0-9][0-9]-*.json ) > "$HERE/inputs/vector-files.sha256"
( cd "$HERE/checker" && shasum -a 256 vrc.py run_vectors.py a2_from_text.py ) > "$HERE/inputs/checker-files.sha256"
run_capture ours-a2-from-text.txt "$PY" -I "$HERE/checker/a2_from_text.py" "$WORK/src/draft-wright-verdict-record-02.txt"
run_capture ours-vectors.txt "$PY" -I "$HERE/checker/run_vectors.py" "$SRC" "$HERE/runs/ours-vectors.jsonl"
echo "run_finished_utc: $(date -u +%FT%TZ)" >> "$HERE/runs/environment-ours.txt"
