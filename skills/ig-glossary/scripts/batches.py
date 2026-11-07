"""Partition the editable corpus into agent packets sized to one agent's context, and write one packet per batch."""
import argparse
import fnmatch
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import config
from common import LOCKED_CLASSES, read_jsonl

# Directories are packed in this order and never share a packet; a file not under any of them goes last.
GROUP_ORDER = ["input/pagecontent", "input/includes", "input/fsh/profiles", "input/fsh/extensions",
               "input/fsh/valuesets", "input/fsh/codesystems", "input/fsh/instances", "input/fsh",
               "input/resources", "input/images-source", "input/images", "input/data"]


def group_of(file):
    for g in GROUP_ORDER:
        if file.startswith(g + "/"):
            return g
    return "other"


def file_sizes(segments, snapshot):
    """Characters an agent must read per editable file: the whole file, or the transcribed labels for a figure."""
    sizes = {}
    for s in segments:
        if s["change_class"] in LOCKED_CLASSES:
            continue
        if s["start"] is None:
            sizes[s["file"]] = (sizes.get(s["file"]) or 0) + len(s["text"])
        else:
            sizes.setdefault(s["file"], None)
    for f, v in sizes.items():
        if v is None:
            sizes[f] = len((Path(snapshot) / f).read_text(encoding="utf-8"))
    return sizes


def plan_batches(sizes, target_chars, overrides):
    """{bid: {title, files}}. Overrides first (first match wins), then a greedy pack per directory group."""
    if not sizes:
        raise ValueError("no editable files to batch")
    plan, left = {}, dict(sizes)
    for o in overrides:
        files = sorted(f for f in left if any(fnmatch.fnmatch(f, p) for p in o["globs"]))
        if not files:
            raise ValueError(f"override {o['id']} matches no file")
        plan[o["id"]] = {"title": o["title"], "files": files}
        for f in files:
            del left[f]
    counter = [1]

    def next_id():
        while f"B{counter[0]:02d}" in plan:
            counter[0] += 1
        bid = f"B{counter[0]:02d}"
        counter[0] += 1
        return bid

    def flush(group, packet):
        plan[next_id()] = {"title": f"{group}: {Path(packet[0]).name} … {Path(packet[-1]).name}"
                           if len(packet) > 1 else f"{group}: {Path(packet[0]).name}", "files": packet}

    groups = sorted({group_of(f) for f in left}, key=lambda g: GROUP_ORDER.index(g) if g in GROUP_ORDER else len(GROUP_ORDER))
    for group in groups:
        packet, size = [], 0
        for f in sorted((f for f in left if group_of(f) == group), key=lambda f: (-(sizes[f] > target_chars), f)):
            if packet and size + sizes[f] > target_chars:
                flush(group, packet)
                packet, size = [], 0
            packet.append(f)
            size += sizes[f]
        if packet:
            flush(group, packet)
    return plan


def hit_id(h):
    key = f"{h['rule_id']}|{h['seg_id']}|{h['start']}|{h['match']}"
    return "H-" + hashlib.sha1(key.encode()).hexdigest()[:8]


def build_manifest(segments, hits, plan):
    where = {f: bid for bid, e in plan.items() for f in e["files"]}
    files, batch_hits = defaultdict(set), defaultdict(list)
    for s in segments:
        b = where.get(s["file"])
        if b and s["change_class"] not in LOCKED_CLASSES:
            files[b].add(s["file"])
    for h in hits:
        b = where.get(h["file"])
        if b and h["type"] != "canonical" and not h["locked"]:
            batch_hits[b].append({**h, "hit_id": hit_id(h)})
    ids = [h["hit_id"] for hs in batch_hits.values() for h in hs]
    if len(ids) != len(set(ids)):
        raise ValueError("hit id collision; lengthen hit_id")
    manifest = {}
    for bid in sorted(plan):
        if files[bid] or batch_hits[bid]:
            manifest[bid] = {"title": plan[bid]["title"], "files": sorted(files[bid]),
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
    ap = config.add_run_arg(argparse.ArgumentParser(description=__doc__))
    args = ap.parse_args(argv)
    cfg = config.load(args.run)
    segments = read_jsonl(cfg["data"] / "segments.jsonl")
    plan = plan_batches(file_sizes(segments, cfg["snapshot"]), cfg["batches"]["target_chars"], cfg["batches"]["overrides"])
    manifest = build_manifest(segments, read_jsonl(cfg["data"] / "hits.jsonl"), plan)
    out = cfg["data"] / "batches"
    out.mkdir(parents=True, exist_ok=True)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    for bid, entry in manifest.items():
        (out / f"{bid}.md").write_text(packet_md(bid, entry), encoding="utf-8")
        print(f"{bid}: {len(entry['files']):3} files, {len(entry['hits']):4} hits — {entry['title']}")


if __name__ == "__main__":
    main()
