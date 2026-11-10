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


def read_reader_candidate(path):
    """(candidate, None), or (None, status) when the packet was never delivered or is unusable."""
    path = Path(path)
    if not path.exists():
        return None, "did not complete"
    try:
        out = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None, "malformed"
    if not isinstance(out, dict) or not isinstance(out.get("findings"), list):
        return None, "malformed"
    return out, None


def incomplete_result(status, reference_kept):
    return {"status": status, "proposed": 0, "valid": 0, "validity": 0.0, "errors": 0,
            "reference_kept": reference_kept, "recall": 0.0, "matches_rejected": 0, "unmatched": 0,
            "precision_proxy": None, "pending_violations": 0, "validation_errors": []}


def overlap(a, b):
    if a.get("start") is None or b.get("start") is None:
        return 0
    return min(a["end"], b["end"]) - max(a["start"], b["start"])


def same_place(a, b):
    if a["key"] == b["key"]:
        return True
    return a["file"] == b["file"] and overlap(a, b) > 0


def match_one_to_one(kept, records):
    """Greedy: exact key first, then largest overlap. Returns (matched pairs, records left unmatched)."""
    pairs = sorted(((a["key"] == r["key"], overlap(a, r), i, j) for i, a in enumerate(kept)
                    for j, r in enumerate(records) if same_place(a, r)), reverse=True)
    used_k, used_r, matched = set(), set(), []
    for _, _, i, j in pairs:
        if i not in used_k and j not in used_r:
            used_k.add(i)
            used_r.add(j)
            matched.append((kept[i], records[j]))
    return matched, [r for j, r in enumerate(records) if j not in used_r]


def overlapping(records):
    """Records that overlap another record in the same file (validate_batch reports these as errors)."""
    bad = set()
    spans = sorted((r["file"], r["start"], i) for i, r in enumerate(records) if r["start"] is not None)
    for (fa, _, i), (fb, _, j) in zip(spans, spans[1:]):
        if fa == fb and records[j]["start"] < records[i]["end"]:
            bad |= {i, j}
    return bad


def score_reader(candidate, entry, cfg, ref_kept, ref_rejected):
    corpus = Corpus(cfg["snapshot"], read_jsonl(cfg["data"] / "segments.jsonl"))
    records, errors = validate_batch(candidate, entry, corpus, config.rulebook(cfg))
    bad = overlapping(records)
    records = [r for i, r in enumerate(records) if i not in bad]
    files = set(entry["files"])
    kept = [r for r in ref_kept if r["file"] in files and r.get("source", "agent") == "agent"]
    rejected = [r for r in ref_rejected if r["file"] in files]
    matched, rest = match_one_to_one(kept, records)
    hits_rej = [r for r in rest if any(same_place(r, x) for x in rejected)]
    unmatched = [r for r in rest if not any(same_place(r, x) for x in rejected)]
    pending = {h["hit_id"] for h in entry["hits"] if h.get("decision")}
    violations = [f for f in candidate.get("findings", []) if not f.get("decision") and set(f.get("hits", [])) & pending]
    proposed = len(candidate.get("findings", []))
    return ({"status": "ok", "proposed": proposed, "valid": len(records), "validity": len(records) / proposed if proposed else 0.0,
             "errors": len(errors),
             "reference_kept": len(kept), "recall": len(matched) / len(kept) if kept else None,
             "matches_rejected": len(hits_rej), "unmatched": len(unmatched),
             "precision_proxy": len(matched) / len(records) if records else None,
             "pending_violations": len(violations), "validation_errors": errors[:20]}, unmatched)


def load_keys(candidate_path):
    keys_path = Path(candidate_path).with_suffix(".keys.json")
    if not keys_path.exists():
        raise SystemExit(f"{keys_path}: missing. Build the candidate packet with verify.py --packets --n 1 --files <batch> "
                         "in the candidate run so the keys file sits beside the verdict file")
    return json.loads(keys_path.read_text(encoding="utf-8"))


def score_skeptic(candidate, reference_files, keys):
    """Every packet key is scored. No reference verdict means the reference confirmed it by default."""
    ref = {}
    for verdicts in reference_files:          # file order: a later pass overrides an earlier one, as merge does
        for v in verdicts:
            ref[v["key"]] = v
    cand = {v["key"]: v for v in candidate}
    confusion, agree, explicit, explicit_agree = Counter(), 0, 0, 0
    same = different = 0
    for k in keys:
        r = ref.get(k, {"verdict": "confirm"})["verdict"]
        c = cand[k]["verdict"] if k in cand else "missing"
        confusion[f"{r}→{c}"] += 1
        agree += r == c
        if k in ref:
            explicit += 1
            explicit_agree += r == c
        if r == c == "revise":
            if ref[k].get("replace") == cand[k].get("replace"):
                same += 1
            else:
                different += 1
    n = len(keys)
    return {"compared": n, "agreement": agree / n if n else None,
            "agreement_explicit": explicit_agree / explicit if explicit else None,
            "confusion": dict(confusion), "revise_same_replace": same, "revise_different_replace": different}


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
    s.add_argument("--candidate", type=Path, required=True, help="the candidate Vnn.json; Vnn.keys.json must sit beside it")
    s.add_argument("--through", default="V07", help="last reference verdict file to include (default V07: before QA)")
    args = ap.parse_args(argv)
    if args.cmd == "reader":
        cfg = config.load(args.candidate)
        manifest = json.loads((cfg["data"] / "batches" / "manifest.json").read_text(encoding="utf-8"))
        kept = json.loads((args.reference / "data" / "findings.json").read_text(encoding="utf-8"))["rows"]
        rejected = json.loads((args.reference / "data" / "rejected.json").read_text(encoding="utf-8"))
        candidate, why = read_reader_candidate(cfg["data"] / "agent" / f"{args.packet}.json")
        if candidate is None:
            n_kept = sum(1 for r in kept if r["file"] in set(manifest[args.packet]["files"]) and r.get("source", "agent") == "agent")
            result, unmatched = incomplete_result(why, n_kept), []
        else:
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
        print(json.dumps(score_skeptic(load_candidate(args.candidate), reference, load_keys(args.candidate)), indent=1))


if __name__ == "__main__":
    main()
