"""Print an agent prompt with this run's paths and IG facts filled in."""
import argparse
import re
from pathlib import Path

import config

PROMPTS = Path(__file__).resolve().parent.parent / "prompts"
PLACEHOLDER = re.compile(r"\{\{(\w+)\}\}")


def render(name, cfg, **extra):
    book = config.rulebook(cfg) if (cfg["run_dir"] / "rulebook.yaml").exists() else {}
    values = {"ig_name": cfg["ig"]["name"], "tag": cfg["ig"]["tag"], "run_dir": str(cfg["run_dir"]),
              "snapshot": str(cfg["snapshot"]), "scripts": str(Path(__file__).resolve().parent),
              "glossary_page": cfg["ig"]["glossary_page"],
              "domain_notes": book.get("domain_notes") or "none",
              "workbook": str(config.workbook_path(cfg)), "summary": str(config.summary_path(cfg)), **extra}
    text = (PROMPTS / f"{name}.md").read_text(encoding="utf-8")
    out = PLACEHOLDER.sub(lambda m: str(values[m.group(1)]) if m.group(1) in values else m.group(0), text)
    left = sorted(set(PLACEHOLDER.findall(out)))
    if left:
        raise ValueError(f"{name}.md: unfilled placeholders {left}")
    return out


def main(argv=None):
    ap = config.add_run_arg(argparse.ArgumentParser(description=__doc__))
    ap.add_argument("name", choices=sorted(p.stem for p in PROMPTS.glob("*.md")))
    ap.add_argument("--packet", default="", help="B03, V02, … for the reader and skeptic prompts")
    args = ap.parse_args(argv)
    print(render(args.name, config.load(args.run), packet=args.packet))


if __name__ == "__main__":
    main()
