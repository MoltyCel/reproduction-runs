#!/usr/bin/env python3
"""Independent reader for ogasurfproject-jpg/horizon-shield idp-bind-v0, real-issuers run
google-2026-10-15, at 491eb46e.

Built from idp-bind-v0/SPEC.md (binding, steps 1-4), provenance-v0/VERIFIER.md section 2
(canonical form, did:key, signatures, preimages, timestamps) and task-execution-bind-v0/SPEC.md
(grant/receipt, E1 action match, window). It does not import or read check.mjs, idp_bind.mjs,
demo/reader.py or any other code from the project. Standard library only; Ed25519 (RFC 8032),
RSASSA-PKCS1-v1_5 and base58btc are implemented below. No network, no clock.

Token content is never printed: only digests, lengths and findings.

Usage: python3 -I hs_reader.py <run dir> [<musubi canonical_vectors.json>]
"""
import base64, hashlib, json, os, re, sys

# ---------------- musubi-canonical-v0 ----------------
class Refused(Exception):
    pass


def _cstr(s):
    out = ['"']
    for ch in s:
        c = ord(ch)
        if ch == '"':
            out.append('\\"')
        elif ch == "\\":
            out.append("\\\\")
        elif c == 0x08:
            out.append("\\b")
        elif c == 0x0C:
            out.append("\\f")
        elif c == 0x0A:
            out.append("\\n")
        elif c == 0x0D:
            out.append("\\r")
        elif c == 0x09:
            out.append("\\t")
        elif c < 0x20 or 0xD800 <= c <= 0xDFFF:
            out.append("\\u%04x" % c)
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def canonical(v):
    if v is None:
        return "null"
    if v is True:
        return "true"
    if v is False:
        return "false"
    if isinstance(v, int):
        if abs(v) > 2 ** 53 - 1:
            raise Refused("unsafe_number")
        return str(v)
    if isinstance(v, float):
        if v.is_integer() and abs(v) <= 2 ** 53 - 1:
            return str(int(v))
        raise Refused("non_integer_number")
    if isinstance(v, str):
        return _cstr(v)
    if isinstance(v, list):
        return "[" + ",".join(canonical(x) for x in v) + "]"
    if isinstance(v, dict):
        for k in v:
            if not all(0x20 <= ord(c) <= 0x7E for c in k):
                raise Refused("key_not_printable_ascii")
        return "{" + ",".join(_cstr(k) + ":" + canonical(v[k]) for k in sorted(v)) + "}"
    raise Refused(type(v).__name__)


def cbytes(v):
    return canonical(v).encode("utf-8", "surrogatepass")


def h(v):
    return hashlib.sha256(cbytes(v)).hexdigest()


# ---------------- Ed25519 verify (RFC 8032 section 5.1.7) ----------------
q = 2 ** 255 - 19
L = 2 ** 252 + 27742317777372353535851937790883648493
d = -121665 * pow(121666, q - 2, q) % q
I = pow(2, (q - 1) // 4, q)


def _xrecover(y, sign):
    xx = (y * y - 1) * pow(d * y * y + 1, q - 2, q) % q
    x = pow(xx, (q + 3) // 8, q)
    if (x * x - xx) % q:
        x = x * I % q
    if (x * x - xx) % q:
        return None
    if x == 0 and sign:
        return None
    if x % 2 != sign:
        x = q - x
    return x


def _edadd(P1, P2):
    x1, y1, z1, t1 = P1
    x2, y2, z2, t2 = P2
    a = (y1 - x1) * (y2 - x2) % q
    b = (y1 + x1) * (y2 + x2) % q
    c = t1 * 2 * d * t2 % q
    dd = z1 * 2 * z2 % q
    e, f, g, hh = b - a, dd - c, dd + c, b + a
    return (e * f % q, g * hh % q, f * g % q, e * hh % q)


def _edmul(P1, s):
    Q = (0, 1, 1, 0)
    while s:
        if s & 1:
            Q = _edadd(Q, P1)
        P1 = _edadd(P1, P1)
        s >>= 1
    return Q


def _decode_point(b):
    if len(b) != 32:
        return None
    y = int.from_bytes(b, "little")
    sign = y >> 255
    y &= (1 << 255) - 1
    if y >= q:
        return None
    x = _xrecover(y, sign)
    if x is None:
        return None
    return (x, y, 1, x * y % q)


def _eq(P1, P2):
    return (P1[0] * P2[2] - P2[0] * P1[2]) % q == 0 and (P1[1] * P2[2] - P2[1] * P1[2]) % q == 0


_By = 4 * pow(5, q - 2, q) % q
_B = (_xrecover(_By, 0), _By, 1, _xrecover(_By, 0) * _By % q)


def ed25519_verify(pub, msg, sig):
    if len(sig) != 64:
        return False
    A = _decode_point(pub)
    R = _decode_point(sig[:32])
    if A is None or R is None:
        return False
    s = int.from_bytes(sig[32:], "little")
    if s >= L:
        return False
    k = int.from_bytes(hashlib.sha512(sig[:32] + pub + msg).digest(), "little") % L
    return _eq(_edmul(_B, s), _edadd(R, _edmul(A, k)))


# ---------------- did:key / base58btc ----------------
_ALPH = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def did_key_pub(did):
    if not isinstance(did, str) or not did.startswith("did:key:z"):
        return None
    s = did[len("did:key:z"):]
    n = 0
    for ch in s:
        i = _ALPH.find(ch)
        if i < 0:
            return None
        n = n * 58 + i
    raw = n.to_bytes((n.bit_length() + 7) // 8, "big") if n else b""
    raw = b"\x00" * (len(s) - len(s.lstrip("1"))) + raw
    if len(raw) != 34 or raw[:2] != b"\xed\x01":
        return None
    return raw[2:]


def sig_ok(did, preimage, sig_b64):
    pub = did_key_pub(did)
    if pub is None:
        return False
    try:
        sig = base64.b64decode(sig_b64, validate=True)
    except Exception:
        return False
    return ed25519_verify(pub, cbytes(preimage), sig)


# ---------------- JWT / RS256 ----------------
def b64url(s):
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


_SHA256_DI = bytes.fromhex("3031300d060960864801650304020105000420")


def rs256_verify(n, e, msg, sig):
    k = (n.bit_length() + 7) // 8
    if len(sig) != k:
        return False
    m = pow(int.from_bytes(sig, "big"), e, n).to_bytes(k, "big")
    t = _SHA256_DI + hashlib.sha256(msg).digest()
    return m == b"\x00\x01" + b"\xff" * (k - len(t) - 3) + b"\x00" + t


TS = re.compile(r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(\.\d+)?Z$")


def ts_epoch(s):
    import calendar
    m = TS.match(s) if isinstance(s, str) else None
    if not m:
        return None
    y, mo, dd, hh, mi, ss = (int(x) for x in m.groups()[:6])
    try:
        import datetime
        datetime.datetime(y, mo, dd, hh, mi, ss)
    except ValueError:
        return None
    return calendar.timegm((y, mo, dd, hh, mi, ss)) + (float(m.group(7)) if m.group(7) else 0)


def verify_binding(b, jwks):
    refusals, findings = [], []
    pre = {k: v for k, v in b.items() if k not in ("binding_id", "actor_sig")}
    try:
        if h(pre) != b.get("binding_id"):
            refusals.append("binding_recompute_mismatch")
    except Refused:
        refusals.append("canonical_refused")
    if did_key_pub(b.get("actor_id")) is None:
        refusals.append("actor_id_unresolvable")
    elif not sig_ok(b["actor_id"], pre, b.get("actor_sig", "")):
        refusals.append("actor_sig_invalid")
    tok = b.get("token", "")
    if hashlib.sha256(tok.encode("ascii")).hexdigest() != b.get("token_sha256"):
        refusals.append("token_digest_mismatch")
    parts = tok.split(".")
    try:
        hdr, pl, sig = json.loads(b64url(parts[0])), json.loads(b64url(parts[1])), b64url(parts[2])
        if len(parts) != 3 or base64.urlsafe_b64encode(sig).decode().rstrip("=") != parts[2]:
            raise ValueError
    except Exception:
        return refusals + ["token_malformed"], findings, {}
    idp = b.get("idp", {})
    if hdr.get("alg") != idp.get("alg") or hdr.get("kid") != idp.get("kid"):
        refusals.append("header_mismatch")
    if hdr.get("alg") != "RS256":
        refusals.append("alg_unsupported")
    if pl.get("iss") != idp.get("issuer"):
        refusals.append("issuer_mismatch")
    if pl.get("sub") != idp.get("subject"):
        refusals.append("subject_mismatch")
    aud = pl.get("aud")
    if idp.get("audience") not in (aud if isinstance(aud, list) else [aud]):
        refusals.append("audience_mismatch")
    if not isinstance(pl.get("exp"), int) or isinstance(pl.get("exp"), bool):
        refusals.append("token_without_exp")
    start = pl.get("nbf", pl.get("iat"))
    t = ts_epoch(b.get("bound_at"))
    if not isinstance(start, int) or t is None:
        refusals.append("bad_nbf")
    elif not (start <= t <= pl.get("exp", -1)):
        refusals.append("outside_token_window")
    if "cnf" in pl:
        c = pl["cnf"]
        if not isinstance(c, dict) or b.get("actor_id") not in (c.get("kid"), c.get("did")):
            refusals.append("cnf_mismatch")
        else:
            findings.append("cnf_bound")
    else:
        findings.append("bearer_only")
    doc = jwks.get("document", "")
    if hashlib.sha256(doc.encode("utf-8")).hexdigest() != jwks.get("sha256"):
        refusals.append("jwks_digest_mismatch")
    keys = [k for k in json.loads(doc).get("keys", []) if k.get("kid") == hdr.get("kid")]
    if len(keys) != 1:
        refusals.append("key_not_in_jwks" if not keys else "kid_ambiguous")
    else:
        k = keys[0]
        if k.get("use") not in (None, "sig"):
            refusals.append("key_not_for_signing")
        if k.get("alg") not in (None, hdr.get("alg")):
            refusals.append("key_alg_mismatch")
        if k.get("kty") != "RSA":
            refusals.append("key_type_mismatch")
        else:
            n, e = int.from_bytes(b64url(k["n"]), "big"), int.from_bytes(b64url(k["e"]), "big")
            if not rs256_verify(n, e, (parts[0] + "." + parts[1]).encode("ascii"), sig):
                refusals.append("idp_signature_invalid")
    info = {"actor_id": b.get("actor_id"), "token_sha256": b.get("token_sha256"), "token_len": len(tok),
            "kid": hdr.get("kid"), "window_s": (pl.get("exp", 0) - start) if isinstance(start, int) else None}
    return refusals, findings, info


def verify_grant_receipt(g, r):
    out = {"grant": [], "receipt": [], "pair": []}
    gp = {k: v for k, v in g.items() if k not in ("grant_ref", "caller_sig", "action_binding")}
    if h(gp) != g.get("grant_ref"):
        out["grant"].append("recompute_mismatch")
    if not sig_ok(g.get("caller_id"), gp, g.get("caller_sig", "")):
        out["grant"].append("caller_sig_invalid")
    rp = {k: v for k, v in r.items() if k not in ("receipt_id", "provider_sig", "action_binding")}
    if h(rp) != r.get("receipt_id"):
        out["receipt"].append("recompute_mismatch")
    if not sig_ok(r.get("provider_id"), rp, r.get("provider_sig", "")):
        out["receipt"].append("provider_sig_invalid")
    if r.get("grant_ref") != g.get("grant_ref"):
        out["pair"].append("grant_ref_mismatch")
    if cbytes(g.get("action")) != cbytes(r.get("executed_action")):
        out["pair"].append("action_mismatch")
    if g.get("provider_id") in (None,):
        out["pair"].append("open_grant")
    elif r.get("provider_id") != g.get("provider_id"):
        out["pair"].append("unauthorized_provider")
    te, nb, na = ts_epoch(r.get("executed_at")), g.get("not_before"), g.get("not_after")
    if te is None or (nb is not None and ts_epoch(nb) is None) or (na is not None and ts_epoch(na) is None):
        out["pair"].append("invalid_timestamp")
    elif (nb is not None and te < ts_epoch(nb)) or (na is not None and te > ts_epoch(na)):
        out["pair"].append("outside_window")
    if g.get("task_id") != r.get("task_id"):
        out["pair"].append("task_id_mismatch")
    return out


def run(dirp):
    J = lambda f: json.load(open(os.path.join(dirp, f), encoding="utf-8"))
    ba, bb, jw, bun = J("binding_a.json"), J("binding_b.json"), J("jwks.json"), J("bundle.json")
    res = {}
    for name, b in (("binding_a", ba), ("binding_b", bb)):
        ref, fnd, info = verify_binding(b, jw)
        res[name] = ("accepted" if not ref else "refused", ref, fnd, info)
    gr = verify_grant_receipt(bun["grant"], bun["receipt"])
    keys = {
        "grant.caller_id == binding_a.actor_id": bun["grant"]["caller_id"] == ba["actor_id"],
        "grant.provider_id == binding_b.actor_id": bun["grant"]["provider_id"] == bb["actor_id"],
        "receipt.provider_id == binding_b.actor_id": bun["receipt"]["provider_id"] == bb["actor_id"],
    }
    return res, gr, keys


def main(argv):
    dirp = argv[0]
    ok_all = True
    print("== controls")
    # Positive control: RFC 8032 section 7.1 TEST 1 (empty message) must verify.
    pk = bytes.fromhex("d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a")
    sg = bytes.fromhex("e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b")
    c1 = ed25519_verify(pk, b"", sg)
    c1n = ed25519_verify(pk, b"x", sg)
    print(f"positive control RFC 8032 TEST 1 verifies: {c1}; same signature over another message verifies: {c1n}")
    ok_all &= c1 and not c1n
    if len(argv) > 1:
        cv = json.load(open(argv[1], encoding="utf-8"))["vectors"]
        hits = sum(h(v["value"]) == v["sha256"] and len(cbytes(v["value"])) == v["bytes"] for v in cv)
        print(f"musubi-canonical-v0 vectors reproduced by our canonicalizer: {hits}/{len(cv)}")
        ok_all &= hits == len(cv)
    res, gr, keys = run(dirp)
    print("== google-2026-10-15 (our reader)")
    for name, (verdict, ref, fnd, info) in res.items():
        print(f"{name}: {verdict} refusals={ref or '-'} findings={fnd} token_sha256={info.get('token_sha256')} "
              f"token_len={info.get('token_len')} kid={info.get('kid')} token_window_s={info.get('window_s')}")
    for k in ("grant", "receipt"):
        print(f"{k}: {'accepted' if not gr[k] else 'refused'} refusals={gr[k] or '-'}")
    print(f"pair: {'consistent' if not gr['pair'] else 'refused'} refusals={gr['pair'] or '-'}")
    for k, v in keys.items():
        print(f"keys: {k}: {v}")
    expected = all(res[n][0] == "accepted" and res[n][2] == ["bearer_only"] for n in res) and not gr["grant"] \
        and not gr["receipt"] and not gr["pair"] and all(keys.values())
    print(f"matches the stated expectation: {expected}")
    # Negative controls on copies, so a reader that accepts everything is caught.
    print("== negative controls (altered copies, must be refused)")
    import copy, tempfile
    J = lambda f: json.load(open(os.path.join(dirp, f), encoding="utf-8"))
    ba, jw, bun = J("binding_a.json"), J("jwks.json"), J("bundle.json")
    t = copy.deepcopy(ba); t["token"] = t["token"][:-2] + ("A" if t["token"][-2] != "A" else "B") + t["token"][-1]
    r1 = verify_binding(t, jw)[0]
    t = copy.deepcopy(ba); t["nonce"] = str(t.get("nonce")) + "x"
    r2 = verify_binding(t, jw)[0]
    t = copy.deepcopy(jw); t["sha256"] = "0" * 64
    r3 = verify_binding(ba, t)[0]
    gg = copy.deepcopy(bun["grant"]); gg["action"]["target"] = "/invoices/refund"
    r4 = verify_grant_receipt(gg, bun["receipt"])
    print(f"token signature segment altered -> {r1}")
    print(f"binding nonce altered -> {r2}")
    print(f"jwks digest altered -> {r3}")
    print(f"grant action target altered -> grant {r4['grant']}, pair {r4['pair']}")
    neg_ok = bool(r1) and bool(r2) and bool(r3) and bool(r4["grant"])
    print(f"all negative controls refused: {neg_ok}")
    return 0 if (ok_all and expected and neg_ok) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
