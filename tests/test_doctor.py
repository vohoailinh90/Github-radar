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
