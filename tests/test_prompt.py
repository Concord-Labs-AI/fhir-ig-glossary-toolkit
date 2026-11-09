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
