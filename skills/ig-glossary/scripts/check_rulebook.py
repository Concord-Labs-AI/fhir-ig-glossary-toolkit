"""Check rulebook.yaml: shape, regexes, decision references, and coverage of the glossary's terms."""
import argparse

import config
import scan
from common import read_jsonl

REQUIRED_DECISION = ("id", "title", "question", "options", "recommendation")


def glossary_terms(segments):
    """Headwords from the glossary page's table rows (first cell), skipping the header row."""
    out = []
    for s in segments:
        if s["kind"] == "glossary" and s["field"] == "table-row":
            cell = s["text"].strip("| ").split(" | ")[0].strip()
            if cell and cell != "Term":
                out.append(cell)
    return out


def problems(book, glossary_terms=None):
    probs = []
    try:
        scan.load_rules(book)
    except (ValueError, KeyError) as err:
        probs.append(str(err))
    for t in book.get("terms", []):
        tid = t.get("id", "?")
        if not t.get("glossary_term"):
            probs.append(f"{tid}: glossary_term required")
        if not t.get("definition"):
            probs.append(f"{tid}: definition required")
        if not any(r.get("type") == "canonical" for r in t.get("rules", [])):
            probs.append(f"{tid}: no canonical rule")
    ids = set()
    for d in book.get("decisions", []):
        did = d.get("id", "?")
        ids.add(did)
        for k in REQUIRED_DECISION:
            if not d.get(k):
                probs.append(f"{did}: {k} required")
        letter = str(d.get("recommendation", "")).partition(" — ")[0].strip()
        letters = {str(o).split(":", 1)[0].strip() for o in d.get("options", [])}
        if letter and letter not in letters:
            probs.append(f"{did}: recommendation {letter!r} names none of its options {sorted(letters)}")
    idd = book.get("identifier_decision")
    if idd and idd not in ids:
        probs.append(f"identifier_decision {idd} is not a decision")
    if glossary_terms:
        have = {t.get("glossary_term") for t in book.get("terms", [])}
        probs += [f"glossary term has no rulebook entry: {g}" for g in glossary_terms if g not in have]
    return probs


def main(argv=None):
    ap = config.add_run_arg(argparse.ArgumentParser(description=__doc__))
    args = ap.parse_args(argv)
    cfg = config.load(args.run)
    segs_path = cfg["data"] / "segments.jsonl"
    terms = glossary_terms(read_jsonl(segs_path)) if segs_path.exists() else None
    probs = problems(config.rulebook(cfg), terms)
    if probs:
        print("\n".join(f"- {p}" for p in probs))
        raise SystemExit(1)
    print("rulebook: OK" + ("" if terms else " (glossary coverage not checked: run extract.py first)"))


if __name__ == "__main__":
    main()
