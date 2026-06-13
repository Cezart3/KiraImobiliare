"""Admin endpoints: scrape trigger + operational stats.

Access: allowed when RS_ENABLE_ADMIN_ENDPOINTS=true (dev), or — with it off in
production — when the request carries X-Admin-Token matching RS_ADMIN_TOKEN.
"""
import secrets
import threading
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core import ratelimit
from app.core.cities import load_cities
from app.core.config import settings
from app.db.models import Listing, ParkingMatch, ParkingSpot, ScrapeRun, User, utcnow
from app.worker.jobs import run_scrape_city

router = APIRouter(tags=["admin"])


def _check_admin(request: Request) -> None:
    if settings.enable_admin_endpoints:
        return
    token = request.headers.get("x-admin-token", "")
    if settings.admin_token and secrets.compare_digest(token, settings.admin_token):
        return
    raise HTTPException(status_code=403, detail="Admin endpoints disabled")


class ScrapeRequest(BaseModel):
    city: str
    site: str | None = None
    max_pages: int | None = None


@router.post("/admin/scrape")
def trigger_scrape(req: ScrapeRequest, request: Request):
    _check_admin(request)
    ratelimit.enforce(request, "admin-scrape", 10)
    if req.city not in load_cities():
        raise HTTPException(status_code=404, detail=f"Unknown city: {req.city}")
    t = threading.Thread(
        target=run_scrape_city,
        kwargs={"city_slug": req.city, "only_site": req.site, "max_pages": req.max_pages},
        daemon=True,
        name=f"scrape-{req.city}",
    )
    t.start()
    return {"started": True, "city": req.city, "site": req.site}


def _build_stats(db: Session) -> dict:
    """Operational snapshot. Every metric here answers an actual question; no
    filler. Used by /admin/stats (JSON) and the /admin dashboard."""
    now = utcnow()
    active_cutoff = now - timedelta(days=settings.listing_active_days)
    stale_after_min = settings.source_stale_hours * 60

    # --- per (city, site) freshness + health -------------------------------
    rows = db.execute(
        select(
            Listing.city_slug,
            Listing.site,
            func.count(),
            func.max(Listing.last_seen_at),
        )
        .where(Listing.last_seen_at >= active_cutoff)
        .group_by(Listing.city_slug, Listing.site)
        .order_by(Listing.city_slug, Listing.site)
    ).all()
    sources = []
    for city, site, count, last_seen in rows:
        age_min = round((now - last_seen).total_seconds() / 60)
        status = "ok" if age_min <= stale_after_min else "stale"
        sources.append(
            {
                "city": city,
                "site": site,
                "active": count,
                "age_min": age_min,
                "status": status,
            }
        )

    # --- last scrape run per (city, site/kind) -----------------------------
    recent_runs = db.scalars(
        select(ScrapeRun)
        .where(ScrapeRun.started_at >= now - timedelta(hours=48))
        .order_by(ScrapeRun.started_at.desc())
    ).all()
    last_run_by: dict[tuple[str, str, str], ScrapeRun] = {}
    for r in recent_runs:
        key = (r.city_slug, r.site, r.kind)
        if key not in last_run_by:
            last_run_by[key] = r
    last_runs = [
        {
            "city": r.city_slug,
            "site": r.site,
            "kind": r.kind,
            "status": r.status,
            "found": r.items_found,
            "upserted": r.items_upserted,
            "at": r.started_at.isoformat(),
            "min_ago": round((now - r.started_at).total_seconds() / 60),
            "error": (r.error or "")[:200],
        }
        for r in sorted(last_run_by.values(), key=lambda x: (x.city_slug, x.site, x.kind))
    ]

    runs_24h = dict(
        db.execute(
            select(ScrapeRun.status, func.count())
            .where(ScrapeRun.started_at >= now - timedelta(hours=24))
            .group_by(ScrapeRun.status)
        ).all()
    )
    failures = [
        {
            "city": r.city_slug,
            "site": r.site,
            "kind": r.kind,
            "at": r.started_at.isoformat(),
            "error": (r.error or "")[:200],
        }
        for r in db.scalars(
            select(ScrapeRun)
            .where(
                ScrapeRun.status == "error",
                ScrapeRun.started_at >= now - timedelta(hours=24),
            )
            .order_by(ScrapeRun.started_at.desc())
            .limit(10)
        ).all()
    ]

    # --- overall health verdict (what to look at first) --------------------
    stale_sources = [s for s in sources if s["status"] == "stale"]
    health = (
        "error"
        if runs_24h.get("error")
        else "warn"
        if stale_sources
        else "ok"
    )

    active_by_city = dict(
        db.execute(
            select(Listing.city_slug, func.count())
            .where(Listing.last_seen_at >= active_cutoff)
            .group_by(Listing.city_slug)
        ).all()
    )

    # subscribers = users with live access (date-based, matches has_access)
    subscribers = db.scalar(
        select(func.count())
        .select_from(User)
        .where(User.sub_period_end.is_not(None), User.sub_period_end > now)
    ) or 0

    # data-quality coverage on active listings
    active = db.scalars(select(Listing).where(Listing.last_seen_at >= active_cutoff)).all()
    n = len(active) or 1
    coverage = {
        "with_image_pct": round(100 * sum(1 for x in active if x.images) / n),
        "with_price_pct": round(100 * sum(1 for x in active if x.price_eur) / n),
        "geocoded_pct": round(
            100 * sum(1 for x in active if x.geo_precision not in ("none", None)) / n
        ),
    }

    return {
        "generated_at": now.isoformat(),
        "health": health,
        "stale_sources": stale_sources,
        "listings_active": sum(active_by_city.values()),
        "listings_active_by_city": active_by_city,
        "listings_total": db.scalar(select(func.count()).select_from(Listing)) or 0,
        "parking_spots": db.scalar(select(func.count()).select_from(ParkingSpot)) or 0,
        "parking_matches": db.scalar(select(func.count()).select_from(ParkingMatch)) or 0,
        "users": db.scalar(select(func.count()).select_from(User)) or 0,
        "subscribers": subscribers,
        "coverage": coverage,
        "sources": sources,
        "last_runs": last_runs,
        "scrape_runs_24h": runs_24h,
        "scrape_failures_24h": failures,
    }


@router.get("/admin/stats")
def stats(request: Request, db: Annotated[Session, Depends(get_db)]):
    """Operational metrics (JSON). See /admin for the visual dashboard."""
    _check_admin(request)
    return _build_stats(db)


@router.get("/admin", response_class=HTMLResponse)
def dashboard(request: Request, db: Annotated[Session, Depends(get_db)]):
    """Visual ops dashboard. Same access rules as the JSON stats. The page
    fetches /admin/stats client-side, sending the X-Admin-Token you enter once
    (stored only in this tab's sessionStorage)."""
    _check_admin(request)
    return _DASHBOARD_HTML


_DASHBOARD_HTML = """<!doctype html>
<html lang="ro"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Kira — panou admin</title>
<style>
 :root{color-scheme:dark}
 *{box-sizing:border-box} body{margin:0;font:14px/1.5 system-ui,Segoe UI,Roboto,sans-serif;
   background:#0f172a;color:#e2e8f0;padding:24px}
 h1{font-size:20px;margin:0 0 4px} .muted{color:#94a3b8;font-size:12px}
 .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:18px 0}
 .card{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:14px}
 .card .k{font-size:12px;color:#94a3b8} .card .v{font-size:26px;font-weight:700;margin-top:2px}
 table{width:100%;border-collapse:collapse;margin-top:8px;font-size:13px}
 th,td{text-align:left;padding:7px 10px;border-bottom:1px solid #334155}
 th{color:#94a3b8;font-weight:600}
 .pill{display:inline-block;padding:2px 9px;border-radius:999px;font-size:12px;font-weight:600}
 .ok{background:#064e3b;color:#6ee7b7} .stale,.warn{background:#78350f;color:#fcd34d}
 .error{background:#7f1d1d;color:#fca5a5}
 h2{font-size:15px;margin:24px 0 4px}
 #login{max-width:360px;margin:60px auto;text-align:center}
 input{width:100%;padding:10px;border-radius:8px;border:1px solid #334155;background:#1e293b;color:#e2e8f0}
 button{margin-top:10px;padding:10px 16px;border:0;border-radius:8px;background:#059669;color:#fff;font-weight:600;cursor:pointer}
 .banner{padding:10px 14px;border-radius:10px;font-weight:600;margin-bottom:16px}
</style></head><body>
<div id="login">
  <h1>Kira — panou admin</h1>
  <p class="muted">Introdu X-Admin-Token (sau lasă gol dacă endpoint-urile admin sunt deschise).</p>
  <input id="tok" type="password" placeholder="X-Admin-Token" autofocus>
  <button onclick="start()">Intră</button>
  <p id="err" style="color:#fca5a5"></p>
</div>
<div id="app" style="display:none"></div>
<script>
const $=id=>document.getElementById(id);
function start(){ sessionStorage.kira_admin_tok=$('tok').value; load(); }
function fmt(n){return new Intl.NumberFormat('ro-RO').format(n)}
async function load(){
  const tok=sessionStorage.kira_admin_tok||'';
  let r;
  try{ r=await fetch('/api/admin/stats',{headers:tok?{'X-Admin-Token':tok}:{}});}catch(e){ $('err').textContent='Eroare de rețea'; return;}
  if(!r.ok){ $('err').textContent='Acces respins ('+r.status+')'; return;}
  const d=await r.json();
  $('login').style.display='none'; $('app').style.display='block';
  const hp={ok:'ok',warn:'warn',error:'error'}[d.health]||'warn';
  const hmsg={ok:'Totul funcționează',warn:'Atenție — surse învechite',error:'Eroare — scrape eșuat în 24h'}[d.health];
  const cov=d.coverage;
  $('app').innerHTML=`
  <div class="banner ${hp}">${hmsg}</div>
  <h1>Panou admin <span class="muted">· actualizat ${new Date(d.generated_at).toLocaleString('ro-RO')}</span></h1>
  <div class="grid">
   <div class="card"><div class="k">Anunțuri active</div><div class="v">${fmt(d.listings_active)}</div></div>
   <div class="card"><div class="k">Total anunțuri</div><div class="v">${fmt(d.listings_total)}</div></div>
   <div class="card"><div class="k">Parcări</div><div class="v">${fmt(d.parking_spots)}</div></div>
   <div class="card"><div class="k">Potriviri parcare</div><div class="v">${fmt(d.parking_matches)}</div></div>
   <div class="card"><div class="k">Utilizatori</div><div class="v">${fmt(d.users)}</div></div>
   <div class="card"><div class="k">Abonați activi</div><div class="v">${fmt(d.subscribers)}</div></div>
  </div>
  <div class="grid">
   <div class="card"><div class="k">Cu poză</div><div class="v">${cov.with_image_pct}%</div></div>
   <div class="card"><div class="k">Cu preț</div><div class="v">${cov.with_price_pct}%</div></div>
   <div class="card"><div class="k">Geolocalizate</div><div class="v">${cov.geocoded_pct}%</div></div>
   <div class="card"><div class="k">Scrape 24h</div><div class="v" style="font-size:15px">${Object.entries(d.scrape_runs_24h).map(([k,v])=>k+': '+v).join(' · ')||'—'}</div></div>
  </div>
  <h2>Surse (prospețime)</h2>
  <table><tr><th>Oraș</th><th>Sursă</th><th>Active</th><th>Văzut acum</th><th>Status</th></tr>
   ${d.sources.map(s=>`<tr><td>${s.city}</td><td>${s.site}</td><td>${fmt(s.active)}</td>
     <td>${s.age_min} min în urmă</td><td><span class="pill ${s.status}">${s.status}</span></td></tr>`).join('')}
  </table>
  <h2>Ultimele rulări scrape</h2>
  <table><tr><th>Oraș</th><th>Sursă</th><th>Tip</th><th>Status</th><th>Găsite</th><th>Salvate</th><th>Când</th></tr>
   ${d.last_runs.map(r=>`<tr><td>${r.city}</td><td>${r.site}</td><td>${r.kind}</td>
     <td><span class="pill ${r.status==='ok'?'ok':'error'}">${r.status}</span></td>
     <td>${r.found}</td><td>${r.upserted}</td><td>${r.min_ago} min</td></tr>`).join('')}
  </table>
  ${d.scrape_failures_24h.length?`<h2 style="color:#fca5a5">Erori 24h</h2>
   <table><tr><th>Oraș</th><th>Sursă</th><th>Eroare</th></tr>
   ${d.scrape_failures_24h.map(f=>`<tr><td>${f.city}</td><td>${f.site}</td><td>${f.error}</td></tr>`).join('')}
   </table>`:''}
  <p class="muted" style="margin-top:24px">Reîncarcă pagina pentru date noi.</p>`;
}
if(sessionStorage.kira_admin_tok!==undefined) load();
</script></body></html>"""
