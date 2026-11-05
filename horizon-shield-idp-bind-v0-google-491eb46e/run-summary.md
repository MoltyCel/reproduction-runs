# Run summary: idp-bind-v0 real-issuers/google-2026-10-15 at 491eb46e

## Pin

- Pin as given: `491eb46e`. Resolved: `491eb46e44578ea096e61cc7de78a773aa3c7dcc`, tree
  `9c0a5e05fb49c2f7e32fe53342bb36c994442dfc`.
- The default branch had moved to `b75bf4041960d7ee925fe6e953b8418e363d1094` at run time.
  Under `idp-bind-v0`, the head adds five lines to `README.md` and a new file
  `trusted_identity.mjs` (`inputs/pin-vs-head-diffstat.txt`, a diff from head to pin, so
  these show as deletions). No file read by this run differs. The run is at the pin.
- The four Google run files match their entries in `real-issuers/SHA256SUMS`
  (`inputs/sha256sums-check-google.txt`).

## Expected (as stated by the submitter)

Both bindings `accepted` with finding `bearer_only`; grant and receipt `accepted`; the keys
line up: the grant's caller is binding A's actor, and the grant's provider and the receipt's
provider are binding B's actor. No network, no clock.

## Our reader

`reader/hs_reader.py` is built from `idp-bind-v0/SPEC.md` (binding verification, steps 1 to 4),
`provenance-v0/VERIFIER.md` section 2 (canonical form, did:key, signatures, preimages,
timestamps) and `task-execution-bind-v0/SPEC.md` (grant and receipt, action match, window).
It does not import or read `check.mjs`, `idp_bind.mjs`, `demo/reader.py` or any other
project code. It brings its own Ed25519 (RFC 8032), RSASSA-PKCS1-v1_5 with SHA-256,
base58btc and musubi-canonical-v0, and uses no network and no clock.

`runs/our-reader.txt`:

- Controls:
  - RFC 8032 section 7.1 TEST 1 verifies, and the same signature over a different message
    does not.
  - Our canonicalizer reproduces 10/10 of `musubi-v0/canonical_vectors.json`.
- `binding_a`: accepted, no refusal, finding `bearer_only`, `token_sha256`
  `6d7d9debcb293a3bdb75118c69e66614ba6ae1ea6db91f91a2ce7ff299c93c6e`.
- `binding_b`: accepted, no refusal, finding `bearer_only`, `token_sha256`
  `fc7701f74fc6650f9a816a47afc6056a7b9789731ff80fd7492f404c9f45a15f`.
- Both tokens are RS256 under `kid` `943a3a5d7d919625a454e489b75c29adab57acba` in the pinned
  JWKS, with a 3600 s window that contains `bound_at`.
- Grant: accepted. Receipt: accepted.
- Pair: consistent. `grant_ref` matches, the actions are equal, the provider is the
  authorized one, and `executed_at` lies in the grant window.
- Keys: all three equalities hold.
- Result: matches the stated expectation.
- Negative controls on altered copies, all refused:
  - token signature segment changed;
  - binding `nonce` changed;
  - JWKS digest changed;
  - grant action target changed.

## Project's scripts

- `runs/project-check-mjs.txt` (`node real-issuers/check.mjs`, node v25.8.1): exit 0.
  - `google-2026-10-15: established`.
  - Binding A and binding B: `accepted [] ["bearer_only"]`.
  - Grant and receipt: `accepted [] ["evidence_bound_unchecked","no_delegation_observations"]`,
    keys line up.
  - The Entra run reports its two bindings as withheld, and its grant and receipt as accepted.
- `runs/project-reader-py.txt` (`demo/reader.py`, Python 3.12.12, cryptography 50.0.2): the
  same verdicts, exit 0.

Our reader reports no findings for grant and receipt. The project's verifier reports
`evidence_bound_unchecked` and `no_delegation_observations`. Our reader does not implement
the evidence and observation layers of `provenance-v0`, so it has no source for those two
findings. The difference is not a disagreement on any verdict.

## What this run does not establish

- That any payment or invoice action happened. The receipt's `outcome.evidence` was not checked.
- That the subjects are who the issuer says, only that the issuer's key signed tokens naming
  them.
- Possession of the Google identity beyond a bearer token. Neither token carries `cnf`,
  hence `bearer_only`.
- That the pinned JWKS was Google's published key set on 2026-10-15. The run checks the
  pinned bytes against their pinned digest. It does not check them against Google.
- The Entra run. Its bindings are withheld by the publisher and were not checked.
