#!/usr/bin/env python3
"""Independent reader for babyblueviper1/preaction-governance-conformance
examples/resolution-payment-pair-v0 at 955721e.

Built from the README at that commit (edge table, outcome rules) and from the fields the
case files carry. It does not import or read the project's check.py or build.py.
Standard library only; secp256k1/BIP-340 and Keccak-256 are implemented below.

Usage:
  python3 -I bb_reader.py <vectors.json>                 # all cases from pinned bytes
  python3 -I bb_reader.py <vectors.json> --live <rpc>    # also re-read real receipts
"""
import hashlib, json, os, sys, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jcs import jcs_bytes  # our own RFC 8785 implementation

# ---------------- Keccak-256 (FIPS 202 permutation, original Keccak padding) ----------------
_RC = [0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000,
       0x000000000000808B, 0x0000000080000001, 0x8000000080008081, 0x8000000000008009,
       0x000000000000008A, 0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
       0x000000008000808B, 0x800000000000008B, 0x8000000000008089, 0x8000000000008003,
       0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A,
       0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008]
_ROT = [[0, 36, 3, 41, 18], [1, 44, 10, 45, 2], [62, 6, 43, 15, 61], [28, 55, 25, 21, 56], [27, 20, 39, 8, 14]]
_M = (1 << 64) - 1


def _rol(x, n):
    return ((x << n) | (x >> (64 - n))) & _M if n else x


def _f(A):
    for rc in _RC:
        C = [A[x][0] ^ A[x][1] ^ A[x][2] ^ A[x][3] ^ A[x][4] for x in range(5)]
        D = [C[(x - 1) % 5] ^ _rol(C[(x + 1) % 5], 1) for x in range(5)]
        A = [[A[x][y] ^ D[x] for y in range(5)] for x in range(5)]
        B = [[0] * 5 for _ in range(5)]
        for x in range(5):
            for y in range(5):
                B[y][(2 * x + 3 * y) % 5] = _rol(A[x][y], _ROT[x][y])
        A = [[B[x][y] ^ ((~B[(x + 1) % 5][y]) & B[(x + 2) % 5][y]) for y in range(5)] for x in range(5)]
        A[0][0] ^= rc
    return A


def keccak256(data):
    rate = 136
    p = bytearray(data) + b"\x01"
    while len(p) % rate:
        p += b"\x00"
    p[-1] |= 0x80
    A = [[0] * 5 for _ in range(5)]
    for off in range(0, len(p), rate):
        blk = p[off:off + rate]
        for i in range(rate // 8):
            A[i % 5][i // 5] ^= int.from_bytes(blk[8 * i:8 * i + 8], "little")
        A = _f(A)
    out = b"".join(A[i % 5][i // 5].to_bytes(8, "little") for i in range(4))
    return out


TRANSFER = "0x" + keccak256(b"Transfer(address,address,uint256)").hex()
AUTH_USED = "0x" + keccak256(b"AuthorizationUsed(address,bytes32)").hex()

# ---------------- secp256k1 / BIP-340 ----------------
P = 2 ** 256 - 2 ** 32 - 977
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
G = (0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798,
     0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8)


def _add(a, b):
    if a is None:
        return b
    if b is None:
        return a
    if a[0] == b[0] and (a[1] + b[1]) % P == 0:
        return None
    if a == b:
        lam = 3 * a[0] * a[0] * pow(2 * a[1], P - 2, P) % P
    else:
        lam = (b[1] - a[1]) * pow(b[0] - a[0], P - 2, P) % P
    x = (lam * lam - a[0] - b[0]) % P
    return (x, (lam * (a[0] - x) - a[1]) % P)


def _mul(pt, k):
    r = None
    while k:
        if k & 1:
            r = _add(r, pt)
        pt = _add(pt, pt)
        k >>= 1
    return r


def _lift_x(x):
    if x >= P:
        return None
    c = (pow(x, 3, P) + 7) % P
    y = pow(c, (P + 1) // 4, P)
    if y * y % P != c:
        return None
    return (x, y if y % 2 == 0 else P - y)


def _tagged(tag, msg):
    t = hashlib.sha256(tag.encode()).digest()
    return hashlib.sha256(t + t + msg).digest()


def bip340_verify(pub_hex, msg32, sig_hex):
    try:
        pub, sig = bytes.fromhex(pub_hex), bytes.fromhex(sig_hex)
    except ValueError:
        return False
    if len(pub) != 32 or len(sig) != 64 or len(msg32) != 32:
        return False
    Pt = _lift_x(int.from_bytes(pub, "big"))
    r, s = int.from_bytes(sig[:32], "big"), int.from_bytes(sig[32:], "big")
    if Pt is None or r >= P or s >= N:
        return False
    e = int.from_bytes(_tagged("BIP0340/challenge", sig[:32] + pub + msg32), "big") % N
    R = _add(_mul(G, s), _mul(Pt, N - e))
    return R is not None and R[1] % 2 == 0 and R[0] == r


# ---------------- NIP-01 event id ----------------
def _nip01_str(s):
    esc = {"\n": "\\n", '"': '\\"', "\\": "\\\\", "\r": "\\r", "\t": "\\t", "\b": "\\b", "\f": "\\f"}
    return '"' + "".join(esc.get(ch, ch) for ch in s) + '"'


def _nip01(v):
    if isinstance(v, str):
        return _nip01_str(v)
    if isinstance(v, bool) or v is None:
        return json.dumps(v)
    if isinstance(v, int):
        return str(v)
    if isinstance(v, list):
        return "[" + ",".join(_nip01(x) for x in v) + "]"
    raise TypeError(type(v).__name__)


def nip01_id(ev):
    ser = _nip01([0, ev["pubkey"], ev["created_at"], ev["kind"], ev["tags"], ev["content"]])
    return hashlib.sha256(ser.encode("utf-8")).hexdigest()


# ---------------- edges ----------------
def sha256_ref(obj):
    return "sha256:" + hashlib.sha256(jcs_bytes(obj)).hexdigest()


def addr_topic(t):
    return "0x" + t[-40:].lower()


def edge_covers(case, expected_key):
    """README: V verifies (NIP-01 id, BIP-340 signature under the expected key,
    decision_ref recomputes) and binds sha256(JCS(args)); the receipt shows that exact
    transfer, authorized by args.from."""
    why = []
    ev, args, rc = case["verdict_event"], case["args"], case["receipt"]
    if nip01_id(ev) != ev["id"]:
        why.append("nip01_id")
    if ev["pubkey"] != expected_key or not bip340_verify(ev["pubkey"], bytes.fromhex(ev["id"]), ev["sig"]):
        why.append("signature")
    try:
        content = json.loads(ev["content"])
    except ValueError:
        return False, ["content_not_json"], None
    pre = {f: content.get(f) for f in content.get("decision_ref_preimage_fields", [])}
    try:
        if not pre or sha256_ref(pre) != content.get("decision_ref"):
            why.append("decision_ref")
    except ValueError:
        why.append("decision_ref_not_canonicalizable")
    if sha256_ref(args) != content.get("action_binding_args_hash"):
        why.append("args_hash")
    if rc.get("status") != "0x1":
        why.append("receipt_status")
    token = args["token"].lower()
    transfers = [l for l in rc["logs"] if l["address"].lower() == token and l["topics"][0] == TRANSFER]
    exact = [l for l in transfers if addr_topic(l["topics"][1]) == args["from"].lower()
             and addr_topic(l["topics"][2]) == args["to"].lower() and int(l["data"], 16) == int(args["amount_atomic"])]
    if not exact:
        why.append("receipt_transfer")
    used = [l for l in rc["logs"] if l["address"].lower() == token and l["topics"][0] == AUTH_USED
            and addr_topic(l["topics"][1]) == args["from"].lower()]
    if not used:
        why.append("authorized_by_args_from")
    return not why, why, content


def evaluate(case, keys):
    expected_key = keys["synthetic"] if case["class"] == "synthetic" else keys["real"]
    if not case.get("receipt"):
        return "UNRESOLVED", ["evidence_unavailable"], {}
    covers, why, content = edge_covers(case, expected_key)
    dref = (content or {}).get("decision_ref", "")
    token = case["args"]["token"].lower()
    nonces = [l["topics"][2].lower() for l in case["receipt"]["logs"]
              if l["address"].lower() == token and l["topics"][0] == AUTH_USED]
    carried = bool(dref.startswith("sha256:") and ("0x" + dref[7:]).lower() in nonces)
    policy = "proceed_on" in case["args"]
    edges = {"covers": covers, "carried": carried, "policy": policy, "covers_detail": why}
    if covers and carried and policy:
        verdict = (content or {}).get("verdict")
        if verdict in case["args"]["proceed_on"]:
            return "AUTHORIZED", [], edges
        return "UNAUTHORIZED", ["executed_on_verdict_outside_policy"], edges
    reasons = []
    if not covers:
        reasons.append("verdict_does_not_cover_payment")
    if not carried:
        reasons.append("payment_does_not_carry_verdict")
    if not policy:
        reasons.append("execution_policy_not_committed")
    return "UNRESOLVED", reasons, edges


def rpc(url, method, params):
    req = urllib.request.Request(url, data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode(),
                                 headers={"content-type": "application/json", "user-agent": "reproduction-runs/1"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["result"]


def main(argv):
    doc = json.load(open(argv[0], encoding="utf-8"))
    keys = {"real": doc["real_issuer_pubkey"], "synthetic": doc["synthetic_test_pubkey"]}
    print(f"topic Transfer          {TRANSFER}")
    print(f"topic AuthorizationUsed {AUTH_USED}")
    bad, pos_ok = 0, False
    for c in doc["cases"]:
        out, reasons, edges = evaluate(c, keys)
        exp = c["expect"]
        agree = out == exp["outcome"] and sorted(reasons) == sorted(exp.get("reasons", []))
        bad += not agree
        if c["id"] == "s1-approve-carried-policy-permits":
            pos_ok = out == "AUTHORIZED"
        e = {k: edges.get(k) for k in ("covers", "carried", "policy")} if edges else {}
        det = f" covers_failed={edges['covers_detail']}" if edges and edges.get("covers_detail") else ""
        print(f"{'agree   ' if agree else 'DISAGREE'} {c['id']:36} {c['class']:9} expected={exp['outcome']}{exp.get('reasons') or ''} "
              f"got={out}{reasons or ''} edges={e}{det}")
    n = len(doc["cases"])
    print(f"{n - bad}/{n} cases agree on outcome and reasons")
    print(f"positive control s1-approve-carried-policy-permits: {'PASSED' if pos_ok else 'FAILED - run does not count'}")
    rc = 0 if bad == 0 and pos_ok else 1
    if len(argv) > 2 and argv[1] == "--live":
        url = argv[2]
        print(f"== live re-read from {url}")
        for c in doc["cases"]:
            if c["class"] != "real":
                continue
            live = rpc(url, "eth_getTransactionReceipt", [c["tx_hash"]])
            blk = rpc(url, "eth_getBlockByNumber", [live["blockNumber"], False]) if live else None
            pin = c["receipt"]
            same_logs = live is not None and [(l["address"].lower(), [t.lower() for t in l["topics"]], l["data"].lower()) for l in live["logs"]] \
                == [(l["address"].lower(), [t.lower() for t in l["topics"]], l["data"].lower()) for l in pin["logs"]]
            print(f"{c['id']}: receipt {'found' if live else 'NOT FOUND'}; status={live and live['status']} "
                  f"block={live and int(live['blockNumber'], 16)} blockHash_equal_pinned={bool(live) and live['blockHash'] == pin['blockHash']} "
                  f"block_header_hash_equal={bool(blk) and blk['hash'] == pin['blockHash']} timestamp_equal={bool(blk) and blk['timestamp'] == pin['block_timestamp']} "
                  f"logs_equal_pinned={same_logs}")
            if live:
                c2 = dict(c, receipt=dict(pin, logs=live["logs"], status=live["status"]))
                out, reasons, _ = evaluate(c2, keys)
                print(f"  outcome from live logs: {out} {reasons}")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
