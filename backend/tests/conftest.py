"""Test env setup. Must run before any `app.*` import (config reads env at import)."""
import os
import tempfile

os.environ.setdefault(
    "RS_DATABASE_URL",
    f"sqlite:///{tempfile.gettempdir()}/rentscalper_test_{os.getpid()}.db",
)
os.environ.setdefault("RS_GEOCODE_BUDGET_PER_RUN", "0")  # never hit Nominatim in tests
os.environ.setdefault("RS_PAYWALL_ENABLED", "false")  # gating tested explicitly
os.environ.setdefault("RS_SECRET_KEY", "test-secret-key-0123456789abcdef0123456789")
os.environ.setdefault("RS_GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")
os.environ.setdefault("RS_AUTH_RATE_LIMIT_PER_MIN", "1000")  # limiter tested explicitly
os.environ.setdefault("RS_GLOBAL_RATE_LIMIT_PER_MIN", "100000")
