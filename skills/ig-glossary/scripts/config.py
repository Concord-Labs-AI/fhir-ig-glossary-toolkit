"""Load the run directory's config.yaml: the whole IG-specific surface of a run."""
from pathlib import Path

import yaml

REQUIRED_IG = ["name", "short", "snapshot", "tag", "canonical", "artifact_prefixes", "published_base", "glossary_page"]
DEFAULTS = {
    "ig": {"historical_pages": ["changehistory.md"]},
    "acronyms": {"table": {}, "not_standalone": []},
    "batches": {"target_chars": 250000, "overrides": []},
    "summary": {"intro": "", "outside_workbook": [], "legend_examples": [], "names_kept_note": "",
                "build_note": "", "locked_examples": ""},
}


class ConfigError(Exception):
    pass


def load(run_dir=None):
    run_dir = Path(run_dir or Path.cwd()).resolve()
    path = run_dir / "config.yaml"
    if not path.exists():
        raise ConfigError(f"no config.yaml in {run_dir} (run init.py <ig-path> first)")
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    cfg = {}
    for section, defaults in DEFAULTS.items():
        cfg[section] = {**defaults, **(raw.get(section) or {})}
    missing = [k for k in REQUIRED_IG if not cfg["ig"].get(k)]
    if missing:
        raise ConfigError("config.yaml is missing " + ", ".join(f"ig.{k}" for k in missing))
    snapshot = (run_dir / cfg["ig"]["snapshot"]).resolve()
    if not (snapshot / "sushi-config.yaml").exists():
        raise ConfigError(f"ig.snapshot {snapshot} has no sushi-config.yaml")
    cfg["ig"]["published_base"] = cfg["ig"]["published_base"].rstrip("/") + "/"
    cfg["ig"]["canonical"] = cfg["ig"]["canonical"].rstrip("/")
    cfg["ig"]["tag"] = str(cfg["ig"]["tag"])
    cfg.update(run_dir=run_dir, data=run_dir / "data", build=run_dir / "_build", snapshot=snapshot)
    return cfg


def rulebook(cfg):
    return yaml.safe_load((cfg["run_dir"] / "rulebook.yaml").read_text(encoding="utf-8"))


def themes(cfg):
    return yaml.safe_load((cfg["run_dir"] / "themes.yaml").read_text(encoding="utf-8"))["themes"]


def _stem(cfg):
    return f"{cfg['ig']['short']}-{cfg['ig']['tag']}-glossary-alignment"


def workbook_path(cfg):
    return cfg["build"] / f"{_stem(cfg)}-findings.xlsx"


def summary_path(cfg):
    return cfg["build"] / f"{_stem(cfg)}-summary.html"


def add_run_arg(parser):
    parser.add_argument("--run", type=Path, default=None, help="run directory (default: current directory)")
    return parser
