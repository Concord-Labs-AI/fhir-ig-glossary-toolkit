"""Partition the editable corpus into agent batches and write one packet per batch."""
import argparse
import fnmatch
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from common import DATA, LOCKED_CLASSES, read_jsonl

BATCHES = [  # first matching batch wins
    ("B06", "Profile intro pages", ["input/pagecontent/*-intro.md", "input/pagecontent/ImplementationGuide-*.md"]),
    ("B01", "Referral workflow", ["input/pagecontent/referral_workflow.md",
                                  "input/pagecontent/patient_coordination_workflow.md"]),
    ("B02", "Capacity, task status, referral for further assessment",
     ["input/pagecontent/capacity.md", "input/pagecontent/checking_task_status.md", "input/pagecontent/rffa.md"]),
    ("B03", "Self-referral, enrollment, app connection",
     ["input/pagecontent/self_referral.md", "input/pagecontent/enrollment.md",
      "input/pagecontent/connecting_applications_with_api_data_sources.md"]),
    ("B04", "Assessment instruments and value sets",
     ["input/pagecontent/assessment_instrument_support.md", "input/pagecontent/gravity_terminology.md"]),
    ("B05", "Background, glossary, and specification pages", ["input/pagecontent/*.md", "input/includes/*.md"]),
    # The CapabilityStatements are 70-200 KB each, so they are split three ways to fit one agent's context.
    ("B08", "CapabilityStatements: referral recipients and patient app",
     ["input/fsh/instances/SDOHCC-ReferralRecipient*.fsh", "input/fsh/instances/SDOHCC-PatientApp.fsh"]),
    ("B11", "CapabilityStatement: coordination platform", ["input/fsh/instances/SDOHCC-CoordinationPlatform.fsh"]),
    ("B12", "CapabilityStatement: referral source", ["input/fsh/instances/SDOHCC-ReferralSource.fsh"]),
    ("B09", "Example instances", ["input/fsh/instances/*"]),
    ("B07", "Profiles, extensions, value sets, code system, invariants", ["input/fsh/*", "input/resources/*"]),
    ("B10", "Diagrams, figures, navigation",
     ["input/images-source/*", "input/images/*", "sushi-config.yaml", "input/data/ig.yml"]),
]


def assign(file):
    for bid, _, patterns in BATCHES:
        if any(fnmatch.fnmatch(file, p) for p in patterns):
            return bid
    return None


def hit_id(h):
    key = f"{h['rule_id']}|{h['seg_id']}|{h['start']}|{h['match']}"
    return "H-" + hashlib.sha1(key.encode()).hexdigest()[:8]


def build_manifest(segments, hits):
    files, batch_hits = defaultdict(set), defaultdict(list)
    for s in segments:
        b = assign(s["file"])
        if b and s["change_class"] not in LOCKED_CLASSES:
            files[b].add(s["file"])
    for h in hits:
        b = assign(h["file"])
        if b and h["type"] != "canonical" and not h["locked"]:
            batch_hits[b].append({**h, "hit_id": hit_id(h)})
    ids = [h["hit_id"] for hs in batch_hits.values() for h in hs]
    if len(ids) != len(set(ids)):
        raise ValueError("hit id collision; lengthen hit_id")
    manifest = {}
    for bid, title, _ in BATCHES:
        if files[bid] or batch_hits[bid]:
            manifest[bid] = {"title": title, "files": sorted(files[bid]),
                             "hits": sorted(batch_hits[bid], key=lambda h: (h["file"], h["line"] or 0, h["start"] or 0))}
    return manifest


def packet_md(bid, entry):
    lines = [f"# Batch {bid} — {entry['title']}", "",
             "Read every file below in full (paths are relative to the snapshot root).", "", "## Files", ""]
    lines += [f"- `{f}`" for f in entry["files"]]
    lines += ["", f"## Candidate hits ({len(entry['hits'])}) — give every one a disposition", ""]
    current = None
    for h in entry["hits"]:
        if h["file"] != current:
            current = h["file"]
            lines += ["", f"### `{current}`", "", "| Hit | Line | Rule | Decision | Context |", "|---|---|---|---|---|"]
        context = h["context"].replace("|", "\\|")
        lines.append(f"| {h['hit_id']} | {h['line'] or 'figure'} | {h['rule_id']} | {h['decision'] or ''} | {context} |")
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", type=Path, default=DATA)
    args = ap.parse_args(argv)
    manifest = build_manifest(read_jsonl(args.data / "segments.jsonl"), read_jsonl(args.data / "hits.jsonl"))
    out = args.data / "batches"
    out.mkdir(parents=True, exist_ok=True)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    for bid, entry in manifest.items():
        (out / f"{bid}.md").write_text(packet_md(bid, entry), encoding="utf-8")
        print(f"{bid}: {len(entry['files']):3} files, {len(entry['hits']):4} hits — {entry['title']}")


if __name__ == "__main__":
    main()
