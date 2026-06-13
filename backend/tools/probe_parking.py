"""Show how parking is phrased in descriptions vs the stored status."""
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import select  # noqa: E402

from app.core.textutil import fold  # noqa: E402
from app.db.base import SessionLocal  # noqa: E402
from app.db.models import Listing  # noqa: E402

# any sentence fragment mentioning parking/garage
PARK = re.compile(r"[^.]*\b(parcare|garaj|parcari)\b[^.]*", re.I)

with SessionLocal() as db:
    rows = db.scalars(
        select(Listing).where(Listing.parking_status.in_(["area_possible", "likely_included"]))
    ).all()
    print(f"{len(rows)} listings with status area_possible/likely_included\n")
    shown = 0
    for r in rows:
        d = r.description or ""
        if not d:
            continue
        m = PARK.search(fold(d))
        if not m:
            continue
        # map back to original-case snippet roughly
        frag = d[max(0, m.start() - 5) : min(len(d), m.end() + 5)]
        print(f"[{r.site} #{r.id}] {r.parking_status}/{r.parking_confidence}: …{frag.strip()[:130]}…")
        shown += 1
        if shown >= 25:
            break
