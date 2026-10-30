# Benchmark novelty indicators

This is a minimal implementation of the three bibliometric novelty indicators against which LENS is compared. It
reads a list of OpenAlex work IDs and computes the indicators from OpenAlex data.

| Indicator | Idea | Output |
|---|---|---|
| Matsumoto, Shibayama, Kang & Igami (2021), *Scientometrics* 126 | A paper is novel if it cites references that its own field rarely cites together: one minus the mean Jaccard overlap with the references of same-field papers from the previous three years (citation window 3). | `matsumoto` |
| Shibayama, Yin & Matsumoto (2021), *PLOS ONE* 16(7) | A paper is novel if it cites references that are far apart in meaning: a percentile of the cosine distances between the title embeddings of its references. | `shibayama_q100`, `shibayama_q90` |
| Leahey, Lee & Funk (2023), *Am. Sociol. Rev.* 88(3) | Novelty as claimed by the authors: sentences of the title and abstract that pair a "new" term with a result, theory or method term. | `leahey_new_result`, `leahey_new_theory`, `leahey_new_method` (0/1), `leahey_n_types` (0–3) |

The adaptations to the original definitions, and the checks against the original papers, are described in the
technical appendix of the paper. In short:
- **Matsumoto:** "same field" means the same OpenAlex primary subfield; at most 1,000 same-field papers are used,
  drawn as a seeded sample.
- **Shibayama:** reference titles are embedded with Qwen3-Embedding-8B instead of scispaCy word vectors.
- **Leahey:** the published dictionary is applied to title and abstract.

## Usage

```
pip install -r requirements.txt
export OPENALEX_API_KEY=...                     # recommended
export EMBEDDING_URL=https://your-endpoint      # any OpenAI-compatible /v1/embeddings server
export EMBEDDING_API_KEY=...
export EMBEDDING_MODEL=Qwen/Qwen3-Embedding-8B  # the model name your server uses
python run.py example_ids.txt scores.csv
```

The input file has one OpenAlex ID per line, either as `W…` or as a full URL. A header line is ignored. Each output
column is left empty when it cannot be computed, which happens in these cases:
- **Matsumoto:** no reference from the previous ten years, or no same-field paper that cites one;
- **Shibayama:** fewer than two references with a title;
- **Leahey:** no abstract.

**Cost.** Matsumoto needs by far the most OpenAlex requests: on average about 80 per paper in our run, and more for
papers with many references or a large field.

**Reproducibility.** OpenAlex data change over time, so a later run can give slightly different scores. Embedding
servers usually return slightly different vectors depending on which texts share a batch. In our tests this
changed distances by up to about 0.002.

## References

This is an independent reimplementation; it was not written or reviewed by the authors of the original papers.

- Matsumoto, K., Shibayama, S., Kang, B., & Igami, M. (2021). Introducing a novelty indicator for scientific
  research: validating the knowledge-based combinatorial approach. *Scientometrics*, 126, 6891–6915.
- Shibayama, S., Yin, D., & Matsumoto, K. (2021). Measuring novelty in science with word embedding.
  *PLOS ONE*, 16(7), e0254034. https://doi.org/10.1371/journal.pone.0254034
- Leahey, E., Lee, J., & Funk, R. J. (2023). What types of novelty are most disruptive? *American Sociological
  Review*, 88(3), 562–597. https://doi.org/10.1177/00031224231168074
  The dictionary and rules in `leahey.py` are transcribed from Appendix B (p. 585) of this article.
- Priem, J., Piwowar, H., & Orr, R. (2022). OpenAlex: A fully-open index of scholarly works, authors, venues,
  institutions, and concepts. arXiv:2205.01833. Data: CC0.
- Qwen3-Embedding-8B (Qwen team, Alibaba), Apache 2.0.

## License

Code: MIT (see `LICENSE`).
