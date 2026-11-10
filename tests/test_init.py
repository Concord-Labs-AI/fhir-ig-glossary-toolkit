import re
import subprocess

import pytest
import yaml

import init as gi


def test_infers_the_ig_facts_from_sushi_config(run):
    cfg = gi.infer(run / "snapshot")
    assert cfg["ig"]["name"] == "Example IG" and cfg["ig"]["short"] == "example"
    assert cfg["ig"]["canonical"] == "http://example.org/fhir/example"
    assert cfg["ig"]["published_base"] == "https://example.org/fhir/example/en/"
    assert cfg["ig"]["tag"] == "1.0.0"
    assert cfg["ig"]["glossary_page"] == "input/pagecontent/glossary.md"
    assert cfg["ig"]["artifact_prefixes"] == ["XYZ"]
    assert cfg["acronyms"] == {"table": {}, "not_standalone": []}
    assert cfg["batches"]["target_chars"] == 250000


def test_artifact_prefix_is_the_common_leading_token(tmp_path):
    fsh = tmp_path / "input" / "fsh"
    fsh.mkdir(parents=True)
    (fsh / "a.fsh").write_text("Profile: SDOHCCGoal\nInstance: SDOHCC-ReferralSource\nValueSet: SDOHCCCategory\n")
    (fsh / "b.fsh").write_text("Profile: USCorePatient\n")
    assert gi.artifact_prefixes(tmp_path) == ["SDOHCC"]
    (fsh / "c.fsh").write_text("Instance: example-goal\nInstance: example-referral\nInstance: sample-task\n")
    assert gi.artifact_prefixes(tmp_path) == ["SDOHCC"]
    (fsh / "c.fsh").unlink()
    (fsh / "a.fsh").write_text("Profile: USCorePatient\n")
    (fsh / "b.fsh").unlink()
    assert gi.artifact_prefixes(tmp_path) == ["US"]
    (fsh / "a.fsh").write_text("Profile: Alpha\nProfile: Beta\nProfile: Gamma\n")
    assert gi.artifact_prefixes(tmp_path) == []


def test_write_refuses_without_sushi_config_and_without_force(run, tmp_path):
    with pytest.raises(gi.InitError, match="sushi-config.yaml"):
        gi.infer(tmp_path)
    with pytest.raises(gi.InitError, match="config.yaml exists"):
        gi.write(run, run / "snapshot", force=False)
    gi.write(run, run / "snapshot", force=True)
    assert yaml.safe_load((run / "config.yaml").read_text())["ig"]["snapshot"] == "snapshot"


def test_main_warns_about_a_short_artifact_prefix(run, capsys, monkeypatch):
    gi.main([str(run / "snapshot"), "--run", str(run), "--force"])
    assert "Artifact prefix 'XYZ' is short" in capsys.readouterr().out
    monkeypatch.setattr(gi, "artifact_prefixes", lambda ig_dir: ["SDOHCC"])
    gi.main([str(run / "snapshot"), "--run", str(run), "--force"])
    assert "is short" not in capsys.readouterr().out


def test_glossary_page_is_left_blank_when_no_file_exists(run):
    (run / "snapshot" / "input" / "pagecontent" / "glossary.md").unlink()
    assert gi.infer(run / "snapshot")["ig"]["glossary_page"] == ""


def test_glossary_page_falls_back_to_input_pages(run):
    pages = run / "snapshot" / "input" / "pages"
    pages.mkdir()
    (run / "snapshot" / "input" / "pagecontent" / "glossary.md").rename(pages / "glossary.md")
    assert gi.infer(run / "snapshot")["ig"]["glossary_page"] == "input/pages/glossary.md"


def test_glossary_page_is_found_without_a_pages_block(run):
    sc = run / "snapshot" / "sushi-config.yaml"
    sc.write_text(re.sub(r"pages:\n(?:  .*\n)+", "", sc.read_text()))
    assert "pages:" not in sc.read_text()
    assert gi.infer(run / "snapshot")["ig"]["glossary_page"] == "input/pagecontent/glossary.md"


def test_glossary_page_absent_from_the_pages_block_is_not_inferred(run):
    sc = run / "snapshot" / "sushi-config.yaml"
    sc.write_text(sc.read_text().replace("  glossary.md:\n    title: Glossary\n", ""))
    assert gi.infer(run / "snapshot")["ig"]["glossary_page"] == ""


def test_git_tag_is_none_outside_a_repository(tmp_path):
    if subprocess.run(["git", "-C", str(tmp_path), "rev-parse"], capture_output=True).returncode == 0:
        pytest.skip("tmp_path is inside a git repository on this machine")
    assert gi.git_tag(tmp_path) is None
