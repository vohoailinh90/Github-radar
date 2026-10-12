import pytest

from tests.support import FakeLLM, fake_github


@pytest.fixture
def servers(monkeypatch):
    gh, llm = fake_github(), FakeLLM()
    monkeypatch.setenv("GITHUB_API_URL", gh.url)
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    for provider in ("GOOGLE", "MISTRAL"):
        monkeypatch.setenv(f"RADAR_BASE_{provider}", llm.url)
    monkeypatch.setenv("GOOGLE_GENERATIVE_AI_API_KEY", "g-key")
    monkeypatch.setenv("MISTRAL_API_KEY", "m-key")
    yield gh, llm
    gh.close()
    llm.close()
