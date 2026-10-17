import argparse

import pytest

from radar import cli, config
from tests.support import _Server


@pytest.fixture
def groq(monkeypatch):
    srv = _Server(lambda call: (200, {"data": [{"id": "openai/gpt-oss-120b"}, {"id": "llama-3.1-8b-instant"}]}))
    monkeypatch.setenv("RADAR_BASE_GROQ", srv.url)
    monkeypatch.setenv("GROQ_API_KEY", "k")
    yield srv
    srv.close()


def doctor(models, capsys):
    cfg = config.load(env={})
    cfg["models"] = {"writer": models, "checker": models}
    code = cli.cmd_doctor(argparse.Namespace(ping=True), cfg)
    return code, capsys.readouterr().out


def test_a_retired_model_is_reported_with_the_ids_the_key_can_really_call(groq, capsys):
    code, out = doctor(["groq/llama-3.3-70b-versatile"], capsys)
    assert code == 1
    assert "FAIL  groq/llama-3.3-70b-versatile is not offered by groq any more" in out
    assert "groq offers: llama-3.1-8b-instant, openai/gpt-oss-120b" in out


def test_models_that_are_all_offered_print_no_list(groq, capsys):
    code, out = doctor(["groq/openai/gpt-oss-120b"], capsys)
    assert code == 0
    assert "groq/openai/gpt-oss-120b is offered" in out and "offers:" not in out


# --- the model record: what a `-latest` alias points to ---------------------------------------------------------------

ALIAS = {"name": "models/gemini-9-flash-001", "version": "001", "displayName": "Gemini 9 Flash", "thinking": True,
         "inputTokenLimit": 1048576, "outputTokenLimit": 65536,
         "description": "Alias that points to the most recent release of Gemini 9 Flash."}


@pytest.fixture
def google(monkeypatch):
    """Two fake endpoints: the OpenAI-compatible model list (what doctor already read) and Google's native model record."""
    compat = _Server(lambda call: (200, {"data": [{"id": "models/gemini-flash-latest"}, {"id": "models/gemini-flash-lite-latest"}]}))
    state = {"status": 200, "record": ALIAS}
    native = _Server(lambda call: (state["status"], state["record"] if state["status"] == 200 else {"error": "x"}))
    monkeypatch.setenv("RADAR_BASE_GOOGLE", compat.url)
    monkeypatch.setenv("RADAR_NATIVE_GOOGLE", native.url)
    monkeypatch.setenv("GOOGLE_GENERATIVE_AI_API_KEY", "secret-g-key")
    yield native, state
    compat.close()
    native.close()


def test_doctor_prints_what_the_google_alias_points_to_and_keeps_the_key_out_of_the_url_and_the_output(google, capsys):
    native, _ = google
    code, out = doctor(["google/gemini-flash-latest"], capsys)
    assert code == 0
    assert ("info  google/gemini-flash-latest -> name=models/gemini-9-flash-001 version=001 display=Gemini 9 Flash thinking=True "
            "tokens in/out=1048576/65536 | Alias that points to the most recent release of Gemini 9 Flash.") in out
    call = native.calls[0]
    assert call["path"] == "/models/gemini-flash-latest" and "secret-g-key" not in call["path"]
    assert {k.lower(): v for k, v in call["headers"].items()}["x-goog-api-key"] == "secret-g-key"     # in a header only
    assert "secret-g-key" not in out


def test_a_missing_model_record_is_a_warning_and_never_fails_the_doctor(google, capsys):
    _, state = google
    state["status"] = 404
    code, out = doctor(["google/gemini-flash-latest"], capsys)
    assert code == 0 and "WARN  google/gemini-flash-latest: no model record from Google (HTTP 404)" in out
    assert "is offered" in out                                              # the pass/fail lines are untouched


def test_text_from_the_record_is_printed_on_one_clean_line_and_unknown_shapes_do_not_crash(google, capsys):
    _, state = google
    state["record"] = {"name": "models/x\n::warning::y", "description": "a\x1b[31m\nb\t" + "z" * 400, "thinking": "yes", "inputTokenLimit": True}
    code, out = doctor(["google/gemini-flash-latest"], capsys)
    line = next(l for l in out.splitlines() if l.startswith("info  google/gemini-flash-latest"))
    assert code == 0 and "\x1b" not in out and "thinking" not in line and "tokens" not in line
    assert line.count("::warning::y") == 1 and len(line) < 400
    state["record"] = ["not", "an", "object"]
    assert "the record has no name, version or limits" in doctor(["google/gemini-flash-latest"], capsys)[1]


def test_no_model_record_is_read_without_a_google_model_or_a_google_key(groq, monkeypatch, capsys):
    monkeypatch.delenv("GOOGLE_GENERATIVE_AI_API_KEY", raising=False)
    code, out = doctor(["groq/openai/gpt-oss-120b"], capsys)
    assert code == 0 and "info  " not in out and "no model record" not in out
