"""Compute the three novelty indicators for a list of OpenAlex works.

    python run.py ids.txt scores.csv
"""

import re
import sys

import nltk
import pandas as pd
from tqdm import tqdm

import leahey
import matsumoto
import shibayama
from openalex import abstract, short_id, works

SELECT = "id,title,publication_year,primary_topic,referenced_works,abstract_inverted_index"
COLUMNS = ["openalex_id", "matsumoto", "shibayama_q100", "shibayama_q90",
           "leahey_new_result", "leahey_new_theory", "leahey_new_method", "leahey_n_types"]


def main(ids_path, out_path):
    nltk.download("punkt_tab", quiet=True)
    with open(ids_path, encoding="utf-8") as f:
        ids = [m.group(0) for line in f if (m := re.search(r"W\d+", line))]
    focal = works(ids, SELECT)
    years, rows = {}, []
    for i in tqdm(ids):
        w = focal[i]
        row = {"openalex_id": i}
        if w:
            years[short_id(w["id"])] = w["publication_year"]
            row["matsumoto"] = matsumoto.novelty(w, years)
            shib = shibayama.novelty(w) or {}
            row.update({f"shibayama_q{q}": shib.get(q) for q in shibayama.QS})
            claims = leahey.novelty(w.get("title"), abstract(w.get("abstract_inverted_index"))) or {}
            row.update({f"leahey_{k}": v for k, v in claims.items()})
        rows.append(row)
    df = pd.DataFrame(rows).reindex(columns=COLUMNS)
    df[COLUMNS[4:]] = df[COLUMNS[4:]].astype("Int64")
    df.to_csv(out_path, index=False)


if __name__ == "__main__":
    main(*sys.argv[1:3])
