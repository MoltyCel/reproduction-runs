# Run summary: resolution-payment-pair-v0 at 955721e

## Pin

- Pin as given: `955721e`. Resolved: `955721e77059a4d51db047ed1b09db4396cf486f`, tree
  `97446aa927c931ed97e9d4b6c189c2b1aaac16ab` (`inputs/checkout.txt`).
- The default branch had moved to `cd2c319e22834632da4e55b550f3ff11ca7945f0` at run time.
  No file under `examples/resolution-payment-pair-v0` differs between the two
  (`inputs/pin-vs-head-diffstat.txt` is empty). The run is at the pin.

## Expected (as stated by the submitter)

`exhibit-3-nonce-is-decision-ref`: `UNRESOLVED`, reason `execution_policy_not_committed`.
`covers` and `carried` hold, `policy` is missing.

## Our reader

`reader/bb_reader.py` is built from the README at the pin (edge table and outcome rules) and
the fields of `vectors.json`. It does not import or read `check.py`, `build.py` or the
project's helper modules. It brings its own RFC 8785 canonicalizer, NIP-01 event id, BIP-340
verification over secp256k1 and Keccak-256. The two event topics it derives from Keccak-256
equal the constants used in the receipts.

Exhibit 3, from the pinned bytes (`runs/our-reader-pinned.txt`):
`UNRESOLVED ['execution_policy_not_committed']`, edges covers=True, carried=True,
policy=False. This matches the expected answer.

Exhibit 3, live (`runs/our-reader-live.txt`): the receipt read from `https://mainnet.base.org`
is in block 52345856 with status 0x1. Its block hash, the block header hash, the timestamp
and all logs equal the pinned fixture, and the outcome computed from the live logs is the same.

Positive control: `s1-approve-carried-policy-permits` must be `AUTHORIZED`, and it is.

All ten cases: 7 of 10 agree on outcome and reason list. The outcome agrees in all ten. The
three that differ are `n1-args-amount-altered`, `n2-verdict-content-altered` and
`n4-verdict-signed-by-another-key`. For each, the vectors expect the reasons
`['verdict_does_not_cover_payment']`, and our reader returns
`['verdict_does_not_cover_payment', 'execution_policy_not_committed']`. Our reader follows the
README sentence "Everything else is UNRESOLVED with each missing edge named". These three
cases are altered copies of exhibit 3, which declares no `proceed_on`, so our reader names
the missing policy edge as well. The exit code of our reader is 1 because of these three cases.

## Project's checker

`runs/project-check-mutants.txt` (`check.py --mutants`): 10/10 cases match, 5/5 mutants
killed, exit 0. `runs/project-check-live.txt` (`check.py --live`): both real receipts and
block hashes equal the pinned fixture, 10/10 cases match, exit 0.

When the `covers` edge fails, `check.py` returns `verdict_does_not_cover_payment` alone and
does not evaluate the remaining edges. That is the source of the three reason-list
differences above. The difference is in the reason list only, not in any outcome.

## What this run does not establish

- That the verdict's content is correct. The run checks that the verdict was signed under
  the key named as the real issuer key in `vectors.json`, not who controls that key.
- That the synthetic and negative cases correspond to anything on chain. Only the two real
  receipts were re-read.
- Anything about the live `verify-execution` service named in the README. It was not called.
- That `vectors.json` is generated from `fixtures/real.json` by `build.py`. `build.py` was not
  run. The exhibit-3 entries in both files were compared field by field during preparation
  and are equal, but that comparison is not part of this run's outputs.
- Which reading of the reason list for n1, n2 and n4 the authors intend. The run records
  both readings.
