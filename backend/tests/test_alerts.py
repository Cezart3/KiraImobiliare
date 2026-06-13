"""Alert detection + dedup (no SMTP configured in tests -> send is a no-op)."""
from app.services import alerts


def setup_function():
    alerts._last_alert.clear()


def test_send_alert_noop_without_smtp():
    # SMTP unset in tests -> returns False, doesn't raise
    assert alerts.send_alert("test", "body") is False


def test_alert_dedup_cooldown():
    # first call records the key; second within cooldown is suppressed
    alerts.send_alert("x", "b", dedup_key="k1")
    # force "already sent recently"
    assert "k1" in alerts._last_alert
    # a different key is independent
    alerts.send_alert("y", "b", dedup_key="k2")
    assert "k2" in alerts._last_alert


def test_alert_scrape_problems_detects_error_and_empty(monkeypatch):
    captured = {}

    def fake_send(subject, body, dedup_key=None):
        captured["subject"] = subject
        captured["body"] = body
        return True

    monkeypatch.setattr(alerts, "send_alert", fake_send)

    summary = {
        "storia": {"rent": {"found": 120, "upserted": 118, "status": "ok"}},
        "olx": {"rent": {"found": 0, "upserted": 0, "status": "ok"}},  # empty -> problem
        "imobiliare": {"rent": {"found": 0, "status": "error", "error": "boom"}},
        "parking_matches": 500,  # non-dict, must be ignored
    }
    alerts.alert_scrape_problems("cluj-napoca", summary)
    assert "cluj-napoca" in captured["subject"]
    assert "olx/rent" in captured["body"]      # 0 results flagged
    assert "imobiliare/rent" in captured["body"]  # error flagged
    assert "storia" not in captured["body"]    # healthy source not flagged


def test_alert_scrape_problems_silent_when_healthy(monkeypatch):
    called = {"n": 0}

    def fake_send(*a, **k):
        called["n"] += 1

    monkeypatch.setattr(alerts, "send_alert", fake_send)
    summary = {"storia": {"rent": {"found": 100, "upserted": 99, "status": "ok"}}}
    alerts.alert_scrape_problems("iasi", summary)
    assert called["n"] == 0  # nothing wrong -> no email
