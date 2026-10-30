"""Leahey, Lee & Funk (2023): dictionary-based novelty claims in title + abstract.

A sentence claims a new result / theory / method if it contains a NEW term and a term of that type. Tokens and
terms are compared as Porter stems. Dictionary and rules: Appendix B, p. 585, ASR 88(3), transcribed verbatim.
"""

import re

import nltk
from nltk.stem import PorterStemmer

_stem = PorterStemmer().stem

TERMS = {
    "new": ["advancement", "breakthrough", "create", "demonstrate", "develop", "devise", "discover", "innovative",
            "introduce", "original", "novel", "new", "propose", "unique", "unknown", "unrecognized"],
    "result": ["confirm", "correlation", "effect", "evidence", "finding", "found", "identify", "discovery",
               "observation", "outcome", "prove", "rate", "response", "result", "support", "show"],
    "theory": ["concept", "explanation", "explain", "generalize", "hypotheses", "hypothesis", "mechanism", "model",
               "synthesis", "synthesize", "term", "theoretical", "theorize", "theory", "thesis"],
    "method": ["analysis", "analyze", "apparatus", "assay", "bioassay", "calculate", "classification", "criteria",
               "criterion", "design", "equipment", "examine", "experiment", "formula", "index", "means", "measure",
               "method", "methodology", "procedure", "process", "protocol", "quantify", "scale", "strategy",
               "technique", "technology", "test", "tool", "treatment"],
}
# Rule 1: "new" followed by one of these is not NEW.
NEW_NOT_FOLLOWED_BY = [
    "york", "haven", "orleans", "delhi", "england", "zealand", "jersey", "brunswick", "mexico", "hampshire", "wiley",
    "dru", "school", "institute", "institution", "edition", "volume", "journal", "version", "teaching",
    "information", "job", "phd", "editor", "faculty", "student", "graduate", "south", "era", "title", "member",
    "host", "business", "experience", "draft", "series", "publication", "textbook", "book", "manuscript", "place",
    "chapter", "laboratory"]
# Rule 2: stem "origin" followed by one of these is not NEW.
ORIGIN_NOT_FOLLOWED_BY = ["of", "in", "paper", "and", "from", "work", "book", "edition", "with", "is", "publication"]
# Rule 3: "new" with a negator nearby is not NEW. "Near" is not specified; we use 3 tokens on either side.
NEGATORS, NEGATION_WINDOW = ["not", "no", "lack"], 3
# Rule 4: "first" is NEW only if followed by one of these.
FIRST_FOLLOWED_BY = ["principles", "patient", "result", "observation", "attempt", "experiment", "synthesis", "study",
                     "comprehensive", "application", "description", "describe", "evidence", "to", "design"]

STEMS = {c: {_stem(t) for t in ts} for c, ts in TERMS.items()}
RULE1, RULE2, RULE3, RULE4 = ({_stem(t) for t in ts} for ts in
                              (NEW_NOT_FOLLOWED_BY, ORIGIN_NOT_FOLLOWED_BY, NEGATORS, FIRST_FOLLOWED_BY))
TYPES = ("result", "theory", "method")


def sentence_tags(tokens):
    st = [_stem(t) for t in tokens]
    has_new, has_type = False, dict.fromkeys(TYPES, False)
    for i, (tok, s) in enumerate(zip(tokens, st)):
        nxt = st[i + 1] if i + 1 < len(st) else None
        if s == "first":
            has_new |= nxt in RULE4
        elif s in STEMS["new"]:
            excluded = (tok == "new" and nxt in RULE1) or (s == "origin" and nxt in RULE2)
            if tok == "new" and not excluded:
                window = st[max(0, i - NEGATION_WINDOW):i] + st[i + 1:i + 1 + NEGATION_WINDOW]
                excluded = any(w in RULE3 for w in window)
            has_new |= not excluded
        for x in TYPES:
            has_type[x] |= s in STEMS[x]
    return {x: has_new and has_type[x] for x in TYPES}


def novelty(title, abstract):
    """{new_result, new_theory, new_method: 0/1, n_types: 0-3}, or None without an abstract."""
    if not abstract:
        return None
    text = re.sub(r"\s+", " ", f"{(title or '').strip()}. {abstract.strip()}").strip()
    out = dict.fromkeys(TYPES, 0)
    for sent in nltk.sent_tokenize(text):
        tokens = [t for t in nltk.word_tokenize(sent.lower()) if t.isalpha()]
        for x, tagged in sentence_tags(tokens).items():
            out[x] |= tagged
    return {**{f"new_{x}": int(v) for x, v in out.items()}, "n_types": sum(out.values())}
