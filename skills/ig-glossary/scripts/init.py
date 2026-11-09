"""Write a run directory's config.yaml from an IG checkout's sushi-config.yaml (the user confirms it afterwards)."""
import argparse
import os
import re
import subprocess
from collections import Counter
from pathlib import Path

import yaml

ENTITY = re.compile(r"^(?:Profile|Extension|Logical|Resource|Instance|ValueSet|CodeSystem)\s*:\s*(\S+)", re.M)
LEADING = re.compile(r"^[A-Z][A-Z0-9]*?(?=[A-Z][a-z]|[-_.]|$)")


class InitError(Exception):
    pass


def artifact_prefixes(ig_dir):
    """The leading token most FSH artifact names share (e.g. SDOHCC from SDOHCCGoal, SDOHCC-ReferralSource)."""
    names = [m.group(1) for p in Path(ig_dir).glob("input/fsh/**/*.fsh")
             for m in ENTITY.finditer(p.read_text(encoding="utf-8", errors="replace"))]
    tokens = Counter(m.group(0) for n in names if (m := LEADING.match(n)) and len(m.group(0)) >= 2)
    if not names or not tokens:
        return []
    token, count = tokens.most_common(1)[0]
    return [token] if count / len(names) >= 0.5 else []


def git_tag(ig_dir):
    try:
        out = subprocess.run(["git", "-C", str(ig_dir), "describe", "--tags", "--exact-match"],
                             capture_output=True, text=True, check=True)
        return out.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def page_names(pages):
    names = []

    def walk(d):
        for k, v in (d or {}).items():
            if re.search(r"\.(md|xml|html)$", str(k)):
                names.append(str(k))
            if isinstance(v, dict):
                walk(v)
    walk(pages)
    return names


def infer(ig_dir):
    ig_dir = Path(ig_dir)
    path = ig_dir / "sushi-config.yaml"
    if not path.exists():
        raise InitError(f"{ig_dir} has no sushi-config.yaml — point init at the root of an IG checkout")
    sc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    canonical = str(sc.get("canonical", "")).rstrip("/")
    glossary = next((f"input/pagecontent/{p}" for p in page_names(sc.get("pages")) if "glossary" in p.lower()), "")
    return {
        "ig": {"name": str(sc.get("title") or sc.get("name") or ig_dir.name),
               "short": str(sc.get("id", "")).split(".")[-1] or ig_dir.name,
               "snapshot": os.path.relpath(ig_dir, Path.cwd()) if ig_dir.is_absolute() else str(ig_dir),
               "tag": git_tag(ig_dir) or str(sc.get("version", "")),
               "canonical": canonical,
               "artifact_prefixes": artifact_prefixes(ig_dir),
               "published_base": re.sub(r"^http://", "https://", canonical) + "/en/",
               "glossary_page": glossary},
        "acronyms": {"table": {}, "not_standalone": []},
        "batches": {"target_chars": 250000, "overrides": []},
        "summary": {"outside_workbook": [], "legend_examples": []},
    }


def write(run_dir, ig_dir, force=False):
    run_dir, ig_dir = Path(run_dir), Path(ig_dir)
    dest = run_dir / "config.yaml"
    if dest.exists() and not force:
        raise InitError(f"{dest}: config.yaml exists; pass --force to overwrite it")
    cfg = infer(ig_dir)
    cfg["ig"]["snapshot"] = os.path.relpath(ig_dir.resolve(), run_dir.resolve())
    run_dir.mkdir(parents=True, exist_ok=True)
    dest.write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return cfg


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("ig_dir", type=Path, help="root of the IG checkout at the tag under review")
    ap.add_argument("--run", type=Path, default=Path.cwd())
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args(argv)
    try:
        cfg = write(args.run, args.ig_dir, args.force)
    except InitError as err:
        raise SystemExit(str(err))
    print(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True))
    blanks = [k for k, v in cfg["ig"].items() if v in ("", [])]
    if blanks:
        print(f"Could not infer: {', '.join(blanks)} — fill these in config.yaml before continuing.")


if __name__ == "__main__":
    main()
