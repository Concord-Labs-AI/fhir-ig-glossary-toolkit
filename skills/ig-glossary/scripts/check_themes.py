"""Check themes.yaml: shape, sizes, and that every term id exists in the rulebook."""
import argparse

import config

REQUIRED = ("id", "title", "terms", "glossary_says", "alignment_work", "work_package")


def problems(themes, book):
    probs, seen = [], set()
    term_ids = {t["id"] for t in book.get("terms", [])}
    for th in themes:
        tid = th.get("id", "?")
        if tid in seen:
            probs.append(f"duplicate theme id {tid}")
        seen.add(tid)
        for k in REQUIRED:
            if not th.get(k):
                probs.append(f"{tid}: {k} required")
        probs += [f"{tid}: unknown term {t}" for t in th.get("terms", []) if t not in term_ids]
        if th.get("size") not in ("S", "M", "L", "", None):
            probs.append(f"{tid}: size must be S, M or L")
    covered = {t for th in themes for t in th.get("terms", [])}
    flagging = {t["id"] for t in book.get("terms", []) if any(r.get("type") != "canonical" for r in t.get("rules", []))}
    probs += [f"{t}: term has flagging rules but no theme" for t in sorted(flagging - covered)]
    return probs


def main(argv=None):
    ap = config.add_run_arg(argparse.ArgumentParser(description=__doc__))
    args = ap.parse_args(argv)
    cfg = config.load(args.run)
    probs = problems(config.themes(cfg), config.rulebook(cfg))
    if probs:
        print("\n".join(f"- {p}" for p in probs))
        raise SystemExit(1)
    print("themes: OK")


if __name__ == "__main__":
    main()
