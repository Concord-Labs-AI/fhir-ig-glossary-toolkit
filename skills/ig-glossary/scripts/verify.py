"""Skeptic pass: packets of findings to re-check, and validation of the verdicts."""
import argparse
import json
from pathlib import Path

from common import DATA
from findings import replace_problems

VERDICTS = {"confirm", "reject", "revise"}


def needs_verification(rec):
    return rec["type"] == "Misuse" or rec["confidence"] == "Medium"


def build_packets(records, n=3):
    picked = [r for r in records if needs_verification(r)]
    packets, sizes = [[] for _ in range(n)], [0] * n
    for f in sorted({r["file"] for r in picked}):  # keep a file's findings together; balance by count
        group = sorted((r for r in picked if r["file"] == f), key=lambda r: r["start"] or 0)
        i = sizes.index(min(sizes))
        packets[i] += group
        sizes[i] += len(group)
    return [p for p in packets if p]


def packet_md(vid, recs):
    lines = [f"# Verification packet {vid}", "", f"{len(recs)} findings — one verdict per key.", ""]
    for r in recs:
        decision = f"{r['decision']} (recommended: {r['recommended']})" if r.get("decision") else "—"
        lines += [f"## `{r['key']}`", "",
                  f"- File: `{r['file']}` line {r['line']} ({r['change_class']}, {r['field']})",
                  f"- Type / terms / confidence: {r['type']} / {', '.join(r['terms'])} / {r['confidence']}",
                  f"- Decision: {decision}", f"- Issue: {r['issue']}",
                  f"- Find: `{r['find']}`", f"- Replace: `{r['replace']}`",
                  f"- Context: {r['context'][:600]}", ""]
    return "\n".join(lines)


def validate_verdicts(verdicts, keys):
    errors, seen = [], set()
    for v in verdicts:
        k = v.get("key")
        if k not in keys:
            errors.append(f"unknown key {k}")
            continue
        if k in seen:
            errors.append(f"duplicate verdict for {k}")
        seen.add(k)
        if v.get("verdict") not in VERDICTS:
            errors.append(f"{k}: verdict must be confirm, reject or revise")
        if not v.get("reason"):
            errors.append(f"{k}: reason is required")
        if v.get("verdict") == "revise":
            errors += [f"{k}: {p}" for p in replace_problems(keys[k], keys[k]["find"], v.get("replace"))]
    errors += [f"no verdict for {k}" for k in sorted(set(keys) - seen)]
    return errors


def load_records(data):
    recs = []
    for p in sorted((data / "agent" / "validated").glob("B[0-9][0-9].json")):
        recs += json.loads(p.read_text(encoding="utf-8"))["records"]
    return recs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--packets", action="store_true")
    mode.add_argument("--check", metavar="VID")
    ap.add_argument("--n", type=int, default=3, help="number of packets (one skeptic agent each)")
    ap.add_argument("--data", type=Path, default=DATA)
    args = ap.parse_args(argv)
    vdir = args.data / "verify"
    vdir.mkdir(parents=True, exist_ok=True)
    if args.packets:
        for n, recs in enumerate(build_packets(load_records(args.data), args.n), 1):
            vid = f"V{n:02d}"
            (vdir / f"{vid}.md").write_text(packet_md(vid, recs), encoding="utf-8")
            (vdir / f"{vid}.keys.json").write_text(json.dumps([r["key"] for r in recs]) + "\n")
            print(f"{vid}: {len(recs)} findings")
        return
    keys = set(json.loads((vdir / f"{args.check}.keys.json").read_text()))
    by_key = {r["key"]: r for r in load_records(args.data) if r["key"] in keys}
    errors = validate_verdicts(json.loads((vdir / f"{args.check}.json").read_text(encoding="utf-8")), by_key)
    print(f"{args.check}: OK" if not errors else "\n".join(errors))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
