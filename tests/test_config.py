import pytest

from radar import config


def test_committed_radar_yaml_matches_the_documented_defaults_for_the_account_limits():
    cfg = config.load(path=config.ROOT / "radar.yaml", env={})
    assert cfg["models"]["checker"][0] == "groq/openai/gpt-oss-120b"      # an independent family first; Mistral reports a quota of 0 for this key
    assert cfg["pace_seconds"] == 45 and config.DEFAULTS["pace_seconds"] == 45
    assert cfg["langs"] == ["vi"] and cfg["models"]["writer"][0] == "google/gemini-flash-latest"
    assert cfg["models"] == config.DEFAULTS["models"]                         # yaml and code defaults cannot drift apart


def test_every_role_has_fallbacks_in_more_than_one_family_so_one_overloaded_model_cannot_stop_a_run():
    from radar.llm import family
    models = config.load(path=config.ROOT / "radar.yaml", env={})["models"]
    assert len(models["writer"]) >= 3 and len(models["checker"]) >= 3
    assert len({family(m) for m in models["writer"]}) >= 2 and len({family(m) for m in models["checker"]}) >= 2
    for writer in models["writer"]:      # whichever model wrote the draft, some checker is of another family
        assert [m for m in models["checker"] if family(m) != family(writer)], writer


def test_environment_overrides_win_without_editing_the_file():
    cfg = config.load(path=config.ROOT / "none.yaml", env={"RADAR_LANGS": "vi,en", "RADAR_PICKS": "2",
                                                          "RADAR_MODELS_CHECKER": "mistral/a groq/b"})
    assert cfg["langs"] == ["vi", "en"] and cfg["picks_per_run"] == 2 and cfg["models"]["checker"] == ["mistral/a", "groq/b"]


def test_the_run_time_budget_is_configured_in_both_places_and_must_be_positive():
    import pytest
    cfg = config.load(path=config.ROOT / "radar.yaml", env={})
    assert cfg["max_run_minutes"] == 35 == config.DEFAULTS["max_run_minutes"]
    with pytest.raises(ValueError, match="max_run_minutes"):
        config.validate({**config.DEFAULTS, "max_run_minutes": 0})


def test_a_gemini_draft_is_checked_by_gpt_oss_first_and_a_gpt_oss_draft_by_another_family_with_gpt_oss_last():
    from radar.write import checker_pool
    models = config.load(path=config.ROOT / "radar.yaml", env={})["models"]
    assert checker_pool(models["checker"], "google/gemini-flash-latest")[:2] == ["groq/openai/gpt-oss-120b", "groq/openai/gpt-oss-20b"]
    assert checker_pool(models["checker"], "groq/openai/gpt-oss-120b") == [
        "mistral/mistral-small-2603", "google/gemini-flash-lite-latest", "groq/openai/gpt-oss-120b", "groq/openai/gpt-oss-20b"]    # same family only as a last resort


def test_a_quick_start_just_past_8000_characters_still_reaches_the_prompt_and_the_cap_stays_well_under_the_checker_budget():
    from radar import facts
    cfg = config.load(path=config.ROOT / "radar.yaml", env={})
    limit = cfg["readme_max_chars"]
    readme = "# Tool\n\n" + "\n".join(f"Feature {i}: does one more useful thing in the pipeline." for i in range(150)) \
        + "\n\n## Quick Start\n\n```bash\n./setup.sh\npip install -r requirements.txt\n```\n\n" + "More text. " * 4000
    start = readme.index("./setup.sh")
    assert 8000 < start < limit                                  # the case the old cap lost: the commands sit past 8,000
    cut = facts.clean_readme(readme, limit)
    assert "./setup.sh" in cut and "pip install -r requirements.txt" in cut and len(cut) <= limit
    assert limit == config.DEFAULTS["readme_max_chars"] <= 16000  # a bigger cap must be a decision about the 20,000 tokens/minute budget


def test_rising_and_pacing_defaults_validation_and_override():
    cfg = config.load(path=config.ROOT / "none.yaml", env={})
    assert cfg["rising"] == {"enabled": True, "slots": 1, "created_within_days": 120, "min_stars": 300}
    assert cfg["search_interval_seconds"] == 2.1 and cfg["history_days"] == 60
    assert config.load(path=config.ROOT / "none.yaml", env={"RADAR_SEARCH_INTERVAL": "0"})["search_interval_seconds"] == 0.0
    for bad in ({"rising": {"slots": 4}}, {"rising": {"created_within_days": 0}}, {"history_days": 10}, {"search_interval_seconds": -1}):
        merged = config.deep_merge(config.DEFAULTS, bad)
        with pytest.raises(ValueError):
            config.validate(merged)
