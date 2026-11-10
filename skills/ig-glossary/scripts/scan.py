"""Rulebook-driven pattern scan over extracted segments → hits, counts, review report."""
import argparse
import json
import re
from collections import Counter
from pathlib import Path

import config
from common import IDENTIFIER, LOCKED_CLASSES, read_jsonl, write_jsonl

RULE_TYPES = {"canonical", "missed-use", "misuse-signal", "form"}


def load_rules(book):
    decisions = {d["id"] for d in book.get("decisions", [])}
    rules, seen = [], set()
    for term in book["terms"]:
        for r in term.get("rules", []):
            rid = r["id"]
            if rid in seen:
                raise ValueError(f"duplicate rule id {rid}")
            seen.add(rid)
            if r["type"] not in RULE_TYPES:
                raise ValueError(f"{rid}: unknown rule type {r['type']!r}")
            decision = r.get("decision") or term.get("decision")
            if decision and decision not in decisions:
                raise ValueError(f"{rid}: unknown decision {decision}")
            try:
                rx = re.compile(r["pattern"], 0 if r.get("case_sensitive") else re.I)
            except re.error as e:
                raise ValueError(f"{rid}: bad pattern: {e}") from e
            rules.append({**r, "term_id": term["id"], "rx": rx, "decision": decision,
                          "exempt": set(term.get("exempt_classes", [])) | set(r.get("exempt_classes", [])),
                          "skip_fields": set(r.get("skip_fields", []))})
    return rules


def context(hay, s, e, width=70):
    return re.sub(r"\s+", " ", f"{hay[max(0, s - width):s]}[[{hay[s:e]}]]{hay[e:e + width]}").strip()


def scan(segments, rules):
    hits = []
    for seg in segments:
        whole = seg["change_class"] == IDENTIFIER or seg["start"] is None
        hay = seg["text"] if whole else seg["visible"]
        for r in rules:
            if seg["field"] in r["skip_fields"]:
                continue
            for m in r["rx"].finditer(hay):
                hits.append({
                    "rule_id": r["id"], "term_id": r["term_id"], "type": r["type"],
                    "seg_id": seg["seg_id"], "file": seg["file"], "field": seg["field"],
                    "line": seg["line"] if whole else seg["line"] + hay.count("\n", 0, m.start()),
                    "start": None if whole else seg["start"] + m.start(),
                    "end": None if whole else seg["start"] + m.end(),
                    "match": m.group(0), "change_class": seg["change_class"],
                    "locked": seg["change_class"] in LOCKED_CLASSES or seg["change_class"] in r["exempt"],
                    "decision": r["decision"], "context": context(hay, m.start(), m.end())})
    return hits


def summarize(hits, rules):
    out = {r["id"]: {"term_id": r["term_id"], "type": r["type"], "total": 0, "editable": 0,
                     "by_class": Counter(), "by_file": Counter()} for r in rules}
    for h in hits:
        b = out[h["rule_id"]]
        b["total"] += 1
        b["editable"] += not h["locked"]
        b["by_class"][h["change_class"]] += 1
        b["by_file"][h["file"]] += 1
    for b in out.values():
        b["by_class"], b["by_file"] = dict(b["by_class"]), dict(b["by_file"].most_common())
    return out


def write_review(book, counts, hits, path, tag, samples=3):
    lines = ["# Rulebook review (Checkpoint 2)", "",
             f"Counts are pattern hits over the {tag} corpus; *editable* excludes locked classes",
             "(Identifier, External, Historical). Reading agents judge each hit in context in Step 5.", "",
             "## Decisions register", ""]
    for d in book.get("decisions", []):
        lines += [f"### {d['id']} — {d.get('title', '')}", "", d.get("question", ""), ""]
        lines += [f"- **{o}**" for o in d.get("options", [])]
        lines += ["", f"Recommendation: {d.get('recommendation', '')}", ""]
    lines += ["## Terms", ""]
    for term in book["terms"]:
        lines += [f"### {term.get('glossary_term') or term['id']}", ""]
        if term.get("definition"):
            lines += [f"> {term['definition']}", ""]
        lines += ["| Rule | Type | Pattern | Suggest | Total | Editable | Top files |",
                  "|---|---|---|---|---|---|---|"]
        for r in term.get("rules", []):
            c = counts[r["id"]]
            top = ", ".join(f"{Path(f).name} ({n})" for f, n in list(c["by_file"].items())[:3])
            pattern = r["pattern"].replace("|", "\\|")
            lines.append(f"| {r['id']} | {r['type']} | `{pattern}` | {r.get('suggest', '')} | "
                         f"{c['total']} | {c['editable']} | {top} |")
        lines.append("")
        for r in term.get("rules", []):
            if r["type"] == "canonical":
                continue
            ex = sorted((h for h in hits if h["rule_id"] == r["id"]), key=lambda h: h["locked"])[:samples]
            if ex:
                lines.append(f"**{r['id']}** — {r.get('note', '')}")
                lines += [f"- `{h['file'].split('/')[-1]}:{h['line']}` {h['context']}" for h in ex]
                lines.append("")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv=None):
    ap = config.add_run_arg(argparse.ArgumentParser(description=__doc__))
    args = ap.parse_args(argv)
    cfg = config.load(args.run)
    book = config.rulebook(cfg)
    rules = load_rules(book)
    hits = scan(read_jsonl(cfg["data"] / "segments.jsonl"), rules)
    counts = summarize(hits, rules)
    write_jsonl(cfg["data"] / "hits.jsonl", hits)
    (cfg["data"] / "counts.json").write_text(json.dumps(counts, indent=1) + "\n")
    write_review(book, counts, hits, cfg["data"] / "rulebook-review.md", cfg["ig"]["tag"])
    print(f"{len(hits)} hits from {len(rules)} rules; "
          f"{sum(not h['locked'] for h in hits)} editable; review → {cfg['data'] / 'rulebook-review.md'}")


if __name__ == "__main__":
    main()
