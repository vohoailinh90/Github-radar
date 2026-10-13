import pytest

from radar import cli, net
from radar.llm import Gateway
from tests.support import _Server


@pytest.fixture
def server(monkeypatch):
    srv = _Server(lambda call: (200, {"choices": [{"message": {"content": "{}"}}], "data": []}))
    monkeypatch.setenv("RADAR_BASE_GROQ", srv.url)
    yield srv
    srv.close()


def agent(call):
    return {k.lower(): v for k, v in call["headers"].items()}["user-agent"]


def test_a_request_names_itself_instead_of_sending_pythons_default_agent(server):
    # Cloudflare in front of Groq answers urllib's own "Python-urllib/3.x" with HTTP 403, error 1010 (browser signature banned)
    net.request_json(server.url + "/x")
    net.request_json(server.url + "/x", payload={"a": 1})
    for call in server.calls:
        assert agent(call).startswith("github-radar/") and "urllib" not in agent(call).lower()


def test_a_caller_may_send_its_own_user_agent(server):
    net.request_json(server.url + "/x", headers={"User-Agent": "mine"})
    assert agent(server.calls[0]) == "mine"


def test_a_model_call_and_the_model_listing_of_doctor_ping_carry_the_agent(server, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "k")
    Gateway(sleep=lambda s: None).chat(["groq/llama-3.3-70b-versatile"], "s", "u")
    cli._list_models("groq")
    assert [c["path"] for c in server.calls] == ["/chat/completions", "/models"]
    assert all(agent(c) == net.USER_AGENT for c in server.calls)
