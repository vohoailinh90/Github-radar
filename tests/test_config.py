from radar import config


def test_committed_radar_yaml_matches_the_documented_defaults_for_the_account_limits():
    cfg = config.load(path=config.ROOT / "radar.yaml", env={})
    assert cfg["models"]["checker"][0] == "groq/meta-llama/llama-4-scout-17b-16e-instruct"      # an independent family first; Mistral reports a quota of 0 for this key
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


def test_a_gemini_draft_is_checked_by_llama_first_and_a_llama_draft_by_another_family_with_llama_last():
    from radar.write import checker_pool
    models = config.load(path=config.ROOT / "radar.yaml", env={})["models"]
    assert checker_pool(models["checker"], "google/gemini-flash-latest")[:2] == ["groq/meta-llama/llama-4-scout-17b-16e-instruct", "groq/meta-llama/llama-4-maverick-17b-128e-instruct"]
    assert checker_pool(models["checker"], "groq/meta-llama/llama-4-scout-17b-16e-instruct") == [
        "mistral/mistral-small-2603", "google/gemini-flash-lite-latest", "groq/meta-llama/llama-4-scout-17b-16e-instruct", "groq/meta-llama/llama-4-maverick-17b-128e-instruct"]    # same family only as a last resort
