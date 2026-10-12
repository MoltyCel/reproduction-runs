# w3c-receipt-checker-20261012

Recomputation of the receipt-checker run described in
public-agent-conformance 2026Oct/0051, against
`DSHCorrectover/ccs-conformance-vectors` at
`effff90f231d11bb3be93d3d0d0792f36934cc78`. Results and findings are in
`run-summary.md`.

`SHA256SUMS` is published unchanged. Its SHA-256 is
`785781ce9159a7a062ca767ffe59dc0ae08e6f9eb4787006c0773c3bfd8db461`.

## Files listed in SHA256SUMS but not published

`shasum -a 256 -c SHA256SUMS` reports 7 files that cannot be read. The other
1568 entries verify.

Four are the fetched sources of the run. Text from correspondence is not
published in this repository:

- `src/mail/0042.html`
- `src/mail/0049.html`
- `src/mail/0051.html`
- `src/mail/receipt-observation.json`

The public archive URLs and the SHA-256 of each are in `run-summary.md`,
section 1.

Three are bytecode files that Python wrote while the checker ran. Compiled
artifacts are not published; these embed the absolute path of the working
directory on the machine that ran the checker:

- `runs/A/checkers/__pycache__/independent_checker.cpython-314.pyc`
- `runs/B/checkers/__pycache__/independent_checker.cpython-314.pyc`
- `runs/C/checkers/__pycache__/independent_checker.cpython-314.pyc`

## Scan

Scan of all 1570 files in this directory with `/usr/bin/grep -a` for personal
name, the home-directory path prefixes of macOS and Linux, host names and e-mail addresses: 0 files.

## Binary files

208 files, all named `signature.sig`, `signature-1.sig` or `signature-2.sig`
under `runs/A`, `runs/B` and `runs/C`, each 64 bytes. They are the raw
signature files of the test vectors, part of the corpus the checker ran on,
and byte-equal to the upstream repository at the pinned commit. The one copy
in `runs/C/.../zz-additional-unlisted-case/` is byte-equal to `01-allow`
(control C in `run-summary.md`). Three further `signature.sig` files are empty
(0 bytes), as upstream.

## Third-party files

`runs/A`, `runs/B` and `runs/C` are the three corpus copies the checker ran
on. They come from the repository above: vector files under CC0 1.0, the
checker under the MIT License (`runs/*/checkers/LICENSE`).
