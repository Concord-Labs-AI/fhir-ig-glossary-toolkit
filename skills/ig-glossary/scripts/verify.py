"""Skeptic pass: packets of findings to re-check, and validation of the verdicts."""
import argparse
import json
from pathlib import Path

import config
from findings import replace_problems

VERDICTS = {"confirm", "reject", "revise", "retag"}


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


def validate_verdicts(verdicts, keys, partial=False, open_decisions=None):
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
            errors.append(f"{k}: verdict must be confirm, reject, revise or retag")
        if not v.get("reason"):
            errors.append(f"{k}: reason is required")
        if v.get("verdict") == "revise":
            errors += [f"{k}: {p}" for p in replace_problems(keys[k], keys[k]["find"], v.get("replace"))]
        if v.get("verdict") == "retag":
            if "decision" not in v:
                errors.append(f"{k}: retag needs decision (a D-id, or null for Ready)")
            elif v["decision"] and open_decisions is not None and v["decision"] not in open_decisions:
                errors.append(f"{k}: retag to {v['decision']} is not an open decision "
                              "(use a D-id from the rulebook, or null for Ready)")
            elif v["decision"] and v.get("recommended") not in ("change", "keep"):
                errors.append(f"{k}: retag to {v['decision']} needs recommended change or keep")
    if not partial:
        errors += [f"no verdict for {k}" for k in sorted(set(keys) - seen)]
    return errors


def load_records(data, files=None):
    recs = []
    for p in sorted((data / "agent" / "validated").glob("B[0-9][0-9].json")):
        recs += json.loads(p.read_text(encoding="utf-8"))["records"]
    return [r for r in recs if files is None or r["file"] in files]


def main(argv=None):
    ap = config.add_run_arg(argparse.ArgumentParser(description=__doc__))
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--packets", action="store_true")
    mode.add_argument("--check", metavar="VID")
    ap.add_argument("--n", type=int, default=3, help="number of packets (one skeptic agent each)")
    ap.add_argument("--files", help="only records in these files (a batch id like B03, or a comma-separated list)")
    ap.add_argument("--partial", action="store_true", help="a verdict file that rules on a subset of keys (consistency pass)")
    args = ap.parse_args(argv)
    cfg = config.load(args.run)
    data = cfg["data"]
    vdir = data / "verify"
    vdir.mkdir(parents=True, exist_ok=True)
    files = None
    if args.files:
        manifest = json.loads((data / "batches" / "manifest.json").read_text(encoding="utf-8"))
        files = set(manifest[args.files]["files"]) if args.files in manifest else set(args.files.split(","))
        if args.files not in manifest and not load_records(data, files):
            raise SystemExit(f"--files {args.files}: no validated records in those files (batch ids look like B03)")
    if args.packets:
        start = max((int(p.name[1:3]) for p in vdir.glob("V[0-9][0-9].*")), default=0)
        for n, recs in enumerate(build_packets(load_records(data, files), args.n), start + 1):
            vid = f"V{n:02d}"
            (vdir / f"{vid}.md").write_text(packet_md(vid, recs), encoding="utf-8")
            (vdir / f"{vid}.keys.json").write_text(json.dumps([r["key"] for r in recs]) + "\n")
            print(f"{vid}: {len(recs)} findings")
        return
    keys_path = vdir / f"{args.check}.keys.json"
    records = load_records(data)
    if keys_path.exists():
        keys = set(json.loads(keys_path.read_text()))
        by_key = {r["key"]: r for r in records if r["key"] in keys}
    elif args.partial:
        by_key = {r["key"]: r for r in records}
        merged = data / "findings.json"  # QA verdicts may rule on script-generated rows too
        if merged.exists():
            for r in json.loads(merged.read_text(encoding="utf-8"))["rows"]:
                by_key.setdefault(r["key"], {**r, "kind": r.get("kind") or ("fsh" if r["file"].endswith(".fsh") else "page")})
    else:
        raise SystemExit(f"no {args.check}.keys.json; pass --partial for a consistency-pass or QA verdict file")
    open_decisions = {d["id"] for d in config.rulebook(cfg).get("decisions", []) if not d.get("team_decision")}
    errors = validate_verdicts(json.loads((vdir / f"{args.check}.json").read_text(encoding="utf-8")), by_key,
                               args.partial, open_decisions)
    print(f"{args.check}: OK" if not errors else "\n".join(errors))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
