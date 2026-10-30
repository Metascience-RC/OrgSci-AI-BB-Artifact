"""Shibayama, Yin & Matsumoto (2021): semantic distance between cited references.

    v_k  = embedding of the title of reference k (Qwen3-Embedding-8B)
    d_kl = 1 - cos(v_k, v_l) for all pairs of references
    N_q  = q-th percentile of {d_kl}; q = 100 (the maximum) and q = 90
"""

import html
import os
import re

import httpx
import numpy as np

from openalex import short_id, works

BATCH = 128
QS = (100, 90)


def clean(title):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", title or ""))).strip()


def embed(texts):
    url = os.environ["EMBEDDING_URL"].rstrip("/").removesuffix("/v1") + "/v1/embeddings"
    headers = {"Authorization": f"Bearer {os.environ['EMBEDDING_API_KEY']}"}
    model = os.environ.get("EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-8B")
    out = []
    with httpx.Client(timeout=300) as http:
        for k in range(0, len(texts), BATCH):
            r = http.post(url, headers=headers, json={"model": model, "input": texts[k:k + BATCH], "encoding_format": "float"})
            r.raise_for_status()
            out += [d["embedding"] for d in sorted(r.json()["data"], key=lambda d: d["index"])]
    return np.asarray(out, dtype=np.float32)


def novelty(focal):
    """{q: N_q}, or None if fewer than two references have a title."""
    refs = [short_id(r) for r in focal.get("referenced_works") or []]
    titles = {}
    for w in works(refs, "id,title").values():  # two IDs merged into one work count once
        if w and (t := clean(w.get("title"))):
            titles[short_id(w["id"])] = t
    if len(titles) < 2:
        return None
    X = embed(list(titles.values()))
    X /= np.linalg.norm(X, axis=1, keepdims=True)
    d = np.clip(1 - (X @ X.T)[np.triu_indices(len(X), k=1)], 0, 2)
    return {q: float(np.percentile(d, q, method="averaged_inverted_cdf")) for q in QS}
