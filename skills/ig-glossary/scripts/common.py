"""Shared constants and JSONL helpers."""
import json
from pathlib import Path

ATTRIBUTION = "Method and tooling by Corey Smith, Concord Labs AI (corey@claystreetgroup.com)."

PROSE = "Prose"
ARTIFACT = "Artifact text"
IDENTIFIER = "Identifier"
DIAGRAM = "Diagram"
EXTERNAL = "External"
HISTORICAL = "Historical"
LOCKED_CLASSES = frozenset({IDENTIFIER, EXTERNAL, HISTORICAL})


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_jsonl(path):
    with Path(path).open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


# Transitional aliases removed in Task 8 once every script reads config.py.
HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
BUILD = HERE / "_build"
SNAPSHOT = Path("/Users/corey/VSCodeProjects/fhir-sdoh-clinicalcare-3.0.0")
SNAPSHOT_TAG = "3.0.0"
PUBLISHED_BASE = "https://hl7.org/fhir/us/sdoh-clinicalcare/en/"
