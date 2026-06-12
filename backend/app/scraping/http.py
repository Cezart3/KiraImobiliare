"""Polite HTTP session: browser headers, per-host delay, bounded retries."""
import logging
import time
from urllib.parse import urlsplit

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings

log = logging.getLogger(__name__)

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
HEADERS = {
    "User-Agent": UA,
    "Accept-Language": "ro-RO,ro;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


class PoliteSession:
    def __init__(self, delay_s: float | None = None):
        self.delay = settings.request_delay_s if delay_s is None else delay_s
        self.sess = requests.Session()
        self.sess.headers.update(HEADERS)
        self._last: dict[str, float] = {}

    def _throttle(self, url: str) -> None:
        host = urlsplit(url).netloc
        wait = self.delay - (time.monotonic() - self._last.get(host, 0.0))
        if wait > 0:
            time.sleep(wait)
        self._last[host] = time.monotonic()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1.5, min=2, max=10),
        retry=retry_if_exception_type(requests.RequestException),
        reraise=True,
    )
    def _get(self, url: str, params: dict | None) -> requests.Response:
        return self.sess.get(url, params=params, timeout=settings.request_timeout_s)

    def get_text(self, url: str, params: dict | None = None) -> str | None:
        """GET a page; returns body text or None. Non-200 is NOT retried (no hammering)."""
        self._throttle(url)
        try:
            r = self._get(url, params)
        except requests.RequestException as e:
            log.warning("GET %s failed: %s", url, e)
            return None
        if r.status_code != 200:
            log.warning("GET %s -> HTTP %s", url, r.status_code)
            return None
        return r.text
