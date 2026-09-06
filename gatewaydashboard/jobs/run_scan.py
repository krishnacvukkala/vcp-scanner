"""Scheduled full-universe scan -> Supabase.

This is the writer. It runs where time is cheap (GitHub Actions, or your own
machine), does the whole scan properly, and stores the result. The hosted
dashboard never scans the universe itself; it reads what this job wrote.

    python -m gatewaydashboard.jobs.run_scan
    python -m gatewaydashboard.jobs.run_scan --no-fundamentals --limit 20

Exit codes: 0 on success, 1 on failure — so a failed scheduled run shows up as
a failed workflow rather than quietly storing nothing.
"""

from __future__ import annotations

import argparse
import os
import sys
import traceback
from datetime import datetime, timezone

# Allow `python jobs/run_scan.py` as well as `python -m gatewaydashboard.jobs.run_scan`
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config          # noqa: E402
import market_data     # noqa: E402
import scanner         # noqa: E402
import store           # noqa: E402


def _progress(done: int, total: int) -> None:
    print(f"  downloading {done}/{total} symbols", flush=True)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=os.environ.get("SCAN_SOURCE", "manual"),
                        help="who ran this: github-actions, local, manual")
    parser.add_argument("--limit", type=int, default=0,
                        help="scan only the first N symbols (a smoke test)")
    parser.add_argument("--no-fundamentals", action="store_true",
                        help="skip the fundamentals pass")
    parser.add_argument("--prune", type=int, default=60,
                        help="keep only the newest N runs afterwards (0 = keep all)")
    parser.add_argument("--dry-run", action="store_true",
                        help="scan and print a summary, write nothing")
    args = parser.parse_args(argv)

    if not args.dry_run and not store.enabled():
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set.",
              file=sys.stderr)
        print("       Set them as repository secrets (Actions) or in your "
              "shell (local).", file=sys.stderr)
        return 1

    if args.limit:
        config.MAX_TICKERS = args.limit

    started = datetime.now(tz=timezone.utc)
    print(f"Aaroquant scan starting {started.isoformat(timespec='seconds')} "
          f"(source={args.source})", flush=True)

    run_id = None
    if not args.dry_run:
        run_id = store.start_run(started, source=args.source)
        print(f"  run id {run_id}", flush=True)

    try:
        result = scanner.scan(
            force=True,                       # a scheduled run always refetches
            with_fundamentals=not args.no_fundamentals,
            progress=_progress,
        )
    except Exception as exc:                  # noqa: BLE001 — must report, not crash silently
        traceback.print_exc()
        if run_id:
            store.fail_run(run_id, f"{type(exc).__name__}: {exc}")
        return 1

    counts = result.get("counts", {})
    print(f"  scanned {result['scanned']}/{result['universe_size']} in "
          f"{result['elapsed_seconds']}s", flush=True)
    print(f"  verdicts: " + ", ".join(f"{k}={v}" for k, v in counts.items()),
          flush=True)
    if result.get("failures"):
        print(f"  {len(result['failures'])} symbol(s) had no usable data",
              flush=True)

    if args.dry_run:
        print("dry run — nothing written")
        return 0

    try:
        written = store.save_results(run_id, result["results"])
        store.finish_run(run_id, result, source=args.source)
        print(f"  stored {written} result rows", flush=True)
    except store.StoreError as exc:
        print(f"ERROR writing to Supabase: {exc}", file=sys.stderr)
        store.fail_run(run_id, str(exc))
        return 1

    # Cache the chart series for everything worth charting, so opening a chart
    # on the dashboard is a database read rather than a Yahoo round trip.
    chartable = [r for r in result["results"]
                 if r.get("verdict") in ("valid_setup", "watch", "target_hit")]
    cached = 0
    for record in chartable:
        symbol = record.get("symbol")
        try:
            payload = market_data.MarketDataProvider.get_historical_ohlc(
                symbol=symbol,
                exchange=record.get("exchange", "NSE"),
                timeframe="1D",
                country=record.get("country", ""),
                asset_class=record.get("assetClass", "EQUITY"),
            )
            if not (payload or {}).get("candles"):
                continue
            store.put_ohlcv(symbol, payload, timeframe="1D",
                            exchange=record.get("exchange"))
            cached += 1
        except Exception:                     # noqa: BLE001 — a cache miss is not a failure
            continue
    print(f"  cached chart series for {cached}/{len(chartable)} candidates",
          flush=True)

    if args.prune:
        removed = store.prune(args.prune)
        if removed:
            print(f"  pruned {removed} old run(s)", flush=True)

    print("done.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
