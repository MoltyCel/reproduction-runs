#!/usr/bin/env bash
# Run of giskard09/argentum-core examples/conformance/settlement-evidence-ref at 225a617d,
# plus the inline artifact posted in aeoess/agent-governance-vocabulary#177 (comment 6202120269).
# Network: GitHub (clone and the public comment API). No ledger lookup.
. "$(cd "$(dirname "$0")" && pwd)/common.sh"
record_env
SRC=$(checkout https://github.com/giskard09/argentum-core.git 225a617d4b21e47ed4f37d06177275f76dfb7e46 argentum-core)
X=examples/conformance/settlement-evidence-ref
( cd "$SRC" && shasum -a 256 docs/spec/settlement-evidence-ref.md $X/vectors.json $X/verify.py ) > "$HERE/inputs/input-files.sha256"
( cd "$SRC" && git diff --stat "$(git ls-remote origin HEAD | cut -f1)" HEAD -- $X docs/spec/settlement-evidence-ref.md ) > "$HERE/inputs/pin-vs-head-diffstat.txt" 2>&1
# Inline artifact: fetched from the public API, extracted outside the run directory. Its text is not published.
curl -s https://api.github.com/repos/aeoess/agent-governance-vocabulary/issues/comments/6202120269 > "$WORK/comment-6202120269.json"
"$PY" -I - "$WORK/comment-6202120269.json" "$WORK/inline-artifact.json" > "$HERE/inputs/inline-artifact-source.txt" <<'PYEOF'
import hashlib, json, re, sys
c = json.load(open(sys.argv[1], encoding="utf-8"))
body = c["body"].encode("utf-8")
block = re.search(r"```json\n(.*?)```", c["body"], re.S).group(1).encode("utf-8")
open(sys.argv[2], "wb").write(block)
print("source: " + c["html_url"])
print("author: " + c["user"]["login"])
print("created_at: " + c["created_at"] + "  updated_at: " + c["updated_at"])
print("sha256 of the comment body as fetched (UTF-8): " + hashlib.sha256(body).hexdigest())
print("sha256 of the extracted json block as fetched: " + hashlib.sha256(block).hexdigest())
PYEOF
run_capture our-reader.txt "$PY" -I "$HERE/reader/gk_reader.py" "$SRC/$X/vectors.json" "$WORK/inline-artifact.json"
( cd "$SRC/$X" && run_capture project-verify-py.txt "$PY" -I verify.py )
[ -x "$PY39" ] && ( cd "$SRC/$X" && run_capture project-verify-second-python.txt "$PY39" -I verify.py )
echo "run_finished_utc: $(date -u +%FT%TZ)" >> "$HERE/runs/environment.txt"
