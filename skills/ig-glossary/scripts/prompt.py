"""Print an agent prompt with this run's paths and IG facts filled in."""
import argparse
import re
from pathlib import Path

import config

PROMPTS = Path(__file__).resolve().parent.parent / "prompts"
PLACEHOLDER = re.compile(r"\{\{(\w+)\}\}")


def render(name, cfg, **extra):
    book = config.rulebook(cfg) if (cfg["run_dir"] / "rulebook.yaml").exists() else {}
    notes = book.get("domain_notes") or "none"
    if isinstance(notes, list):
        notes = "\n".join(f"- {n}" for n in notes)
    values = {"ig_name": cfg["ig"]["name"], "tag": cfg["ig"]["tag"], "run_dir": str(cfg["run_dir"]),
              "snapshot": str(cfg["snapshot"]), "scripts": str(Path(__file__).resolve().parent),
              "glossary_page": cfg["ig"]["glossary_page"],
              "domain_notes": notes,
              "examples": str(Path(__file__).resolve().parents[3] / "examples"),
              "workbook": str(config.workbook_path(cfg)), "summary": str(config.summary_path(cfg)), **extra}
    text = (PROMPTS / f"{name}.md").read_text(encoding="utf-8")
    missing = sorted({m for m in PLACEHOLDER.findall(text) if m not in values})
    if missing:
        raise ValueError(f"{name}.md: unfilled placeholders {missing}")
    return PLACEHOLDER.sub(lambda m: str(values[m.group(1)]), text)


def main(argv=None):
    ap = config.add_run_arg(argparse.ArgumentParser(description=__doc__))
    ap.add_argument("name", choices=sorted(p.stem for p in PROMPTS.glob("*.md")))
    ap.add_argument("--packet", default="", help="packet id: Bnn for reader, Vnn for skeptic, the next free Vnn for consistency, Qnn for qa-review")
    args = ap.parse_args(argv)
    extra = {"packet": args.packet} if args.packet else {}
    print(render(args.name, config.load(args.run), **extra))


if __name__ == "__main__":
    main()
