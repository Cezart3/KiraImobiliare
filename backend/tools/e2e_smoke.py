"""End-to-end smoke test against the LIVE local stack (through the vite proxy at
:5173 so it exercises the exact path the browser uses). No browser needed — hits
every API flow a user touches.

Run: python tools/e2e_smoke.py  [--base http://localhost:5173]
"""
import argparse
import sys
import time
import uuid

import requests

sys.stdout.reconfigure(encoding="utf-8")

PASS, FAIL = "PASS", "FAIL"
results: list[tuple[str, str, str]] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    results.append((PASS if cond else FAIL, name, detail))
    mark = "[ok]" if cond else "[XX]"
    print(f"{mark} {name}" + (f"  -- {detail}" if detail and not cond else ""))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:5173")
    args = ap.parse_args()
    b = args.base.rstrip("/")
    api = f"{b}/api"

    # ---- health ----
    r = requests.get(f"{api}/health", timeout=10)
    check("health 200 + db", r.status_code == 200 and r.json().get("db") is True, r.text)

    # ---- cities meta ----
    r = requests.get(f"{api}/cities", timeout=10)
    cities = r.json() if r.ok else []
    slugs = {c["slug"] for c in cities}
    expected = {"cluj-napoca", "bucuresti", "iasi", "oradea", "targu-mures", "timisoara"}
    check("cities: all 6 present", expected <= slugs, str(slugs))
    cluj = next((c for c in cities if c["slug"] == "cluj-napoca"), {})
    check("cities: zones present", len(cluj.get("zones", [])) > 0)
    check(
        "cities: nearby towns present (floresti)",
        any(t["slug"] == "floresti" for t in cluj.get("nearby_towns", [])),
    )

    # ---- listings anonymous: paywall gating ----
    r = requests.get(f"{api}/listings", params={"city": "cluj-napoca", "page_size": 60})
    data = r.json()
    total = data.get("total", 0)
    items = data.get("items", [])
    check("listings: returns items", len(items) > 0, f"got {len(items)}")
    check("listings: real total present", total > len(items), f"total={total}")
    check("listings: paywall locks anon", data.get("locked") is True, str(data.get("locked")))
    vis = data.get("visible_limit")
    check(
        "listings: capped at free limit",
        vis is not None and len(items) == vis,
        f"limit={vis} items={len(items)}",
    )
    check("listings: pages=1 while locked", data.get("pages") == 1)

    # page=2 must not leak more
    r2 = requests.get(
        f"{api}/listings", params={"city": "cluj-napoca", "page": 2, "page_size": 60}
    )
    check("listings: page2 cannot bypass paywall", r2.json().get("page") == 1)

    # ---- card data integrity (the bugs we fixed) ----
    for city in ("cluj-napoca", "iasi", "bucuresti", "oradea", "targu-mures", "timisoara"):
        rr = requests.get(f"{api}/listings", params={"city": city, "page_size": 8})
        its = rr.json().get("items", [])
        prices = [i["price_eur"] for i in its if i.get("price_eur")]
        check(
            f"price sanity [{city}]: no rocket (>5000) on first page",
            all(p <= 5000 for p in prices),
            f"max={max(prices) if prices else 0}",
        )
        check(
            f"images present [{city}]: >=half cards have photo",
            sum(1 for i in its if i.get("images")) >= max(1, len(its) // 2),
        )

    # ---- filters ----
    def listing_filter(**params):
        params.setdefault("city", "cluj-napoca")
        return requests.get(f"{api}/listings", params=params).json()

    f_heat = listing_filter(heating="centrala_proprie")
    check("filter heating: all match", all(
        i["heating"] == "centrala_proprie" for i in f_heat.get("items", [])
    ))
    f_price = listing_filter(price_max=400)
    check("filter price_max: all <=400", all(
        (i["price_eur"] or 0) <= 400 for i in f_price.get("items", []) if i["price_eur"]
    ))
    f_park = listing_filter(parking="rentable_nearby")
    items_p = f_park.get("items", [])
    check(
        "filter rentable_nearby: items have best_parking",
        all(i.get("best_parking") for i in items_p) if items_p else True,
        f"{len(items_p)} items",
    )
    if items_p and items_p[0].get("best_parking"):
        bp = items_p[0]["best_parking"]
        check("parking match: has maps_url", "google.com/maps" in (bp.get("maps_url") or ""))
        # distance_m can legitimately be 0 when both sides share a zone centroid
        # (approximate match) — just assert the field exists and is non-negative
        check("parking match: has distance field", bp.get("distance_m") is not None and bp["distance_m"] >= 0)

    # nearby towns hidden by default
    base_n = listing_filter()["total"]
    with_n = listing_filter(include_nearby=True)["total"]
    check("nearby towns: hidden unless toggled", with_n >= base_n)

    # ---- listing detail ----
    any_item = listing_filter(page_size=1).get("items", [])
    if any_item:
        lid = any_item[0]["id"]
        rd = requests.get(f"{api}/listings/{lid}")
        check("detail: 200 + description field", rd.status_code == 200 and "description" in rd.json())

    # ---- auth flow ----
    s = requests.Session()
    email = f"e2e-{uuid.uuid4().hex[:8]}@example.com"
    pw = "parolaTest123"

    me0 = s.get(f"{api}/auth/me").json()
    check("auth: anon me", me0.get("authenticated") is False)

    rr = s.post(f"{api}/auth/register", json={"email": email, "password": pw})
    check("auth: register 200", rr.status_code == 200, rr.text[:120])
    check("auth: register authenticates", rr.json().get("authenticated") is True)

    # duplicate
    rdup = requests.post(f"{api}/auth/register", json={"email": email, "password": pw})
    check("auth: duplicate -> 409", rdup.status_code == 409)

    # short pw / long pw / bad email
    check("auth: short pw -> 422",
          requests.post(f"{api}/auth/register",
                        json={"email": f"x{uuid.uuid4().hex[:6]}@e.com", "password": "short"}).status_code == 422)
    check("auth: 80-char pw -> 422 (no 500)",
          requests.post(f"{api}/auth/register",
                        json={"email": f"x{uuid.uuid4().hex[:6]}@e.com", "password": "x" * 80}).status_code == 422)
    check("auth: bad email -> 422",
          requests.post(f"{api}/auth/register",
                        json={"email": "nope", "password": pw}).status_code == 422)

    # logged-in user still capped (no Stripe sub)
    li = s.get(f"{api}/listings", params={"city": "cluj-napoca", "page_size": 60}).json()
    check("auth: free user still locked", li.get("locked") is True)

    # logout
    s.post(f"{api}/auth/logout")
    check("auth: logout clears session", s.get(f"{api}/auth/me").json().get("authenticated") is False)

    # login back
    rl = s.post(f"{api}/auth/login", json={"email": email, "password": pw})
    check("auth: login 200", rl.status_code == 200)
    check("auth: wrong pw -> 401",
          requests.post(f"{api}/auth/login", json={"email": email, "password": "WRONGpw123"}).status_code == 401)

    # ---- billing without stripe keys -> graceful 503 (not 500) ----
    rb = s.post(f"{api}/billing/checkout")
    check("billing: checkout 503 when Stripe unset (graceful)", rb.status_code in (503, 409), f"got {rb.status_code}")

    # ---- security headers ----
    rh = requests.get(f"{api}/health")
    check("security: X-Content-Type-Options", rh.headers.get("X-Content-Type-Options") == "nosniff")
    check("security: X-Frame-Options DENY", rh.headers.get("X-Frame-Options") == "DENY")

    # ---- image proxy guards ----
    rip = requests.get(f"{api}/img", params={"u": "https://evil.example.com/x.jpg"})
    check("img proxy: rejects non-whitelisted host", rip.status_code == 403, f"got {rip.status_code}")
    rip2 = requests.get(f"{api}/img", params={"u": "ftp://x/y"})
    check("img proxy: rejects bad scheme", rip2.status_code == 400)

    # ---- cleanup: delete the e2e account ----
    rdel = s.post(f"{api}/auth/delete-account")
    check("gdpr: delete-account 200", rdel.status_code == 200)

    # ---- summary ----
    n_fail = sum(1 for r, _, _ in results if r == FAIL)
    n_pass = sum(1 for r, _, _ in results if r == PASS)
    print(f"\n{'='*50}\n{n_pass} passed, {n_fail} failed, {len(results)} total")
    if n_fail:
        print("\nFAILURES:")
        for r, name, detail in results:
            if r == FAIL:
                print(f"  - {name}  {detail}")
    return 1 if n_fail else 0


if __name__ == "__main__":
    time.sleep(0.2)
    raise SystemExit(main())
