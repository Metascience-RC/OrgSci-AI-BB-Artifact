"""Minimal OpenAlex client."""

import os
import time

import httpx

BASE = "https://api.openalex.org"
PER_PAGE = 200
_http = httpx.Client(timeout=120, follow_redirects=True)


def short_id(url):
    return url.rsplit("/", 1)[-1] if url else None


def get(path, params):
    key = os.environ.get("OPENALEX_API_KEY")
    params = {**params, **({"api_key": key} if key else {})}
    for attempt in range(8):
        r = _http.get(BASE + path, params=params)
        if r.status_code == 404:
            return None
        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(float(r.headers.get("retry-after") or min(60, 2 ** attempt)))
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError(f"OpenAlex request failed: {path}")


def works(ids, select):
    """Records by ID, keyed by the requested ID. Merged IDs are resolved via the singleton endpoint."""
    ids = list(dict.fromkeys(ids))
    out = {}
    for k in range(0, len(ids), 100):
        chunk = ids[k:k + 100]
        body = get("/works", {"filter": "openalex_id:" + "|".join(chunk), "select": select, "per_page": 100})
        got = {short_id(w["id"]): w for w in body["results"]}
        for i in chunk:
            out[i] = got[i] if i in got else get(f"/works/{i}", {"select": select})
    return out


def abstract(inverted_index):
    if not inverted_index:
        return None
    pos = {i: w for w, idxs in inverted_index.items() for i in idxs}
    return " ".join(pos[i] for i in sorted(pos)).strip() or None
