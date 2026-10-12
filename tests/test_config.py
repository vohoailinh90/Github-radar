from radar import config


def test_committed_radar_yaml_matches_the_documented_defaults_for_the_account_limits():
    cfg = config.load(path=config.ROOT / "radar.yaml", env={})
    assert cfg["models"]["checker"] == ["mistral/mistral-small-2603"]       # the name this account lists under "Limites"
    assert cfg["pace_seconds"] == 45 and config.DEFAULTS["pace_seconds"] == 45
    assert cfg["langs"] == ["vi"] and cfg["models"]["writer"] == ["google/gemini-flash-latest"]


def test_environment_overrides_win_without_editing_the_file():
    cfg = config.load(path=config.ROOT / "none.yaml", env={"RADAR_LANGS": "vi,en", "RADAR_PICKS": "2",
                                                          "RADAR_MODELS_CHECKER": "mistral/a groq/b"})
    assert cfg["langs"] == ["vi", "en"] and cfg["picks_per_run"] == 2 and cfg["models"]["checker"] == ["mistral/a", "groq/b"]
