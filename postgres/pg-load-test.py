#!/usr/bin/env python3
"""
pg-load-test.py — Simulate N concurrent PostgreSQL users against the Amadeus travel DB.

Usage:
    python3 pg-load-test.py                          # 50 users, default settings
    python3 pg-load-test.py --users 50               # explicit user count
    python3 pg-load-test.py --users 100 --duration 30
    python3 pg-load-test.py --ramp 10                # ramp up 10 users/sec (default: all at once)
    python3 pg-load-test.py --host <ip> --password <pw>
"""

import argparse
import os
import random
import statistics
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

try:
    import psycopg2
    from psycopg2 import OperationalError, DatabaseError
except ImportError:
    print("ERROR: psycopg2 not installed. Run: pip3 install psycopg2-binary")
    raise SystemExit(1)

# ── Default connection settings ───────────────────────────────────────────────
DEFAULT_HOST     = "ec2-18-205-38-130.compute-1.amazonaws.com"
DEFAULT_PORT     = 5432
DEFAULT_DB       = "amadeus"
DEFAULT_USER     = "amadeus"
DEFAULT_PASSWORD = "amadeus123"

# ── Realistic query workload (mirrors what the agents run) ────────────────────
QUERIES = [
    # FlightSearchAgent — direct flight lookup
    (
        "flight_direct",
        """
        SELECT flight_no, airline, departure_time, duration, num_stops,
               available_seats, total_price_usd
        FROM flight_offers
        WHERE origin_iata = %s AND destination_iata = %s AND cabin = 'ECONOMY'
        ORDER BY total_price_usd ASC LIMIT 10;
        """,
        lambda: random.choice([
            ("SIN", "NRT"), ("SIN", "BKK"), ("SIN", "HKG"), ("LHR", "JFK"),
            ("SYD", "LAX"), ("DXB", "LHR"), ("CDG", "NRT"), ("BOM", "DXB"),
            ("KUL", "CGK"), ("ICN", "PVG"),
        ]),
    ),
    # FlightSearchAgent — IATA code lookup
    (
        "airport_lookup",
        "SELECT iata_code, name, city_name, country_code FROM airports "
        "WHERE city_name ILIKE %s LIMIT 5;",
        lambda: (f"%{random.choice(['Tokyo','London','Paris','Singapore','Dubai','Sydney','Bangkok','Mumbai'])}%",),
    ),
    # HotelSearchAgent — hotel search by city
    (
        "hotel_by_city",
        """
        SELECT hotel_name, star_rating, distance_km, room_type,
               price_per_night, room_description
        FROM hotel_offers
        WHERE city_name ILIKE %s
        ORDER BY star_rating DESC, price_per_night ASC LIMIT 10;
        """,
        lambda: (f"%{random.choice(['Tokyo','Bali','Paris','London','Singapore','Dubai','Bangkok','New York'])}%",),
    ),
    # HotelSearchAgent — budget filter
    (
        "hotel_budget_filter",
        """
        SELECT hotel_name, star_rating, room_type, price_per_night
        FROM hotel_offers
        WHERE city_name ILIKE %s AND price_per_night BETWEEN %s AND %s
        ORDER BY star_rating DESC LIMIT 10;
        """,
        lambda: (
            f"%{random.choice(['Tokyo','Bali','Paris','London','Singapore'])}%",
            random.choice([50, 100, 150]),
            random.choice([200, 300, 500]),
        ),
    ),
    # General — row count (lightweight)
    (
        "count_routes",
        "SELECT COUNT(*) FROM routes;",
        lambda: (),
    ),
    # Connecting flights (heavier join)
    (
        "flight_connecting",
        """
        SELECT f1.flight_no AS leg1, f1.destination_iata AS hub,
               f2.flight_no AS leg2,
               f1.total_price_usd + f2.total_price_usd AS combined_price
        FROM flight_offers f1
        JOIN flight_offers f2 ON f2.origin_iata = f1.destination_iata
        WHERE f1.origin_iata = %s AND f2.destination_iata = %s
          AND f1.cabin = 'ECONOMY' AND f2.cabin = 'ECONOMY'
        ORDER BY combined_price ASC LIMIT 5;
        """,
        lambda: random.choice([
            ("SIN", "CDG"), ("SIN", "JFK"), ("LHR", "SYD"), ("NRT", "LAX"),
        ]),
    ),
]

# ── Per-worker result ─────────────────────────────────────────────────────────
@dataclass
class WorkerResult:
    worker_id:      int
    queries_run:    int = 0
    errors:         int = 0
    connect_ms:     float = 0.0
    query_times_ms: list = field(default_factory=list)
    error_messages: list = field(default_factory=list)
    connected:      bool = False


# ── Worker thread ─────────────────────────────────────────────────────────────
def worker(worker_id: int, args, barrier: threading.Barrier,
           stop_event: threading.Event, results: list):
    result = WorkerResult(worker_id=worker_id)
    results[worker_id] = result   # store reference early so main thread sees live updates
    conn = None

    # ── Connect ──────────────────────────────────────────────────────────────
    t0 = time.perf_counter()
    try:
        conn = psycopg2.connect(
            host=args.host, port=args.port, dbname=args.db,
            user=args.user, password=args.password,
            connect_timeout=10,
            options=f"-c application_name=load_test_worker_{worker_id}",
        )
        conn.autocommit = True
        result.connect_ms = (time.perf_counter() - t0) * 1000
        result.connected = True
    except OperationalError as e:
        result.errors += 1
        result.error_messages.append(f"CONNECT: {e}")
        try:
            barrier.wait(timeout=5)
        except Exception:
            pass
        return

    # ── Wait at the barrier so all workers start querying simultaneously ──────
    try:
        barrier.wait(timeout=30)
    except threading.BrokenBarrierError:
        pass

    # ── Query loop ────────────────────────────────────────────────────────────
    cur = conn.cursor()
    while not stop_event.is_set():
        name, sql, params_fn = random.choice(QUERIES)
        params = params_fn()
        qt0 = time.perf_counter()
        try:
            cur.execute(sql, params if params else None)
            cur.fetchall()
            result.query_times_ms.append((time.perf_counter() - qt0) * 1000)
            result.queries_run += 1
        except (DatabaseError, OperationalError) as e:
            result.errors += 1
            result.error_messages.append(f"QUERY({name}): {str(e)[:80]}")
            try:
                conn.rollback()
            except Exception:
                pass
        # Small think-time between queries (0–200 ms) to mimic real users
        time.sleep(random.uniform(0, 0.2))

    cur.close()
    conn.close()


# ── Pretty printer ────────────────────────────────────────────────────────────
def fmt_ms(ms: float) -> str:
    return f"{ms:.1f} ms"

def percentile(data: list, p: float) -> float:
    if not data:
        return 0.0
    s = sorted(data)
    k = (len(s) - 1) * p / 100
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)

SEP = "─" * 62


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="PostgreSQL concurrent-user load test")
    parser.add_argument("--host",     default=os.environ.get("PG_HOST", DEFAULT_HOST))
    parser.add_argument("--port",     type=int, default=int(os.environ.get("PG_PORT", DEFAULT_PORT)))
    parser.add_argument("--db",       default=os.environ.get("PG_DB",   DEFAULT_DB))
    parser.add_argument("--user",     default=os.environ.get("PG_USER", DEFAULT_USER))
    parser.add_argument("--password", default=os.environ.get("PGPASSWORD", DEFAULT_PASSWORD))
    parser.add_argument("--users",    type=int, default=50, help="Concurrent users to simulate (default 50)")
    parser.add_argument("--duration", type=int, default=20, help="Seconds to run queries after all connected (default 20)")
    parser.add_argument("--ramp",     type=int, default=0,  help="Users to add per second (0 = all at once)")
    args = parser.parse_args()

    print()
    print(SEP)
    print("  PostgreSQL Concurrent-User Load Test")
    print(SEP)
    print(f"  Target    : {args.host}:{args.port}/{args.db}")
    print(f"  Users     : {args.users}")
    print(f"  Duration  : {args.duration}s query phase")
    print(f"  Ramp-up   : {'all at once' if args.ramp == 0 else f'{args.ramp} users/sec'}")
    print(f"  Started   : {datetime.now().strftime('%H:%M:%S')}")
    print(SEP)
    print()

    results:    list[Optional[WorkerResult]] = [None] * args.users
    threads:    list[threading.Thread]       = []
    stop_event  = threading.Event()
    barrier     = threading.Barrier(args.users)

    # ── Spawn workers ─────────────────────────────────────────────────────────
    print(f"  Connecting {args.users} workers...", end="", flush=True)
    t_spawn_start = time.perf_counter()

    for i in range(args.users):
        t = threading.Thread(
            target=worker,
            args=(i, args, barrier, stop_event, results),
            daemon=True,
        )
        threads.append(t)
        t.start()
        if args.ramp > 0:
            time.sleep(1.0 / args.ramp)
            if (i + 1) % 10 == 0:
                print(f" {i+1}", end="", flush=True)

    # Wait for all to reach the barrier (connect phase done)
    print()
    print(f"  Waiting for all workers to connect...", end="", flush=True)

    # Poll until barrier is fully filled or 30s timeout
    deadline = time.perf_counter() + 30
    while time.perf_counter() < deadline:
        connected_so_far = sum(
            1 for r in results if r is not None and r.connected
        )
        failed_so_far = sum(
            1 for r in results if r is not None and not r.connected
        )
        if connected_so_far + failed_so_far >= args.users:
            break
        time.sleep(0.2)

    connect_elapsed = (time.perf_counter() - t_spawn_start) * 1000
    connected_count = sum(1 for t in threads if t.is_alive())
    print(f" done ({connect_elapsed:.0f} ms)")
    print()

    # ── Run query phase ───────────────────────────────────────────────────────
    print(f"  Running query phase for {args.duration}s...")
    t_query_start = time.perf_counter()

    for elapsed in range(args.duration):
        time.sleep(1)
        alive = sum(1 for t in threads if t.is_alive())
        queries_so_far = sum(
            r.queries_run for r in results if r is not None
        )
        errors_so_far  = sum(
            r.errors for r in results if r is not None
        )
        print(f"  [{elapsed+1:3d}s]  workers={alive:3d}  queries={queries_so_far:5d}  errors={errors_so_far}", flush=True)

    stop_event.set()

    # Wait for threads to finish
    for t in threads:
        t.join(timeout=5)

    # ── Collect results ───────────────────────────────────────────────────────
    all_connect_ms   = [r.connect_ms for r in results if r and r.connected]
    all_query_ms     = [q for r in results if r for q in r.query_times_ms]
    total_queries    = sum(r.queries_run for r in results if r)
    total_errors     = sum(r.errors for r in results if r)
    workers_ok       = sum(1 for r in results if r and r.connected)
    workers_failed   = sum(1 for r in results if r and not r.connected)
    all_error_msgs   = [m for r in results if r for m in r.error_messages[:3]]
    elapsed_s        = time.perf_counter() - t_query_start

    # ── Print report ──────────────────────────────────────────────────────────
    print()
    print(SEP)
    print("  RESULTS")
    print(SEP)
    print()

    print("  Connection phase")
    print(f"    Workers requested  : {args.users}")
    print(f"    Connected ok       : {workers_ok}")
    print(f"    Failed to connect  : {workers_failed}")
    if all_connect_ms:
        print(f"    Connect time min   : {fmt_ms(min(all_connect_ms))}")
        print(f"    Connect time avg   : {fmt_ms(statistics.mean(all_connect_ms))}")
        print(f"    Connect time max   : {fmt_ms(max(all_connect_ms))}")
    print()

    print("  Query phase")
    print(f"    Duration           : {elapsed_s:.1f}s")
    print(f"    Total queries      : {total_queries}")
    print(f"    Queries/sec        : {total_queries / elapsed_s:.1f}")
    print(f"    Total errors       : {total_errors}")
    if total_queries > 0:
        error_pct = total_errors / (total_queries + total_errors) * 100
        print(f"    Error rate         : {error_pct:.2f}%")
    print()

    if all_query_ms:
        print("  Query latency (all query types)")
        print(f"    Min                : {fmt_ms(min(all_query_ms))}")
        print(f"    Avg                : {fmt_ms(statistics.mean(all_query_ms))}")
        print(f"    Median (p50)       : {fmt_ms(percentile(all_query_ms, 50))}")
        print(f"    p95                : {fmt_ms(percentile(all_query_ms, 95))}")
        print(f"    p99                : {fmt_ms(percentile(all_query_ms, 99))}")
        print(f"    Max                : {fmt_ms(max(all_query_ms))}")
        print()

    # Per-query-type breakdown
    query_names = list({q[0] for q in QUERIES})
    per_type: dict[str, list] = {n: [] for n in query_names}
    for r in results:
        if not r:
            continue
        # We don't track per-type in the worker, so skip breakdown
    # (Per-type tracking would need a dict in WorkerResult — omitted for simplicity)

    # ── Connection pool assessment ────────────────────────────────────────────
    print("  Assessment")
    if workers_failed == 0:
        print(f"    ✓ All {workers_ok} workers connected successfully")
    else:
        print(f"    ✗ {workers_failed} workers failed to connect (max_connections may be too low)")

    if total_errors == 0:
        print("    ✓ Zero query errors")
    else:
        print(f"    ✗ {total_errors} query errors — see details below")

    if all_query_ms:
        p95 = percentile(all_query_ms, 95)
        if p95 < 500:
            print(f"    ✓ p95 latency {fmt_ms(p95)} — good")
        elif p95 < 2000:
            print(f"    ~ p95 latency {fmt_ms(p95)} — acceptable but consider tuning work_mem / shared_buffers")
        else:
            print(f"    ✗ p95 latency {fmt_ms(p95)} — slow, run pg-check-tune.sh --apply")

    if workers_ok < args.users:
        shortage = args.users - workers_ok
        print(f"    ✗ {shortage} connections refused — increase max_connections above current value")
        print(f"      Run: PG_USER=amadeus PG_DB=amadeus PGPASSWORD=amadeus123 bash pg-check-tune.sh --apply")

    print()

    # Error sample
    if all_error_msgs:
        print("  Error sample (first 5 unique)")
        for msg in list(dict.fromkeys(all_error_msgs))[:5]:
            print(f"    - {msg}")
        print()

    print(SEP)
    print(f"  Finished : {datetime.now().strftime('%H:%M:%S')}")
    print(SEP)
    print()


if __name__ == "__main__":
    main()
