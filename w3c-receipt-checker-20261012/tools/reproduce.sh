#!/bin/sh
# Rebuild the three corpus copies from the pinned commit and rerun A, B, C.
#   sh tools/reproduce.sh            (from the directory holding tools/)
# Needs: git, uv. Writes runs/, env/, lauf-*.json, lauf-*.stdout.txt.
set -eu
COMMIT=effff90f231d11bb3be93d3d0d0792f36934cc78
REPO=https://github.com/DSHCorrectover/ccs-conformance-vectors
SEED=2

if [ ! -d src/repo/ccs/.git ]; then
  mkdir -p src/repo && git init -q src/repo/ccs
  git -C src/repo/ccs remote add origin "$REPO"
fi
git -C src/repo/ccs fetch -q --depth 1 origin "$COMMIT"
git -C src/repo/ccs -c advice.detachedHead=false checkout -q "$COMMIT"
test "$(git -C src/repo/ccs rev-parse HEAD)" = "$COMMIT"

[ -x env/bin/python ] || uv venv -q --python 3.14 env
uv pip install -q --python env/bin/python \
  cryptography==50.0.2 cffi==2.1.1 pycparser==3.1 jcs==0.2.1

for r in A B C; do
  rm -rf runs/$r && mkdir -p runs/$r
  git -C src/repo/ccs archive "$COMMIT" checkers vectors/v1.4.0-conformance | tar -x -C runs/$r
done

# B: 01-allow signature -> AA==, manifest entry for that one file refreshed
env/bin/python -I - <<'EOF'
import hashlib, json, pathlib
root = pathlib.Path("runs/B/vectors/v1.4.0-conformance")
rp = root / "01-allow/receipt.json"
raw = rp.read_bytes()
new = raw.replace(json.dumps(json.loads(raw)["signature"]).encode(), b'"AA=="', 1)
assert new != raw
rp.write_bytes(new)
m = root / "manifest.json"
k = "01-allow/receipt.json"
m.write_bytes(m.read_bytes().replace(
    json.loads(m.read_bytes())["files"][k].encode(), hashlib.sha256(new).hexdigest().encode(), 1))
EOF

# C: unchanged copy of 01-allow outside the manifest
cp -R runs/C/vectors/v1.4.0-conformance/01-allow \
      runs/C/vectors/v1.4.0-conformance/zz-additional-unlisted-case

for r in A B C; do env/bin/python -I tools/run_one.py runs/$r $r lauf-$r.json $SEED; done
