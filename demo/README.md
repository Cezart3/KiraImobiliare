# The public demo

`kira-demo.vercel.app` runs the real application against invented data.

## What is real

The FastAPI routes, the SQLAlchemy queries, the filtering and sorting, the
extractors that read heating and parking out of ad text, the geocoding ladder
and the parking-proximity matching — all of it is the code from `backend/`,
unchanged.

## What is not

Every listing. `generate_demo_db.py` composes Romanian ad text from templates,
then runs that text through the app's own extractors and matching service to
build `demo.db`. No listing site is contacted, at build time or at run time, and
no real address, phone number or person appears anywhere in it.

## What the demo cannot do

`RS_DEMO=1` closes the two routes that could reach a third-party site:

- `POST /api/scrape` returns 403. The demo never scrapes.
- `GET /api/img` returns 404. Invented listings carry no photos, and an image
  proxy on a public host is an open door.

Geocoding is answered from `backend/app/data/demo_origins.json` — a small table
of well-known Cluj landmarks — rather than from Nominatim, because a public
instance should not send a shared community service the addresses strangers type
into it. Anything outside that table simply does not resolve.

## Rebuilding the data

```bash
python demo/generate_demo_db.py
```

Deterministic: same seed, same database. Commit the result — the deployment
bundles it and copies it into `/tmp` on cold start, since the serverless
filesystem is read-only everywhere else.

## Why the demo exists at all

Kira is built to run on your own machine, one person for themselves, and its
licence does not permit hosting the real thing publicly — the listings belong to
the sites they came from. The demo exists so the interface can be looked at
without installing anything. For actual listings, run it locally: see the
[Romanian setup guide](../README.ro.md).
