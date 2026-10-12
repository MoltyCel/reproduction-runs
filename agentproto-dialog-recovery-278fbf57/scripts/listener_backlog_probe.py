"""Standalone probe, no repo code imported.

Rebuilds the connection pattern of tests/restart_harness.py (serve():
multiprocessing.connection.Listener on AF_UNIX with authkey and the default
backlog=1, one accept thread that also performs the auth handshake, one handler
thread per connection; clients open one connection per call). Fires K clients
at the same moment, ROUNDS times, and counts client-side connect errors.

usage: listener_backlog_probe.py SOCKDIR ROUNDS K [BACKLOG]
"""
import json
import os
import sys
import threading
from multiprocessing.connection import Client, Listener

sockdir, rounds, k = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
backlog = int(sys.argv[4]) if len(sys.argv) > 4 else None
addr = os.path.join(sockdir, f"s{os.getpid()}")
key = os.urandom(16)
lst = Listener(addr, family="AF_UNIX", authkey=key) if backlog is None else \
    Listener(addr, family="AF_UNIX", authkey=key, backlog=backlog)
stop = threading.Event()


def handle(conn):
    try:
        while True:
            try:
                msg = conn.recv()
            except (EOFError, OSError):
                return
            conn.send({"value": msg})
    finally:
        conn.close()


def accept_loop():
    while not stop.is_set():
        try:
            conn = lst.accept()
        except (OSError, EOFError):
            continue
        threading.Thread(target=handle, args=(conn,), daemon=True).start()


threading.Thread(target=accept_loop, daemon=True).start()
errors = {}
ok = 0
lock = threading.Lock()
for _ in range(rounds):
    barrier = threading.Barrier(k)

    def one():
        global ok
        barrier.wait()
        try:
            with Client(addr, family="AF_UNIX", authkey=key) as c:
                c.send(1)
                c.recv()
            with lock:
                ok += 1
        except Exception as e:  # noqa: BLE001
            with lock:
                errors[type(e).__name__] = errors.get(type(e).__name__, 0) + 1
    ts = [threading.Thread(target=one) for _ in range(k)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
stop.set()
print(json.dumps({"rounds": rounds, "clients_per_round": k, "backlog": backlog or 1,
                  "connections": rounds * k, "ok": ok, "errors": errors,
                  "python": sys.version.split()[0], "platform": sys.platform}))
