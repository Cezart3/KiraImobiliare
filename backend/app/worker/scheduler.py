"""Worker entrypoints.

One-shot:   python -m app.worker.scheduler --once [--city X] [--site Y] [--max-pages N]
Scheduler:  python -m app.worker.scheduler          (staggered interval per city)
"""
import argparse
import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.cities import load_cities
from app.core.config import settings
from app.worker.jobs import run_scrape_city


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    ap = argparse.ArgumentParser(description="Kira scraping worker")
    ap.add_argument("--once", action="store_true", help="run a single pass and exit")
    ap.add_argument("--city", help="restrict to one city slug")
    ap.add_argument("--site", help="restrict to one site adapter")
    ap.add_argument("--max-pages", type=int, default=None)
    args = ap.parse_args()

    city_slugs = [args.city] if args.city else list(load_cities())

    if args.once:
        for slug in city_slugs:
            run_scrape_city(slug, only_site=args.site, max_pages=args.max_pages)
        return

    sched = BlockingScheduler(timezone="Europe/Bucharest")
    for i, slug in enumerate(city_slugs):
        sched.add_job(
            run_scrape_city,
            IntervalTrigger(minutes=settings.scrape_interval_min),
            args=[slug],
            kwargs={"only_site": args.site, "max_pages": args.max_pages},
            id=f"scrape-{slug}",
            next_run_time=datetime.now() + timedelta(minutes=2 + i * 7),
            max_instances=1,
            coalesce=True,
        )
    logging.getLogger(__name__).info(
        "scheduler started: %s every %d min", city_slugs, settings.scrape_interval_min
    )
    sched.start()


if __name__ == "__main__":
    main()
