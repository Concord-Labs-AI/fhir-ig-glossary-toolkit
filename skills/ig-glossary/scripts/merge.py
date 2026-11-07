"""Merge validated findings, script findings, identifier rows and verdicts into data/findings.json."""
import argparse
import datetime
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from acronyms import acronym_findings
import config
from common import IDENTIFIER, read_jsonl
from findings import Corpus, make_record, positions

THEME_FORM, THEME_OTHER = "TH-FORM", "TH-OTHER"
TYPE_OF = {"missed-use": "Missed use", "misuse-signal": "Misuse", "form": "Form"}


def theme_for(rec, themes):
    if rec["type"] == "Form":
        return THEME_FORM
    for t in themes:
        if rec["terms"][0] in t["terms"]:
            return t["id"]
    return THEME_OTHER


def relocate(r, find, corpus):
    """Move a record to a wider span (same line) that contains its original one."""
    text = corpus.text(r["file"])
    pos = positions(text, find)
    hits = [p for p in pos if p <= r["start"] and p + len(find) >= r["end"]]
    if len(hits) != 1:
        raise ValueError(f"{r['key']}: widened find {find!r} must cover the original span exactly once")
    return {**r, "find": find, "start": hits[0], "end": hits[0] + len(find),
            "occurrence": pos.index(hits[0]) + 1, "occurrences_total": len(pos)}


def apply_verdicts(records, verdicts, corpus=None):
    """Verdicts apply in file order, so a later pass (consistency, QA) can build on an earlier one."""
    by_key = defaultdict(list)
    for v in verdicts:
        by_key[v["key"]].append(v)
    kept, rejected = [], []
    for r in records:
        orig, reject = r, None
        for v in by_key.get(r["key"], []):
            if v["verdict"] == "reject":
                reject = v  # the last reject's reason is the one reported (the consistency pass refines earlier ones)
                continue
            if v["verdict"] == "revise":
                if v.get("find"):
                    r = relocate(r, v["find"], corpus)
                r = {**r, "replace": v.get("replace", r["replace"]), "issue": v.get("issue", r["issue"]),
                     "revision_note": v["reason"]}
            elif v["verdict"] == "retag":  # QA pass: move the row to another decision, or to Ready
                if v["decision"] and not v.get("recommended"):
                    raise ValueError(f"{r['key']}: retag to {v['decision']} needs a recommended value")
                r = {**r, "decision": v["decision"], "recommended": v.get("recommended") if v["decision"] else None}
            r = {**r, "verified": v["verdict"]}
        (rejected if reject else kept).append({**orig, "verdict_reason": reject["reason"]} if reject else r)
    return kept, rejected


def resolve_overlaps(records):
    """Agent findings win over script/identifier rows on overlapping spans; agent-agent overlaps are errors."""
    out, errors, by_file = [], [], defaultdict(list)
    for r in records:
        by_file[r["file"]].append(r)
    for file in sorted(by_file):
        kept = []
        for r in sorted((r for r in by_file[file] if r["start"] is not None),
                        key=lambda r: (r["start"], r["source"] != "agent")):
            clash = [k for k in kept if r["start"] < k["end"] and k["start"] < r["end"]]
            if not clash:
                kept.append(r)
            elif r["source"] != "agent":
                continue
            elif all(k["source"] != "agent" for k in clash):
                for k in clash:
                    kept.remove(k)
                kept.append(r)
            else:
                errors.append(f"{file}: agent findings overlap ({r['key']} vs {clash[0]['key']})")
        out += kept + [r for r in by_file[file] if r["start"] is None]
    return out, errors


def identifier_rows(hits, segments, rules, corpus, decision):
    seg_by_id = {s["seg_id"]: s for s in segments}
    rows, seen = [], set()
    for h in hits:
        if h["change_class"] != IDENTIFIER or h["type"] == "canonical":
            continue
        seg = seg_by_id[h["seg_id"]]
        k = (seg["file"], seg["artifact"], h["rule_id"])
        if k in seen:
            continue
        seen.add(k)
        pos = positions(corpus.text(seg["file"]), seg["raw"])
        occurrence = pos.index(seg["start"]) + 1 if seg["start"] in pos else 1
        note = rules[h["rule_id"]].get("note", "")
        rows.append(make_record(seg, seg["line"], seg["start"], seg["end"], seg["raw"], "", occurrence, len(pos),
                                terms=[h["term_id"]], type=TYPE_OF[h["type"]], rule=h["rule_id"],
                                issue=f"Artifact name/id contains '{h['match']}'. {note} Renaming is a breaking change.",
                                confidence="High", decision=decision, recommended="keep", hits=[], source="identifier"))
    return rows


def trim_context(text, find, width=220):
    if len(text) <= 2 * width:
        return text
    i = max(text.find(find), 0)
    s, e = max(0, i - width), min(len(text), i + len(find) + width)
    return ("…" if s else "") + text[s:e] + ("…" if e < len(text) else "")


def digest(rows):
    return hashlib.sha256(json.dumps(rows, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def finalize(records, themes, book):
    order = {t["id"]: i for i, t in enumerate(themes)}
    order[THEME_FORM], order[THEME_OTHER] = len(themes), len(themes) + 1
    titles = {t["id"]: t["title"] for t in themes}
    titles[THEME_FORM], titles[THEME_OTHER] = "Form & presentation", "Other"
    names = {t["id"]: t.get("glossary_term") or t.get("label") or t["id"] for t in book["terms"]}
    recs = sorted(records, key=lambda r: (order[theme_for(r, themes)], r["file"],
                                          -1 if r["start"] is None else r["start"]))
    rows = []
    for n, r in enumerate(recs, 1):
        th = theme_for(r, themes)
        rows.append({"id": f"GA-{n:04d}", "theme": titles[th], "theme_id": th,
                     "terms": "; ".join(names[t] for t in r["terms"]), "type": r["type"], "rule": r["rule"] or "",
                     "page": r["artifact"] or Path(r["file"]).name, "section": r["section"] or "",
                     "file": r["file"], "line": r["line"], "occurrence": r["occurrence"],
                     "occurrences_total": r["occurrences_total"], "url": r["url"] or "",
                     "context": trim_context(r["context"], r["find"]), "issue": r["issue"],
                     "find": r["find"], "replace": r["replace"], "change_class": r["change_class"],
                     "apply_method": r["apply_method"], "confidence": r["confidence"],
                     "status": f"Pending {r['decision']}" if r["decision"] else "Ready",
                     "decision": r["decision"], "recommended": r["recommended"],
                     "start": r["start"], "end": r["end"], "hits": r.get("hits", []),
                     "source": r["source"], "key": r["key"]})
    return rows


def main(argv=None):
    ap = config.add_run_arg(argparse.ArgumentParser(description=__doc__))
    args = ap.parse_args(argv)
    cfg = config.load(args.run)
    data = cfg["data"]
    book = config.rulebook(cfg)
    themes = config.themes(cfg)
    segments = read_jsonl(data / "segments.jsonl")
    corpus = Corpus(cfg["snapshot"], segments)
    records = []
    for p in sorted((data / "agent" / "validated").glob("[BQ][0-9][0-9].json")):
        records += json.loads(p.read_text(encoding="utf-8"))["records"]
    records += acronym_findings(segments, corpus)
    rules = {r["id"]: r for t in book["terms"] for r in t.get("rules", [])}
    if book.get("identifier_decision"):
        records += identifier_rows(read_jsonl(data / "hits.jsonl"), segments, rules, corpus, book["identifier_decision"])
    verdicts = []
    for p in sorted((data / "verify").glob("V[0-9][0-9].json")):
        verdicts += json.loads(p.read_text(encoding="utf-8"))
    records, rejected = apply_verdicts(records, verdicts, corpus)  # after every source, so QA can rule on script rows too
    records, errors = resolve_overlaps(records)
    if errors:
        print("\n".join(errors))
        raise SystemExit(1)
    rows = finalize(records, themes, book)
    doc = {"meta": {"snapshot": cfg["ig"]["tag"], "ig": cfg["ig"]["name"], "rulebook": book["version"],
                    "generated": datetime.date.today().isoformat(), "rows": len(rows), "sha256": digest(rows)},
           "rows": rows}
    (data / "findings.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (data / "rejected.json").write_text(json.dumps(rejected, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(rows)} rows ({len(rejected)} rejected by the skeptic pass)")
    for label, key in (("status", "status"), ("type", "type"), ("apply method", "apply_method"), ("theme", "theme")):
        print(f"  by {label}: {dict(Counter(r[key] for r in rows))}")


if __name__ == "__main__":
    main()
