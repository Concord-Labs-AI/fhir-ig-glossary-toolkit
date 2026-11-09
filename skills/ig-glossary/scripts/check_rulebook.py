"""Check rulebook.yaml: shape, regexes, decision references, and coverage of the glossary's terms."""
import argparse
import re

import config
import scan
from common import read_jsonl

REQUIRED_DECISION = ("id", "title", "question", "options", "recommendation")


def headword(text):
    """First table cell as a reader sees it: markup, link syntax and tags removed."""
    cell = text.strip().strip("|").split("|")[0]
    cell = re.sub(r"\[([^\]]*)\]\([^)]*\)|<[^>]*>|[*_`]", lambda m: m.group(1) or "", cell)
    return " ".join(cell.split())


def glossary_terms(segments):
    """Headwords from the glossary page's table rows (first cell). The first row is the header; so is any repeat of it."""
    out, header = [], None
    for s in segments:
        if s["kind"] == "glossary" and s["field"] == "table-row":
            cell = headword(s["text"])
            if header is None:
                header = cell
            elif cell and cell != header:
                out.append(cell)
    return out


def problems(book, glossary_terms=None, acronyms=None):
    probs = []
    for t in book.get("terms", []):
        if not t.get("id"):
            probs.append(f"term without id: {t.get('glossary_term', '?')}")
        for r in t.get("rules", []):
            probs += [f"{t.get('id', '?')}: rule {r.get('id', '?')} needs {k}" for k in ("id", "type", "pattern") if not r.get(k)]
    if not probs:
        try:
            scan.load_rules(book)
        except ValueError as err:
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
        rec = str(d.get("recommendation", ""))
        letter = rec.partition(" — ")[0].strip()
        letters = {str(o).split(":", 1)[0].strip() for o in d.get("options", [])}
        if rec and " — " not in rec:
            probs.append(f'{did}: recommendation must start with an option letter and " — " (e.g. "A — reason")')
        elif letter and letter not in letters:
            probs.append(f"{did}: recommendation {letter!r} names none of its options {sorted(letters)}")
    idd = book.get("identifier_decision")
    if idd and idd not in ids:
        probs.append(f"identifier_decision {idd} is not a decision")
    if glossary_terms:
        have = {t.get("glossary_term") for t in book.get("terms", [])}
        probs += [f"glossary term has no rulebook entry: {g}" for g in glossary_terms if g not in have]
    if acronyms:
        term_ids = {t.get("id") for t in book.get("terms", [])}
        probs += [f"acronyms.table.{acr}.term {e['term']} is not a rulebook term id"
                  for acr, e in acronyms.get("table", {}).items() if e["term"] not in term_ids]
    return probs


def main(argv=None):
    ap = config.add_run_arg(argparse.ArgumentParser(description=__doc__))
    args = ap.parse_args(argv)
    cfg = config.load(args.run)
    segs_path = cfg["data"] / "segments.jsonl"
    terms = glossary_terms(read_jsonl(segs_path)) if segs_path.exists() else None
    probs = problems(config.rulebook(cfg), terms, cfg["acronyms"])
    if probs:
        print("\n".join(f"- {p}" for p in probs))
        raise SystemExit(1)
    note = ""
    if terms is None:
        note = " (glossary coverage not checked: run extract.py first)"
    elif not terms:
        note = (" (glossary coverage not checked: the glossary page has no table rows; "
                "confirm by hand that every glossary term has an entry)")
    print("rulebook: OK" + note)


if __name__ == "__main__":
    main()
