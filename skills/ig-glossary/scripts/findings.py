"""Validate agent findings against the snapshot and turn them into exactly-locatable edit records."""
import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

import yaml

from common import DATA, HERE, LOCKED_CLASSES, SNAPSHOT, read_jsonl
from extract import LineIndex

TYPES = {"Misuse", "Missed use", "Form"}
CONFIDENCE = {"High", "Medium"}
RECOMMENDED = {"change", "keep"}
AUTO_METHODS = ("Text replace", "Diagram source + re-render", "Glossary entry edit")


def apply_method(seg):
    if seg["change_class"] in LOCKED_CLASSES or seg["start"] is None or seg["field"] == "svg text":
        return "Manual"
    if seg["kind"] == "diagram":
        return "Diagram source + re-render"
    if seg["kind"] == "glossary":
        return "Glossary entry edit"
    return "Text replace"


def positions(text, find):
    """Start offsets of non-overlapping occurrences — the same rule apply-time uses."""
    out, i = [], text.find(find)
    while i >= 0:
        out.append(i)
        i = text.find(find, i + len(find))
    return out


class Corpus:
    def __init__(self, snapshot, segments):
        self.snapshot = Path(snapshot)
        self.raw, self.idx = {}, {}
        self.segs = defaultdict(list)
        for s in segments:
            self.segs[s["file"]].append(s)

    def text(self, file):
        if file not in self.raw:
            self.raw[file] = (self.snapshot / file).read_text(encoding="utf-8")
            self.idx[file] = LineIndex(self.raw[file])
        return self.raw[file]


def locate(corpus, f):
    """Return (location, None) or (None, error)."""
    file, find = f["file"], f.get("find") or ""
    if not find or find != find.strip():
        return None, "find must be non-empty with no leading or trailing whitespace"
    if "\n" in find:
        return None, "find must not span lines"
    figure = [s for s in corpus.segs[file] if s["start"] is None]
    if figure:
        match = [s for s in figure if find in s["text"]]
        if len(match) != 1:
            return None, f"find matches {len(match)} transcribed labels (need exactly 1)"
        return {"seg": match[0], "start": None, "end": None, "line": None,
                "occurrence": 1, "occurrences_total": 1}, None
    raw = corpus.text(file)
    starts = corpus.idx[file].starts
    line = f.get("line")
    if not isinstance(line, int) or not 1 <= line <= len(starts):
        return None, f"bad line {line!r}"
    ls = starts[line - 1]
    le = raw.find("\n", ls)
    le = len(raw) if le < 0 else le
    pos = positions(raw[ls:le], find)
    if not pos:
        return None, f"find not on line {line}"
    nth = f.get("nth_in_line")
    if len(pos) > 1 and nth is None:
        return None, f"find occurs {len(pos)}x on line {line}; give nth_in_line"
    nth = nth or 1
    if not 1 <= nth <= len(pos):
        return None, f"nth_in_line {nth} out of range 1..{len(pos)}"
    start = ls + pos[nth - 1]
    end = start + len(find)
    seg = next((s for s in corpus.segs[file] if s["start"] is not None and s["start"] <= start and end <= s["end"]), None)
    if seg is None:
        return None, "span is not inside one reader-visible segment"
    vis = seg["visible"]
    if vis[start - seg["start"]] != raw[start] or vis[end - 1 - seg["start"]] != raw[end - 1]:
        return None, "span starts or ends inside hidden markup (link URL, tag, comment)"
    allpos = positions(raw, find)
    if start not in allpos:
        return None, "find overlaps itself in this file; lengthen it"
    return {"seg": seg, "start": start, "end": end, "line": line,
            "occurrence": allpos.index(start) + 1, "occurrences_total": len(allpos)}, None


def replace_problems(seg, find, replace):
    if not isinstance(replace, str) or replace == find:
        return ["replace must be text that differs from find"]
    probs = []
    if "\n" in replace:
        probs.append("replace must not contain a newline")
    if seg["kind"] == "fsh" and re.search(r'(?<!\\)"', replace):
        probs.append('FSH string: escape double quotes as \\"')
    if seg["field"] == "table-row" and replace.count("|") != find.count("|"):
        probs.append("table row: replace must keep the same number of | characters")
    return probs


def make_record(seg, line, start, end, find, replace, occurrence, total, **meta):
    key = f"{seg['file']}@{start}" if start is not None else f"{seg['seg_id']}@figure"
    rec = {"key": key, "file": seg["file"], "line": line, "start": start, "end": end,
           "occurrence": occurrence, "occurrences_total": total, "find": find, "replace": replace,
           "seg_id": seg["seg_id"], "change_class": seg["change_class"], "kind": seg["kind"],
           "field": seg["field"], "section": seg["section"], "artifact": seg["artifact"], "url": seg["url"],
           "context": seg["text"], "apply_method": apply_method(seg)}
    rec.update(meta)
    return rec


def overlap_errors(records):
    errors, by_file = [], defaultdict(list)
    for r in records:
        if r["start"] is not None:
            by_file[r["file"]].append(r)
    for file, rs in by_file.items():
        rs.sort(key=lambda r: r["start"])
        for a, b in zip(rs, rs[1:]):
            if b["start"] < a["end"]:
                errors.append(f"{file}: findings at lines {a['line']} and {b['line']} overlap "
                              f"('{a['find']}' / '{b['find']}'); merge them into one finding")
    return errors


def validate_batch(out, entry, corpus, book):
    terms = {t["id"] for t in book["terms"]}
    rules = {r["id"] for t in book["terms"] for r in t.get("rules", [])}
    open_decisions = {d["id"] for d in book["decisions"] if not d.get("team_decision")}
    hits = {h["hit_id"]: h for h in entry["hits"]}
    files = set(entry["files"])
    used, records, errors = defaultdict(list), [], []
    for i, f in enumerate(out.get("findings", [])):
        where = f"finding {i + 1} ({f.get('file')}:{f.get('line')})"
        probs = []
        if f.get("file") not in files:
            probs.append("file is not in this batch")
        if f.get("type") not in TYPES:
            probs.append(f"type must be one of {sorted(TYPES)}")
        if f.get("confidence") not in CONFIDENCE:
            probs.append("confidence must be High or Medium")
        if not f.get("terms") or not set(f["terms"]) <= terms:
            probs.append("terms must be a non-empty list of rulebook term ids")
        if f.get("rule") is not None and f["rule"] not in rules:
            probs.append(f"unknown rule {f['rule']}")
        if not f.get("issue"):
            probs.append("issue is required")
        for h in f.get("hits", []):
            if h in hits:
                used[h].append(where)
            else:
                probs.append(f"unknown hit {h}")
        pending = sorted({hits[h]["decision"] for h in f.get("hits", [])
                          if h in hits and hits[h]["decision"] in open_decisions})
        decision = f.get("decision") or (pending[0] if pending else None)
        if decision and decision not in open_decisions:
            probs.append(f"unknown or already-decided decision {decision}")
        elif decision and f.get("recommended") not in RECOMMENDED:
            probs.append("pending finding needs recommended: change or keep")
        loc = None
        if f.get("file") in files:
            loc, err = locate(corpus, f)
            if err:
                probs.append(err)
            else:
                probs += replace_problems(loc["seg"], f["find"], f.get("replace"))
        if probs:
            errors += [f"{where}: {p}" for p in probs]
            continue
        records.append(make_record(loc["seg"], loc["line"], loc["start"], loc["end"], f["find"], f["replace"],
                                   loc["occurrence"], loc["occurrences_total"], terms=f["terms"], type=f["type"],
                                   rule=f.get("rule"), issue=f["issue"], confidence=f["confidence"],
                                   decision=decision, recommended=f.get("recommended") if decision else None,
                                   hits=f.get("hits", []), source="agent"))
    for d in out.get("dismissed", []):
        h = d.get("hit")
        if h not in hits:
            errors.append(f"dismissed unknown hit {h}")
        elif not d.get("reason"):
            errors.append(f"dismissed {h} needs a reason")
        else:
            used[h].append("dismissed")
    for h in hits:
        if not used[h]:
            errors.append(f"hit {h} has no disposition")
        elif "dismissed" in used[h] and len(used[h]) > 1:
            errors.append(f"hit {h} is both dismissed and covered by a finding")
    errors += overlap_errors(records)
    return records, errors


def batch_entry(manifest, bid, out):
    """QA batches (Q01, ...) add findings outside the reading packets, so they own only the files they touch."""
    if bid in manifest or not bid.startswith("Q"):
        return manifest[bid]
    return {"title": f"QA additions {bid}", "files": sorted({f.get("file") for f in out.get("findings", [])}), "hits": []}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--batch", help="e.g. B01 (default: every batch with agent output)")
    ap.add_argument("--snapshot", type=Path, default=SNAPSHOT)
    ap.add_argument("--data", type=Path, default=DATA)
    args = ap.parse_args(argv)
    book = yaml.safe_load((HERE / "rulebook.yaml").read_text(encoding="utf-8"))
    manifest = json.loads((args.data / "batches" / "manifest.json").read_text(encoding="utf-8"))
    corpus = Corpus(args.snapshot, read_jsonl(args.data / "segments.jsonl"))
    bids = [args.batch] if args.batch else sorted(p.stem for p in (args.data / "agent").glob("[BQ][0-9][0-9].json"))
    failed = False
    for bid in bids:
        out = json.loads((args.data / "agent" / f"{bid}.json").read_text(encoding="utf-8"))
        records, errors = validate_batch(out, batch_entry(manifest, bid, out), corpus, book)
        if errors:
            failed = True
            print(f"{bid}: {len(errors)} problem(s)")
            print("\n".join(f"  - {e}" for e in errors))
            continue
        dest = args.data / "agent" / "validated" / f"{bid}.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps({"records": records, "dismissed": out.get("dismissed", []),
                                    "glossary_feedback": out.get("glossary_feedback", [])},
                                   indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{bid}: OK — {len(records)} findings, {len(out.get('dismissed', []))} dismissed")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
