import subprocess
import sys
from pathlib import Path

import pytest
import yaml

import config


def test_load_resolves_paths_and_fills_defaults(run):
    cfg = config.load(run)
    assert cfg["run_dir"] == run and cfg["data"] == run / "data" and cfg["build"] == run / "_build"
    assert cfg["snapshot"] == run / "snapshot" and (cfg["snapshot"] / "sushi-config.yaml").exists()
    assert cfg["ig"]["published_base"].endswith("/")
    assert cfg["ig"]["historical_pages"] == ["changehistory.md"]
    assert cfg["batches"]["target_chars"] == 1000 and cfg["batches"]["overrides"] == []
    assert cfg["summary"]["outside_workbook"] == [] and cfg["summary"]["legend_examples"]
    assert config.workbook_path(cfg).name == "example-1.0.0-glossary-alignment-findings.xlsx"
    assert config.summary_path(cfg).name == "example-1.0.0-glossary-alignment-summary.html"


def test_rulebook_and_themes_load_from_the_run_dir(run):
    cfg = config.load(run)
    assert config.rulebook(cfg)["identifier_decision"] == "D-2"
    assert [t["id"] for t in config.themes(cfg)] == ["TH-ACTORS", "TH-ORGS"]


def test_missing_required_key_is_a_named_error(run):
    raw = yaml.safe_load((run / "config.yaml").read_text())
    del raw["ig"]["canonical"]
    (run / "config.yaml").write_text(yaml.safe_dump(raw))
    with pytest.raises(config.ConfigError, match="ig.canonical"):
        config.load(run)


def test_missing_config_file_is_a_named_error(tmp_path):
    with pytest.raises(config.ConfigError, match="config.yaml"):
        config.load(tmp_path)


def test_missing_snapshot_is_a_named_error(run):
    raw = yaml.safe_load((run / "config.yaml").read_text())
    raw["ig"]["snapshot"] = "nowhere"
    (run / "config.yaml").write_text(yaml.safe_dump(raw))
    with pytest.raises(config.ConfigError, match="snapshot"):
        config.load(run)


def test_each_load_gets_its_own_default_lists(run):
    raw = yaml.safe_load((run / "config.yaml").read_text())
    del raw["batches"]; del raw["acronyms"]; del raw["summary"]
    (run / "config.yaml").write_text(yaml.safe_dump(raw))
    first = config.load(run)
    first["batches"]["overrides"].append({"id": "B99"})
    first["ig"]["historical_pages"].append("x.md")
    second = config.load(run)
    assert second["batches"]["overrides"] == [] and second["ig"]["historical_pages"] == ["changehistory.md"]


def test_empty_artifact_prefixes_is_valid(run):
    raw = yaml.safe_load((run / "config.yaml").read_text())
    raw["ig"]["artifact_prefixes"] = []
    (run / "config.yaml").write_text(yaml.safe_dump(raw))
    assert config.load(run)["ig"]["artifact_prefixes"] == []


def test_missing_themes_file_is_a_named_error(run):
    (run / "themes.yaml").unlink()
    with pytest.raises(config.ConfigError, match="themes.yaml"):
        config.themes(config.load(run))


def test_missing_glossary_page_is_a_named_error(run):
    (run / "snapshot" / "input" / "pagecontent" / "glossary.md").unlink()
    with pytest.raises(config.ConfigError, match="ig.glossary_page"):
        config.load(run)


def test_acronym_entry_needs_long_and_term(run):
    raw = yaml.safe_load((run / "config.yaml").read_text())
    raw["acronyms"]["table"]["CBO"] = {"long": "community-based organization"}
    (run / "config.yaml").write_text(yaml.safe_dump(raw))
    with pytest.raises(config.ConfigError, match="acronyms.table.CBO needs long and term"):
        config.load(run)
    raw["acronyms"]["table"]["CBO"] = "community-based organization"
    (run / "config.yaml").write_text(yaml.safe_dump(raw))
    with pytest.raises(config.ConfigError, match="acronyms.table.CBO needs long and term"):
        config.load(run)


def test_outside_workbook_entry_needs_where_and_what(run):
    raw = yaml.safe_load((run / "config.yaml").read_text())
    raw["summary"]["outside_workbook"] = [{"where": "Home page"}]
    (run / "config.yaml").write_text(yaml.safe_dump(raw))
    with pytest.raises(config.ConfigError, match=r"summary.outside_workbook\[0\] needs where and what"):
        config.load(run)
    raw["summary"]["outside_workbook"] = [{"where": "Home page", "what": "Not scanned"}]
    (run / "config.yaml").write_text(yaml.safe_dump(raw))
    assert config.load(run)["summary"]["outside_workbook"][0]["what"] == "Not scanned"


def test_rulebook_without_decisions_means_none(run):
    raw = yaml.safe_load((run / "rulebook.yaml").read_text())
    raw.pop("decisions", None)
    (run / "rulebook.yaml").write_text(yaml.safe_dump(raw))
    assert config.rulebook(config.load(run))["decisions"] == []
    raw["decisions"] = None
    (run / "rulebook.yaml").write_text(yaml.safe_dump(raw))
    assert config.rulebook(config.load(run))["decisions"] == []


def test_blank_acronym_table_and_outside_workbook_load_as_empty(run):
    (run / "config.yaml").write_text(
        (run / "config.yaml").read_text().replace("  table:\n    CBO: {long: community-based organization, term: T-SSO}\n    SDOH: {long: social determinants of health, term: T-SDOH}\n", "  table:\n")
        + "  outside_workbook:\n")
    cfg = config.load(run)
    assert cfg["acronyms"]["table"] == {} and cfg["summary"]["outside_workbook"] == []


def test_mistyped_table_or_outside_workbook_is_a_named_error(run):
    raw = yaml.safe_load((run / "config.yaml").read_text())
    raw["acronyms"]["table"] = ["CBO"]
    (run / "config.yaml").write_text(yaml.safe_dump(raw))
    with pytest.raises(config.ConfigError, match="acronyms.table must be a mapping"):
        config.load(run)
    raw["acronyms"]["table"] = {}
    raw["summary"]["outside_workbook"] = "text"
    (run / "config.yaml").write_text(yaml.safe_dump(raw))
    with pytest.raises(config.ConfigError, match="summary.outside_workbook must be a list"):
        config.load(run)


def test_section_given_as_a_list_is_a_named_error(run):
    raw = yaml.safe_load((run / "config.yaml").read_text())
    raw["summary"] = ["a"]
    (run / "config.yaml").write_text(yaml.safe_dump(raw))
    with pytest.raises(config.ConfigError, match="config.yaml: summary must be a mapping"):
        config.load(run)


@pytest.mark.parametrize("script", ["extract.py", "merge.py"])
def test_a_config_error_ends_a_script_with_one_line_not_a_traceback(run, script):
    raw = yaml.safe_load((run / "config.yaml").read_text())
    del raw["ig"]["canonical"]
    (run / "config.yaml").write_text(yaml.safe_dump(raw))
    path = Path(config.__file__).with_name(script)
    res = subprocess.run([sys.executable, str(path), "--run", str(run)], capture_output=True, text=True)
    assert res.returncode == 1
    assert "Traceback" not in res.stderr
    assert res.stderr.strip().splitlines() == [f"{run.resolve() / 'config.yaml'} is missing ig.canonical"]
