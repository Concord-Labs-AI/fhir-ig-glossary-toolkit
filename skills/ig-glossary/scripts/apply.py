"""Apply finding rows to an IG tree by exact (find, occurrence); drift is reported, never guessed."""
import argparse
import json
from collections import defaultdict
from pathlib import Path

from batches import hit_id
from common import DATA, read_jsonl
from findings import AUTO_METHODS, positions


def apply_rows(rows, root, choose):
    """choose(row) -> replacement text, or None to skip the row."""
    report = {"applied": [], "skipped": [], "drifted": []}
    todo = defaultdict(list)
    for r in rows:
        text = choose(r)
        if text is None or r["apply_method"] not in AUTO_METHODS:
            report["skipped"].append(r["id"])
        else:
            todo[r["file"]].append((r, text))
    for file, items in sorted(todo.items()):
        path = Path(root) / file
        src = path.read_text(encoding="utf-8")
        spans = []
        for r, text in items:
            pos = positions(src, r["find"])
            if len(pos) != r["occurrences_total"]:
                report["drifted"].append({"id": r["id"], "reason": f"'{r['find']}' occurs {len(pos)}x now, "
                                                                  f"{r['occurrences_total']}x at the snapshot"})
                continue
            s = pos[r["occurrence"] - 1]
            spans.append((s, s + len(r["find"]), text, r["id"]))
        spans.sort()
        for a, b in zip(spans, spans[1:]):
            if b[0] < a[1]:
                raise ValueError(f"{file}: rows {a[3]} and {b[3]} overlap")
        for s, e, text, rid in reversed(spans):
            src = src[:s] + text + src[e:]
            report["applied"].append(rid)
        path.write_text(src, encoding="utf-8")
    return report


def residuals(before, after, explained_hit_ids):
    """Per non-canonical rule: editable hits left after a dry run vs those explained by dismissals/Manual rows."""
    out = defaultdict(lambda: {"before": 0, "after": 0, "explained": 0})
    for h in before:
        if h["type"] != "canonical" and not h["locked"]:
            out[h["rule_id"]]["before"] += 1
            if hit_id(h) in explained_hit_ids:
                out[h["rule_id"]]["explained"] += 1
    for h in after:
        if h["type"] != "canonical" and not h["locked"]:
            out[h["rule_id"]]["after"] += 1
    for v in out.values():
        v["unexplained"] = v["after"] - v["explained"]
    return dict(out)


def explained_hits(rows, data):
    """Hits deliberately left in place: Manual rows, agent dismissals, and findings the skeptic pass rejected."""
    explained = {h for r in rows if r["apply_method"] == "Manual" for h in r["hits"]}
    for p in (data / "agent" / "validated").glob("B[0-9][0-9].json"):
        explained |= {d["hit"] for d in json.loads(p.read_text(encoding="utf-8"))["dismissed"]}
    rejected = data / "rejected.json"
    if rejected.exists():
        explained |= {h for r in json.loads(rejected.read_text(encoding="utf-8")) for h in r["hits"]}
    return explained


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, help="IG tree to edit (dry run: a scratch worktree)")
    ap.add_argument("--residuals", action="store_true", help="compare data/hits.jsonl with data/dryrun/hits.jsonl")
    ap.add_argument("--data", type=Path, default=DATA)
    args = ap.parse_args(argv)
    doc = json.loads((args.data / "findings.json").read_text(encoding="utf-8"))
    out = args.data / "dryrun"
    out.mkdir(parents=True, exist_ok=True)
    if args.residuals:
        res = residuals(read_jsonl(args.data / "hits.jsonl"), read_jsonl(out / "hits.jsonl"),
                        explained_hits(doc["rows"], args.data))
        (out / "residuals.json").write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
        for rule, v in sorted(res.items()):
            if v["unexplained"] > 0:
                print(f"  {rule:18} before {v['before']:4} after {v['after']:4} "
                      f"explained {v['explained']:4} UNEXPLAINED {v['unexplained']}")
        return
    report = apply_rows(doc["rows"], args.root, lambda r: r["replace"] or None)
    (out / "apply-report.json").write_text(json.dumps(report, indent=1) + "\n")
    print(f"applied {len(report['applied'])}, skipped {len(report['skipped'])}, drifted {len(report['drifted'])}")
    for d in report["drifted"]:
        print(f"  drift {d['id']}: {d['reason']}")


if __name__ == "__main__":
    main()
