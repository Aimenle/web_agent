from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from aimenle import __version__
from aimenle.bot import Bot
from aimenle.config import ConfigError, load_config
from aimenle.fetcher import Fetcher
from aimenle.storage import Store

DEFAULT_DB = "data/aimenle.db"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aimenle", description="Config-driven product data scraper")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("-v", "--verbose", action="store_true", help="show debug output")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="scrape a site described by a YAML config")
    run.add_argument("config", help="path to the site config")
    run.add_argument("--db", default=DEFAULT_DB, help=f"SQLite file (default: {DEFAULT_DB})")
    run.add_argument("--max-pages", type=int, help="override max_pages from the config")
    run.add_argument("--delay", type=float, help="override delay (seconds) from the config")

    export = sub.add_parser("export", help="dump stored products to CSV or JSON")
    export.add_argument("out", help="output file, format is taken from the extension")
    export.add_argument("--db", default=DEFAULT_DB)
    export.add_argument("--source", help="only export one site, by config name")

    return parser


def cmd_run(args) -> int:
    site = load_config(args.config)
    if args.max_pages is not None:
        site.max_pages = args.max_pages
    if args.delay is not None:
        site.delay = args.delay

    fetcher = Fetcher(
        user_agent=site.user_agent,
        delay=site.delay,
        respect_robots=site.respect_robots,
    )
    store = Store(args.db)
    try:
        stored = Bot(site, fetcher, store).run()
        total = store.count(site.name)
    finally:
        store.close()

    print(f"{stored} items processed, {total} total for '{site.name}' in {args.db}")
    return 0


def cmd_export(args) -> int:
    fmt = Path(args.out).suffix.lstrip(".").lower()
    if fmt not in ("csv", "json"):
        print("output file must end in .csv or .json", file=sys.stderr)
        return 2

    store = Store(args.db)
    try:
        count = store.export(args.out, fmt, args.source)
    finally:
        store.close()

    print(f"wrote {count} rows to {args.out}")
    return 0


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
    )
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    try:
        if args.command == "run":
            return cmd_run(args)
        return cmd_export(args)
    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
