"""Re-run the parking classifier over every stored listing's full text and
overwrite the stored status. Use after improving extractors/parking.py.

(Normal upsert keeps the higher-confidence status; this is an intentional
full recompute, so it overwrites unconditionally.)
"""
import sys

sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import select  # noqa: E402

from app.db.base import SessionLocal  # noqa: E402
from app.db.models import Listing  # noqa: E402
from app.scraping.extractors.parking import classify_parking  # noqa: E402

with SessionLocal() as db:
    rows = db.scalars(select(Listing)).all()
    changed: dict[str, int] = {}
    # statuses that may have come from a structured site tag (storia GARAGE) which
    # isn't stored — don't let a text-only recompute erase them to unknown.
    for r in rows:
        full = f"{r.title} {r.description or ''}"
        status, conf = classify_parking(full)
        if status.value == r.parking_status:
            continue
        downgrade_to_unknown = (
            status.value == "unknown" and r.parking_status != "unknown"
        )
        if downgrade_to_unknown:
            continue  # keep the existing (likely tag-derived) status
        key = f"{r.parking_status} -> {status.value}"
        changed[key] = changed.get(key, 0) + 1
        r.parking_status = status.value
        r.parking_confidence = conf
    db.commit()
    total = sum(changed.values())
    print(f"reclassified {total} listings:")
    for k, n in sorted(changed.items(), key=lambda kv: -kv[1]):
        print(f"  {n:4}  {k}")
