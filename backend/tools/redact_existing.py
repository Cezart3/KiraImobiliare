"""One-off: strip phone numbers / emails from already-stored listing + parking
text (GDPR data minimisation, applied retroactively after adding redaction)."""
import sys

sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import select  # noqa: E402

from app.core.textutil import redact_personal  # noqa: E402
from app.db.base import SessionLocal  # noqa: E402
from app.db.models import Listing, ParkingSpot  # noqa: E402

with SessionLocal() as db:
    changed = 0
    for model in (Listing, ParkingSpot):
        for row in db.scalars(select(model)).all():
            new_title = redact_personal(row.title)
            new_desc = redact_personal(row.description)
            if new_title != row.title or new_desc != (row.description or ""):
                row.title = new_title
                row.description = new_desc
                changed += 1
        db.commit()
    print(f"redacted personal data in {changed} rows")
