"""Image proxy: listing photos hotlinked via our origin (many CDNs block referers).

Abuse hardening (this is the only endpoint that can generate real egress):
- only hosts declared by registered site adapters are allowed (no open proxy)
- per-IP rate limit on top of the global one
- upstream download is streamed with a hard size cap
- disk cache is LRU-pruned at RS_IMAGE_CACHE_MAX_MB
"""
import hashlib
from pathlib import Path
from typing import Annotated
from urllib.parse import urlsplit

import requests
from fastapi import APIRouter, HTTPException, Query, Request, Response

from app.core import ratelimit
from app.core.config import settings
from app.scraping.base import allowed_image_hosts
from app.scraping.http import UA

router = APIRouter(tags=["images"])

_CT_ALLOWED = {"image/jpeg", "image/png", "image/webp", "image/avif", "image/gif"}
_MAX_BYTES = 8_000_000
_PRUNE_EVERY = 200  # cache-size check frequency (every N writes)
_write_count = 0


def _host_allowed(url: str) -> bool:
    host = urlsplit(url).netloc.lower().split(":")[0]
    return any(host == h or host.endswith("." + h) for h in allowed_image_hosts())


def _fetch_capped(u: str) -> tuple[bytes, str]:
    try:
        r = requests.get(
            u, timeout=10, headers={"User-Agent": UA, "Accept": "image/*"}, stream=True
        )
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail="Upstream fetch failed") from e
    with r:
        # anti-SSRF: a whitelisted CDN must not be able to bounce us elsewhere
        # via redirects — re-check the FINAL url after requests followed them
        if not _host_allowed(str(r.url)):
            raise HTTPException(status_code=403, detail="Redirected off whitelist")
        if r.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Upstream HTTP {r.status_code}")
        ct = (r.headers.get("content-type") or "").split(";")[0].strip().lower()
        if ct not in _CT_ALLOWED:
            raise HTTPException(status_code=415, detail="Not an image")
        declared = r.headers.get("content-length")
        if declared and declared.isdigit() and int(declared) > _MAX_BYTES:
            raise HTTPException(status_code=413, detail="Image too large")
        chunks: list[bytes] = []
        size = 0
        for chunk in r.iter_content(chunk_size=65536):
            size += len(chunk)
            if size > _MAX_BYTES:
                raise HTTPException(status_code=413, detail="Image too large")
            chunks.append(chunk)
    return b"".join(chunks), ct


def _maybe_prune_cache(cache_dir: Path) -> None:
    global _write_count
    _write_count += 1
    if _write_count % _PRUNE_EVERY:
        return
    max_bytes = settings.image_cache_max_mb * 1_000_000
    entries = []
    total = 0
    for p in cache_dir.iterdir():
        if not p.is_file():
            continue
        try:
            st = p.stat()
        except OSError:
            continue
        entries.append((st.st_mtime, st.st_size, p))
        total += st.st_size
    if total <= max_bytes:
        return
    entries.sort()  # oldest first
    for _, sz, p in entries:
        try:
            p.unlink()
        except OSError:
            continue
        total -= sz
        if total <= max_bytes * 0.8:
            break


@router.get("/img")
def image_proxy(u: Annotated[str, Query(max_length=700)], request: Request):
    parts = urlsplit(u)
    if parts.scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail="Invalid URL")
    if not _host_allowed(u):
        raise HTTPException(status_code=403, detail="Host not allowed")

    cache_dir = settings.image_cache_dir
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(u.encode()).hexdigest()
    body_path = cache_dir / key
    ct_path = cache_dir / f"{key}.ct"

    if body_path.exists() and ct_path.exists():
        return Response(
            content=body_path.read_bytes(),
            media_type=ct_path.read_text(encoding="utf-8"),
            headers={
                "Cache-Control": "public, max-age=604800",
                "X-Content-Type-Options": "nosniff",
            },
        )

    # cache miss = upstream egress; rate-limit it per client
    if settings.img_rate_limit_per_min > 0:
        ratelimit.enforce(request, "img", settings.img_rate_limit_per_min)

    content, ct = _fetch_capped(u)
    body_path.write_bytes(content)
    ct_path.write_text(ct, encoding="utf-8")
    _maybe_prune_cache(cache_dir)
    return Response(
        content=content,
        media_type=ct,
        headers={
            "Cache-Control": "public, max-age=604800",
            "X-Content-Type-Options": "nosniff",
        },
    )
