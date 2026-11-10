"""Score a candidate model's reader or skeptic output against the reference run (model-dependency experiment)."""
import argparse
import json
from collections import Counter
from pathlib import Path

import config
from common import read_jsonl
from findings import Corpus, batch_entry, validate_batch
from verify import packet_md


def load_candidate(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as err:
        raise SystemExit(f"{path}: cannot read candidate output ({err})")


def same_place(a, b):
    if a["key"] == b["key"]:
        return True
    return (a["file"] == b["file"] and a.get("start") is not None and b.get("start") is not None
            and a["start"] < b["end"] and b["start"] < a["end"])


def score_reader(candidate, entry, cfg, ref_kept, ref_rejected):
    corpus = Corpus(cfg["snapshot"], read_jsonl(cfg["data"] / "segments.jsonl"))
    records, errors = validate_batch(candidate, entry, corpus, config.rulebook(cfg))
    files = set(entry["files"])
    kept = [r for r in ref_kept if r["file"] in files and r.get("source", "agent") == "agent"]
    rejected = [r for r in ref_rejected if r["file"] in files]
    found = [k for k in kept if any(same_place(k, r) for r in records)]
    hits_rej = [r for r in records if any(same_place(r, x) for x in rejected)]
    unmatched = [r for r in records if not any(same_place(r, x) for x in kept + rejected)]
    pending = {h["hit_id"] for h in entry["hits"] if h.get("decision")}
    violations = [f for f in candidate.get("findings", []) if not f.get("decision") and set(f.get("hits", [])) & pending]
    proposed = len(candidate.get("findings", []))
    return ({"proposed": proposed, "valid": len(records), "validity": len(records) / proposed if proposed else None,
             "reference_kept": len(kept), "recall": len(found) / len(kept) if kept else None,
             "matches_rejected": len(hits_rej), "unmatched": len(unmatched),
             "precision_proxy": 1 - (len(hits_rej) + len(unmatched)) / len(records) if records else None,
             "pending_violations": len(violations), "validation_errors": errors[:20]}, unmatched)


def score_skeptic(candidate, reference_files):
    ref = {}
    for verdicts in reference_files:          # file order: a later pass overrides an earlier one, as merge does
        for v in verdicts:
            ref[v["key"]] = v["verdict"]
    pairs = Counter(f"{ref[c['key']]}/{c['verdict']}" for c in candidate if c["key"] in ref)
    compared = sum(pairs.values())
    agree = sum(n for k, n in pairs.items() if k.split("/")[0] == k.split("/")[1])
    return {"compared": compared, "agreement": agree / compared if compared else None, "pairs": dict(pairs)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("reader", help="score data/agent/<packet>.json in a candidate run against the reference run")
    r.add_argument("--reference", type=Path, required=True, help="reference run dir (has data/findings.json, data/rejected.json)")
    r.add_argument("--candidate", type=Path, required=True, help="candidate run dir (copy of base + its agent output)")
    r.add_argument("--packet", required=True)
    r.add_argument("--spotcheck-out", type=Path, help="write a skeptic packet of the unmatched findings (max 20) here")
    s = sub.add_parser("skeptic", help="compare a candidate verdict file with the reference verdict files")
    s.add_argument("--reference", type=Path, required=True)
    s.add_argument("--candidate", type=Path, required=True, help="the candidate Vnn.json")
    s.add_argument("--through", default="V07", help="last reference verdict file to include (default V07: before QA)")
    args = ap.parse_args(argv)
    if args.cmd == "reader":
        cfg = config.load(args.candidate)
        manifest = json.loads((cfg["data"] / "batches" / "manifest.json").read_text(encoding="utf-8"))
        candidate = load_candidate(cfg["data"] / "agent" / f"{args.packet}.json")
        kept = json.loads((args.reference / "data" / "findings.json").read_text(encoding="utf-8"))["rows"]
        rejected = json.loads((args.reference / "data" / "rejected.json").read_text(encoding="utf-8"))
        result, unmatched = score_reader(candidate, batch_entry(manifest, args.packet, candidate), cfg, kept, rejected)
        meta = cfg["data"] / "agent" / f"{args.packet}.meta.json"
        if meta.exists():
            result["meta"] = json.loads(meta.read_text())
        out = cfg["data"] / "scores"
        out.mkdir(exist_ok=True)
        (out / f"{args.packet}.json").write_text(json.dumps(result, indent=1) + "\n")
        if args.spotcheck_out:
            args.spotcheck_out.mkdir(parents=True, exist_ok=True)
            sample = sorted(unmatched, key=lambda r: r["key"])[:20]
            (args.spotcheck_out / f"SPOT-{args.packet}.md").write_text(packet_md(f"SPOT-{args.packet}", sample), encoding="utf-8")
            (args.spotcheck_out / f"SPOT-{args.packet}.keys.json").write_text(json.dumps([r["key"] for r in sample]) + "\n")
        print(json.dumps(result, indent=1))
    else:
        files = sorted(p for p in (args.reference / "data" / "verify").glob("V[0-9][0-9].json") if p.stem <= args.through)
        reference = [json.loads(p.read_text(encoding="utf-8")) for p in files]
        print(json.dumps(score_skeptic(load_candidate(args.candidate), reference), indent=1))


if __name__ == "__main__":
    main()
