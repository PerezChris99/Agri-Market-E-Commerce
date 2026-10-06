#!/usr/bin/env python3
"""Small dependency-free HTTP concurrency harness for staging smoke/soak tests."""
import argparse
import concurrent.futures
import statistics
import time
import urllib.request


def hit(url, timeout):
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            response.read(4096)
            return response.status, time.perf_counter() - started
    except Exception:
        return 0, time.perf_counter() - started


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--requests", type=int, default=100)
    parser.add_argument("--workers", type=int, default=10)
    parser.add_argument("--timeout", type=float, default=10)
    args = parser.parse_args()
    started = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(lambda _: hit(args.url, args.timeout), range(args.requests)))
    elapsed = time.perf_counter() - started
    latencies = [duration for status, duration in results]
    failures = sum(status < 200 or status >= 500 for status, _ in results)
    print({
        "requests": args.requests,
        "workers": args.workers,
        "elapsed_seconds": round(elapsed, 3),
        "throughput_rps": round(args.requests / elapsed, 2) if elapsed else 0,
        "failures": failures,
        "p50_seconds": round(statistics.median(latencies), 4),
        "max_seconds": round(max(latencies), 4),
    })


if __name__ == "__main__":
    main()
