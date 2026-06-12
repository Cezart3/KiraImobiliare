"""Quick load test against a running API (no extra deps, threads + requests).

Usage: python tools/load_test.py [--base http://localhost:8000] [--threads 30]
       [--requests 600]
Simulates the real anonymous browse mix: listings searches across cities with
assorted filters + health pings.
"""
import argparse
import random
import statistics
import sys
import threading
import time

import requests

sys.stdout.reconfigure(encoding="utf-8")

CITIES = ["cluj-napoca", "bucuresti", "iasi", "oradea", "targu-mures", "timisoara"]
FILTERS = [
    {},
    {"heating": "centrala_proprie"},
    {"parking": ["included", "likely_included"]},
    {"parking": "rentable_nearby"},
    {"price_max": 500},
    {"rooms": [1, 2]},
    {"sort": "price_asc"},
    {"q": "balcon"},
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8000")
    ap.add_argument("--threads", type=int, default=30)
    ap.add_argument("--requests", type=int, default=600)
    args = ap.parse_args()

    latencies: list[float] = []
    errors: list[str] = []
    lock = threading.Lock()
    counter = {"n": 0}

    def worker() -> None:
        s = requests.Session()
        while True:
            with lock:
                if counter["n"] >= args.requests:
                    return
                counter["n"] += 1
            params: dict = {"city": random.choice(CITIES), "page_size": 24}
            params.update(random.choice(FILTERS))
            t0 = time.perf_counter()
            try:
                r = s.get(f"{args.base}/api/listings", params=params, timeout=30)
                dt = (time.perf_counter() - t0) * 1000
                with lock:
                    if r.status_code == 200:
                        latencies.append(dt)
                    else:
                        errors.append(f"HTTP {r.status_code}")
            except Exception as e:  # noqa: BLE001
                with lock:
                    errors.append(type(e).__name__)

    t_start = time.perf_counter()
    threads = [threading.Thread(target=worker) for _ in range(args.threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    wall = time.perf_counter() - t_start

    ok = len(latencies)
    latencies.sort()

    def pct(p: float) -> float:
        return latencies[min(ok - 1, int(ok * p))] if ok else 0.0

    print(f"requests: {args.requests}  concurrency: {args.threads}  wall: {wall:.1f}s")
    print(f"ok: {ok}  errors: {len(errors)}  throughput: {ok / wall:.0f} req/s")
    if ok:
        print(
            f"latency ms — mean {statistics.fmean(latencies):.0f}  "
            f"p50 {pct(0.50):.0f}  p95 {pct(0.95):.0f}  p99 {pct(0.99):.0f}  "
            f"max {latencies[-1]:.0f}"
        )
    if errors:
        uniq: dict[str, int] = {}
        for e in errors:
            uniq[e] = uniq.get(e, 0) + 1
        print("errors:", uniq)


if __name__ == "__main__":
    main()
