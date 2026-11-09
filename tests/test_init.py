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
    (fsh / "a.fsh").write_text("Profile: Alpha\nProfile: Beta\nProfile: Gamma\n")
    assert gi.artifact_prefixes(tmp_path) == []


def test_write_refuses_without_sushi_config_and_without_force(run, tmp_path):
    with pytest.raises(gi.InitError, match="sushi-config.yaml"):
        gi.infer(tmp_path)
    with pytest.raises(gi.InitError, match="config.yaml exists"):
        gi.write(run, run / "snapshot", force=False)
    gi.write(run, run / "snapshot", force=True)
    assert yaml.safe_load((run / "config.yaml").read_text())["ig"]["snapshot"] == "snapshot"
