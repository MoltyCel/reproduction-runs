# Shared helpers for this run. Sourced by run-ours.sh and run-reference.sh.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
WORK=${WORK:-$HERE/../_work}
PY=${PY:-python3.12}
VECTORS_URL=https://github.com/diggertydog/verdict-record-test-vectors.git
VECTORS_PIN=d302e24d2114f0a397496cdec37e9fac8a14816d
DRAFT_URL=https://www.ietf.org/archive/id/draft-wright-verdict-record-02.txt
mkdir -p "$WORK/src" "$HERE/inputs" "$HERE/runs"

record_env() { # outfile
  {
    echo "run_started_utc: $(date -u +%FT%TZ)"
    echo "os: $(uname -srm)"
    command -v sw_vers >/dev/null && echo "macos: $(sw_vers -productVersion)"
    echo "python: $($PY --version 2>&1)"
    echo "git: $(git --version)"
  } > "$HERE/runs/$1"
}

checkout() { # url pin name recordfile
  local url=$1 pin=$2 name=$3 rec=$4 d="$WORK/src/$3"
  [ -d "$d/.git" ] || git clone -q "$url" "$d"
  git -C "$d" fetch -q origin
  git -C "$d" -c advice.detachedHead=false checkout -q "$pin"
  {
    echo "repository: $url"
    echo "pin: $pin"
    echo "resolved_commit: $(git -C "$d" rev-parse HEAD)"
    echo "tree: $(git -C "$d" rev-parse 'HEAD^{tree}')"
    echo "commit_date: $(git -C "$d" show -s --format=%cI HEAD)"
    echo "default_branch_head_at_run: $(git ls-remote "$url" HEAD | cut -f1)"
  } > "$HERE/inputs/$rec"
  echo "$d"
}

run_capture() { # outfile cmd...
  local out=$1; shift
  ( "$@" ) > "$HERE/runs/$out" 2>&1
  echo "exit=$?" >> "$HERE/runs/$out"
}
