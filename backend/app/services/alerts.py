"""Email alerts for operational problems (a scraper broke, a source went stale).

SMTP is optional: if not configured, alerts are logged and skipped (no crash).
De-duplicated in-process so the same problem doesn't email every scrape cycle.
"""
import logging
import smtplib
import time
from email.message import EmailMessage

from app.core.config import settings

log = logging.getLogger(__name__)

# remember what we already alerted on, so we don't spam the same issue each run
_ALERT_COOLDOWN_S = 6 * 3600  # re-alert the same key at most every 6h
_last_alert: dict[str, float] = {}


def _smtp_ready() -> bool:
    return bool(settings.alert_email and settings.smtp_host and settings.smtp_user)


def send_alert(subject: str, body: str, dedup_key: str | None = None) -> bool:
    """Send an alert email. Returns True if sent. No-op (logged) if SMTP unset
    or the same dedup_key fired recently."""
    key = dedup_key or subject
    now = time.monotonic()
    last = _last_alert.get(key)
    if last is not None and now - last < _ALERT_COOLDOWN_S:
        return False  # still in cooldown for this issue

    if not _smtp_ready():
        log.warning("ALERT (email not configured): %s — %s", subject, body[:200])
        _last_alert[key] = now
        return False

    msg = EmailMessage()
    msg["Subject"] = f"[Kira] {subject}"
    msg["From"] = settings.smtp_from or settings.smtp_user
    msg["To"] = settings.alert_email
    msg.set_content(body)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as s:
            s.starttls()
            s.login(settings.smtp_user, settings.smtp_password)
            s.send_message(msg)
        _last_alert[key] = now
        log.info("alert sent: %s", subject)
        return True
    except Exception as e:  # never let an alert failure break scraping
        log.error("alert send failed (%s): %s", subject, e)
        return False


def alert_scrape_problems(city_slug: str, summary: dict) -> None:
    """Inspect a scrape summary and email if any source errored or returned
    nothing. Called at the end of each city scrape."""
    problems: list[str] = []
    for site, kinds in summary.items():
        if not isinstance(kinds, dict):
            continue  # skip "parking_matches" int
        for kind, res in kinds.items():
            if not isinstance(res, dict):
                continue
            status = res.get("status")
            found = res.get("found", 0)
            if status == "error":
                problems.append(f"  {site}/{kind}: EROARE — {res.get('error', '')[:160]}")
            elif kind == "rent" and found == 0:
                problems.append(f"  {site}/{kind}: 0 anunțuri găsite (adapter posibil stricat)")

    if not problems:
        return
    body = (
        f"Probleme la scrape pentru orașul: {city_slug}\n\n"
        + "\n".join(problems)
        + "\n\nVerifică /api/admin/stats sau logurile workerului."
    )
    send_alert(
        f"Scrape cu probleme — {city_slug}",
        body,
        dedup_key=f"scrape-problem-{city_slug}",
    )
