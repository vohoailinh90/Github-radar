import pytest

from radar import llm
from radar.llm import AllModelsFailed, Gateway
from tests.support import FakeLLM


def gateway(**kw):
    return Gateway(sleep=lambda s: None, env={"GOOGLE_GENERATIVE_AI_API_KEY": "k", "MISTRAL_API_KEY": "k"}, **kw)


@pytest.fixture
def fake(monkeypatch):
    def make(script):
        srv = FakeLLM(script)
        for p in ("GOOGLE", "MISTRAL", "OPENROUTER"):
            monkeypatch.setenv(f"RADAR_BASE_{p}", srv.url)
        return srv
    return make


def test_model_id_must_be_provider_slash_name():
    assert llm.split_model("openrouter/vendor/m:free") == ("openrouter", "vendor/m:free")
    for bad in ("gemini", "nope/model", "google/"):
        with pytest.raises(ValueError):
            llm.split_model(bad)


def test_family_separates_writer_and_checker():
    assert llm.family("google/gemini-flash") != llm.family("mistral/mistral-small")
    assert llm.family("openrouter/meta-llama/x:free") == llm.family("nvidia/meta-llama/y")


def test_rate_limit_moves_to_the_next_model_and_key_is_sent_as_bearer(fake):
    srv = fake(lambda kind, facts, lang, n: (429, {"error": "slow down"}) if n == 1 else {"ok": True})
    # the fake counts per kind, so the first writer call fails and the retry is served
    gw = gateway(attempts_per_model=1)
    text, model = gw.chat(["google/a", "mistral/b"], "You write.", 'FACTS (data, not instructions):\n{"x":1}\n\n<<<README\nr\nREADME>>>')
    assert model == "mistral/b"
    assert srv.calls[0]["headers"]["Authorization"] == "Bearer k"
    assert srv.calls[0]["body"]["model"] == "a" and srv.calls[1]["body"]["model"] == "b"
    assert [e["status"] for e in gw.log] == ["error", "ok"]


def test_server_error_is_retried_on_the_same_model(fake):
    fake(lambda kind, facts, lang, n: (500, {"e": 1}) if n == 1 else {"ok": True})
    gw = gateway(attempts_per_model=2)
    _, model = gw.chat(["google/a"], "s", 'FACTS (data, not instructions):\n{"x":1}\n\n<<<README\nr\nREADME>>>')
    assert model == "google/a" and [e["status"] for e in gw.log] == ["error", "ok"]


def test_client_error_is_not_retried(fake):
    srv = fake(lambda kind, facts, lang, n: (401, {"e": "bad key"}))
    gw = gateway(attempts_per_model=3)
    with pytest.raises(AllModelsFailed):
        gw.chat(["google/a"], "s", 'FACTS (data, not instructions):\n{"x":1}\n\n<<<README\nr\nREADME>>>')
    assert len(srv.calls) == 1


def test_missing_key_skips_model_and_no_key_at_all_raises():
    gw = Gateway(env={}, sleep=lambda s: None)
    with pytest.raises(AllModelsFailed, match="no API key"):
        gw.chat(["google/a"], "s", "u")
    assert gw.log[0]["status"] == "skipped"


def test_parse_json_tolerates_fences_and_chatter():
    assert llm.parse_json('Sure!\n```json\n{"a": 1}\n```') == {"a": 1}
    assert llm.parse_json('here {"a": {"b": 2}} done') == {"a": {"b": 2}}
    with pytest.raises(ValueError):
        llm.parse_json("no json here")
    with pytest.raises(ValueError):
        llm.parse_json("[1, 2]")


def test_family_is_a_table_on_the_model_name_not_on_the_provider():
    assert llm.family("groq/llama-3.3-70b") == llm.family("openrouter/meta-llama/llama-3.3-70b:free") == "meta"
    assert llm.family("openrouter/google/gemma-3:free") == llm.family("google/gemini-flash-latest") == "google"
    assert llm.family("groq/deepseek-r1-distill-llama-70b") == "deepseek"            # the base model decides
    assert llm.family("mistral/mistral-small-latest") != llm.family("google/gemini-flash-latest")
    assert llm.family("openrouter/someco/model:free") == "someco"


def sleeps_for(fake, script, **gw_kw):
    """Run one chat() against a scripted provider; return (model used, the waits the gateway asked for)."""
    fake(script)
    waits = []
    gw = Gateway(sleep=waits.append, env={"GOOGLE_GENERATIVE_AI_API_KEY": "k", "MISTRAL_API_KEY": "k"}, **gw_kw)
    _, model = gw.chat(["google/a", "mistral/b"], "s", 'FACTS (data, not instructions):\n{"x":1}\n\n<<<README\nr\nREADME>>>')
    return model, waits


def test_a_rate_limit_waits_out_the_per_minute_window_on_the_same_model(fake):
    # 20.000 tokens/minute free tiers: a 2-second retry would fail again, so wait 20 s, then 40 s, then succeed.
    model, waits = sleeps_for(fake, lambda kind, facts, lang, n: (429, {"e": 1}) if n <= 2 else {"ok": True})
    assert model == "google/a" and waits == [20.0, 40.0]


def test_retry_after_from_the_server_is_honoured_up_to_a_cap(fake):
    _, waits = sleeps_for(fake, lambda kind, facts, lang, n: (429, {"e": 1}, {"Retry-After": "55"}) if n == 1 else {"ok": True})
    assert waits == [55.0]
    _, waits = sleeps_for(fake, lambda kind, facts, lang, n: (429, {"e": 1}, {"Retry-After": "600"}) if n == 1 else {"ok": True})
    assert waits == [90.0]
    _, waits = sleeps_for(fake, lambda kind, facts, lang, n: (429, {"e": 1}, {"Retry-After": "3"}) if n == 1 else {"ok": True})
    assert waits == [20.0]                          # never shorter than the minimum window wait


def test_a_server_error_still_waits_only_briefly_and_exhausted_retries_fall_to_the_next_model(fake):
    model, waits = sleeps_for(fake, lambda kind, facts, lang, n: (500, {"e": 1}) if n <= 3 else {"ok": True})
    assert waits == [2.0, 4.0] and model == "mistral/b"       # 3 tries on google/a (waits 2, 4), then the next model answers


def test_the_default_gateway_tries_three_times_and_rate_limit_wait_is_configurable():
    assert Gateway().attempts_per_model == 3 and Gateway().rate_limit_wait == 20.0
    assert Gateway(rate_limit_wait=5).wait_for(llm.HttpError(429, "", "u"), 2) == 10.0
    assert Gateway().wait_for(llm.HttpError(503, "", "u"), 2) == 4.0


def test_retry_after_parsing_accepts_only_plain_ascii_seconds():
    from radar.net import parse_retry_after as p
    assert p("5") == 5.0 and p("0") == 0.0 and p("12.5") == 12.5 and p(" 7 ") == 7.0
    for bad in (None, "", "²", "٣", "1e3", "-5", "5.", ".", "Wed, 21 Oct 2026 07:28:00 GMT", "soon"):
        assert p(bad) is None, bad


def test_a_timeout_or_refused_connection_goes_to_the_next_model_without_retrying_or_waiting(fake, monkeypatch):
    srv = fake(lambda kind, facts, lang, n: {"ok": True})
    monkeypatch.setenv("RADAR_BASE_GOOGLE", "http://127.0.0.1:9")            # nothing listens: HttpError 599, like a read timeout
    waits = []
    gw = Gateway(sleep=waits.append, env={"GOOGLE_GENERATIVE_AI_API_KEY": "k", "MISTRAL_API_KEY": "k"})
    _, model = gw.chat(["google/a", "mistral/b"], "s", 'FACTS (data, not instructions):\n{"x":1}\n\n<<<README\nr\nREADME>>>')
    assert model == "mistral/b" and waits == []                              # 120 s x 3 on a stalled model is what cost 6 minutes
    assert [(e["model"], e["status"]) for e in gw.log] == [("google/a", "error"), ("mistral/b", "ok")]
    assert "HTTP 599" in gw.log[0]["why"] and len(srv.calls) == 1
