import pytest

import prompt as gp


def test_reader_prompt_fills_every_placeholder_from_config_and_rulebook(cfg):
    out = gp.render("reader", cfg, packet="B01")
    assert "{{" not in out
    assert str(cfg["snapshot"]) in out and "B01" in out and "Example IG" in out
    assert 'Treat "recipient" as the retired name' in out        # rulebook domain_notes
    assert "findings.py" in out and "--batch B01" in out


def test_every_template_renders(cfg):
    for name in ("reader", "skeptic", "consistency", "qa-review", "rulebook-author", "themes-author"):
        assert "{{" not in gp.render(name, cfg, packet="B01")


def test_unfilled_placeholder_is_refused(tmp_path, cfg, monkeypatch):
    (tmp_path / "odd.md").write_text("Hello {{nobody}} and {{ig_name}}")
    monkeypatch.setattr(gp, "PROMPTS", tmp_path)
    with pytest.raises(ValueError, match="nobody"):
        gp.render("odd", cfg)


def test_missing_rulebook_renders_domain_notes_as_none(run, cfg):
    (run / "rulebook.yaml").unlink()
    assert "(from the rulebook author)\nnone" in gp.render("reader", cfg, packet="B01")


def test_brief_needing_a_packet_refuses_to_render_without_one(cfg):
    with pytest.raises(ValueError, match="packet"):
        gp.render("consistency", cfg)


def test_examples_placeholder_points_at_the_plugin_examples_directory(tmp_path, cfg, monkeypatch):
    (tmp_path / "odd.md").write_text("See {{examples}}/")
    monkeypatch.setattr(gp, "PROMPTS", tmp_path)
    assert gp.render("odd", cfg).rstrip("/").endswith("examples")


def test_domain_notes_list_renders_as_bullets(run, cfg):
    import yaml
    path = run / "rulebook.yaml"
    book = yaml.safe_load(path.read_text())
    book["domain_notes"] = ["first note", "second note"]
    path.write_text(yaml.safe_dump(book))
    out = gp.render("reader", cfg, packet="B01")
    assert "- first note\n- second note" in out


def test_braces_inside_domain_notes_are_not_placeholders(run, cfg):
    import yaml
    path = run / "rulebook.yaml"
    book = yaml.safe_load(path.read_text())
    book["domain_notes"] = "Leave {{x}} alone."
    path.write_text(yaml.safe_dump(book))
    assert "Leave {{x}} alone." in gp.render("reader", cfg, packet="B01")


def test_cli_without_packet_refuses_a_packet_brief(run):
    with pytest.raises(ValueError, match="packet"):
        gp.main(["consistency", "--run", str(run)])
