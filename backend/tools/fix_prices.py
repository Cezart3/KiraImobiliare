"""One-off repair after the publi24 price/title bug.

- re-parses price_eur from the stored price_raw with the anchored regex
  ('04 1 500 EUR' -> 1500, '05 250 EUR' -> 250)
- nulls prices above RS_RENT_MAX_EUR that can't be re-parsed
- strips badge counters from publi24 titles ('Promovat 3 24 Apartament...')
- backfills price_negotiable for ALL listings from title+description
"""
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import select  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.textutil import fold  # noqa: E402
from app.db.base import SessionLocal, init_db  # noqa: E402
from app.db.models import Listing  # noqa: E402
from app.scraping.extractors.price import find_price_text, to_eur  # noqa: E402

TITLE_JUNK_RE = re.compile(r"^(?:promovat\s+)?\d+\s+\d+\s+", re.I)
NEGOTIABLE = re.compile(r"\bnegocia")
SALE_AD = re.compile(r"\bde vanzare\b|\bvand\b|\bvindem\b")
PLAUSIBLE_RENT_MAX = 8000  # repair heuristic only; real RO rents top out well below


def reparse(raw_str: str) -> tuple[float, str, str] | None:
    """Parse price from a stored raw string; if the result is implausible for a
    rent, assume a badge counter got glued in front ('14 270 EUR' -> 270) and
    retry without the leading number token."""
    found = find_price_text(raw_str)
    if not found:
        return None
    val = to_eur(found[0], found[1], settings.ron_per_eur)
    if val is not None and val > PLAUSIBLE_RENT_MAX:
        stripped = re.sub(r"^\s*\d{1,3}\s+", "", raw_str.strip())
        f2 = find_price_text(stripped)
        if f2:
            v2 = to_eur(f2[0], f2[1], settings.ron_per_eur)
            if v2 is not None and v2 <= PLAUSIBLE_RENT_MAX:
                return v2, f2[0], f2[1]
        return None
    if val is None:
        return None
    return val, found[0], found[1]


def main() -> None:
    init_db()
    fixed_prices = nulled = fixed_titles = negotiable = deleted = 0
    with SessionLocal() as db:
        for listing in db.scalars(select(Listing)).all():
            if listing.site == "publi24":
                got = reparse(listing.price_raw or "")
                if got is not None:
                    new_price, value, cur = got
                    if listing.price_eur != new_price:
                        print(
                            f"  price {listing.price_eur!s:>10} -> {new_price:>7}  "
                            f"{listing.title[:60]!r}"
                        )
                        listing.price_eur = new_price
                        listing.price_raw = f"{value} {cur}".strip()[:64]
                        fixed_prices += 1
                elif listing.price_eur and listing.price_eur > PLAUSIBLE_RENT_MAX:
                    listing.price_eur = None
                    nulled += 1

                cleaned = TITLE_JUNK_RE.sub("", listing.title or "")
                if cleaned != listing.title:
                    listing.title = cleaned
                    fixed_titles += 1

            else:
                # non-publi24: price_raw is a clean "value currency" string;
                # re-run it through the fixed separator logic ('906.29 EUR'
                # was read as 90629, '1,000' as 1.0)
                new_price = to_eur(listing.price_raw, "", settings.ron_per_eur)
                if (
                    new_price is not None
                    and listing.price_eur is not None
                    and abs(new_price - listing.price_eur) > 0.5
                ):
                    print(
                        f"  price {listing.price_eur!s:>10} -> {new_price:>9}  "
                        f"({listing.site}) {listing.title[:50]!r}"
                    )
                    listing.price_eur = new_price
                    fixed_prices += 1

            # sale ads leaked into the rental feed -> delete
            if SALE_AD.search(fold(listing.title)) or (
                listing.price_eur and listing.price_eur > settings.rent_max_eur
            ):
                print(
                    f"  DELETE sale leak ({listing.site}, {listing.price_eur}) "
                    f"{listing.title[:55]!r}"
                )
                db.delete(listing)
                deleted += 1
                continue

            if not listing.price_negotiable and NEGOTIABLE.search(
                fold(f"{listing.title} {listing.description or ''}")
            ):
                listing.price_negotiable = True
                negotiable += 1
        db.commit()
    print(
        f"\nfixed prices: {fixed_prices}  nulled (unparseable): {nulled}  "
        f"cleaned titles: {fixed_titles}  marked negotiable: {negotiable}  "
        f"deleted sale leaks: {deleted}"
    )


if __name__ == "__main__":
    main()
