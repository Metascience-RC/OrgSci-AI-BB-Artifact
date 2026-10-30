"""Matsumoto, Shibayama, Kang & Igami (2021): citation-overlap novelty, window 3.

    R_i = references of i published in [Y-10, Y-1]
    J_i = same-subfield papers published in [Y-3, Y-1] that cite at least one work in R_i (at most 1,000)
    novelty_i = 1 - mean_j |R_i & R_j| / |R_i | R_j|,   R_j restricted to [Y-10, Y-1] as well
"""

import random

from openalex import PER_PAGE, get, short_id, works

REF_WINDOW, COCITE_WINDOW, CAP, SEED = 10, 3, 1000, 20210623
EXCLUDED_TYPES = ["paratext", "erratum", "retraction", "editorial", "peer-review", "libguides",
                  "supplementary-material", "grant", "standard"]


def _years(ids, known):
    todo = [i for i in dict.fromkeys(ids) if i not in known]
    for i, w in works(todo, "id,publication_year").items():
        known[i] = w.get("publication_year") if w else None


def _records(pages):
    return {short_id(w["id"]): [short_id(r) for r in w["referenced_works"]] for p in pages for w in p["results"]}


def _cociting(chunk, subfield, Y, seed, sample_if_capped):
    flt = ",".join(["cites:" + "|".join(chunk), f"primary_topic.subfield.id:{subfield}",
                    f"from_publication_date:{Y - COCITE_WINDOW}-01-01", f"to_publication_date:{Y - 1}-12-31",
                    *[f"type:!{t}" for t in EXCLUDED_TYPES]])
    params = {"filter": flt, "select": "id,referenced_works", "per_page": PER_PAGE}
    pages = [get("/works", {**params, "cursor": "*"})]
    if sample_if_capped and pages[0]["meta"]["count"] > CAP:
        # OpenAlex's seeded sample; it does not support cursor paging.
        return _records(get("/works", {**params, "sample": CAP, "seed": seed, "page": p})
                        for p in range(1, CAP // PER_PAGE + 1))
    while pages[-1]["results"] and pages[-1]["meta"].get("next_cursor"):
        pages.append(get("/works", {**params, "cursor": pages[-1]["meta"]["next_cursor"]}))
    return _records(pages)


def novelty(focal, known):
    """focal: OpenAlex record with id, publication_year, primary_topic, referenced_works. known: id -> year."""
    fid, Y = short_id(focal["id"]), focal["publication_year"]
    refs = [short_id(r) for r in focal.get("referenced_works") or []]
    if not refs or not focal.get("primary_topic"):
        return None
    subfield = short_id(focal["primary_topic"]["subfield"]["id"])
    _years(refs, known)
    in_window = lambda ids: {r for r in ids if known.get(r) is not None and Y - REF_WINDOW <= known[r] <= Y - 1}
    R_i = sorted(in_window(refs))
    if not R_i:
        return None
    seed = SEED + int(fid[1:]) % 1_000_000
    chunks = [R_i[k:k + 100] for k in range(0, len(R_i), 100)]  # OpenAlex allows 100 OR values per filter
    J = {}
    for c in chunks:
        J.update(_cociting(c, subfield, Y, seed, sample_if_capped=len(chunks) == 1))
    J.pop(fid, None)
    if len(J) > CAP:
        J = {j: J[j] for j in random.Random(seed).sample(sorted(J), CAP)}
    if not J:
        return None
    _years((r for refs_j in J.values() for r in refs_j), known)
    R_i = set(R_i)
    overlaps = [len(R_i & R_j) / len(R_i | R_j) for R_j in map(in_window, J.values())]
    return 1 - sum(overlaps) / len(overlaps)
