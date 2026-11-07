"""Shared constants and JSONL helpers for the STU 3.1 glossary alignment analysis."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
BUILD = HERE / "_build"
SNAPSHOT = Path("/Users/corey/VSCodeProjects/fhir-sdoh-clinicalcare-3.0.0")

SNAPSHOT_TAG = "3.0.0"
PUBLISHED_BASE = "https://hl7.org/fhir/us/sdoh-clinicalcare/en/"

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
