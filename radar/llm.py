"""Free-model gateway: the provider table and key names of docs/vps-team.md, over plain HTTPS.

A model id is `<provider>/<model>` exactly as in the VPS team's `team.env` (the first is the
primary, the rest are fallbacks). Text generation needs no agent sandbox, so each call is one
OpenAI-compatible chat completion. A model whose key is missing is skipped, a rate limit or a
server error moves to the next model, and a run that exhausts the list raises `AllModelsFailed`
instead of inventing an answer.
"""

from __future__ import annotations

import json
import os
import re
import time

from .net import HttpError, request_json

# Same names as PROVIDER_KEYS in scripts/team/team.py of claude-agent-routing-template.
PROVIDER_KEYS = {
    "openrouter": "OPENROUTER_API_KEY",
    "google": "GOOGLE_GENERATIVE_AI_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "groq": "GROQ_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "nvidia": "NVIDIA_API_KEY",
}
# OpenAI-compatible chat endpoints. Override one with RADAR_BASE_<PROVIDER> (tests, proxies).
BASE_URLS = {
    "openrouter": "https://openrouter.ai/api/v1",
    "google": "https://generativelanguage.googleapis.com/v1beta/openai",
    "mistral": "https://api.mistral.ai/v1",
    "groq": "https://api.groq.com/openai/v1",
    "deepseek": "https://api.deepseek.com",
    "nvidia": "https://integrate.api.nvidia.com/v1",
}
# Model-name fragments -> vendor family. Order matters: a distilled model names two families, the base model decides.
FAMILIES = (("deepseek", "deepseek"), ("gemini", "google"), ("gemma", "google"), ("llama", "meta"), ("mixtral", "mistral"),
            ("mistral", "mistral"), ("codestral", "mistral"), ("magistral", "mistral"), ("ministral", "mistral"),
            ("qwen", "qwen"), ("qwq", "qwen"), ("gpt", "openai"), ("claude", "anthropic"), ("glm", "zhipu"), ("kimi", "moonshot"),
            ("phi-", "microsoft"), ("nemotron", "nvidia"), ("command", "cohere"), ("grok", "xai"))


class AllModelsFailed(RuntimeError):
    pass


def split_model(model: str) -> tuple[str, str]:
    provider, _, name = model.partition("/")
    if provider not in PROVIDER_KEYS or not name:
        raise ValueError(f"model id {model!r} must be <provider>/<model> with provider in {sorted(PROVIDER_KEYS)}")
    return provider, name


def family(model: str) -> str:
    """The vendor family of a model, so the checker is not the writer's own family (as `team doctor` warns).
    `groq/llama-3` and `openrouter/meta-llama/llama-3:free` are one family; `openrouter/google/gemma` and `google/gemini` too."""
    provider, name = split_model(model)
    low = name.lower()
    for key, vendor in FAMILIES:
        if key in low:
            return vendor
    if provider in ("openrouter", "nvidia") and "/" in low:
        return re.sub(r"[^a-z]", "", low.split("/", 1)[0]) or provider
    return provider


def base_url(provider: str) -> str:
    return os.environ.get(f"RADAR_BASE_{provider.upper()}") or BASE_URLS[provider]


def has_key(model: str, env: dict | None = None) -> bool:
    env = os.environ if env is None else env
    return bool(env.get(PROVIDER_KEYS[split_model(model)[0]]))


class Gateway:
    """Calls the first usable model; records every attempt so a run report can show them."""

    def __init__(self, *, attempts_per_model: int = 2, backoff: float = 2.0, timeout: float = 120.0,
                 sleep=time.sleep, env: dict | None = None):
        self.attempts_per_model = attempts_per_model
        self.backoff = backoff
        self.timeout = timeout
        self.sleep = sleep
        self.env = os.environ if env is None else env
        self.log: list[dict] = []

    def chat(self, models: list[str], system: str, user: str, *, max_tokens: int = 4000,
             temperature: float = 0.3, json_mode: bool = True) -> tuple[str, str]:
        """Return (text, model). Raises AllModelsFailed when no model in the list answers."""
        errors = []
        for model in models:
            provider, name = split_model(model)
            key = self.env.get(PROVIDER_KEYS[provider])
            if not key:
                self.log.append({"model": model, "status": "skipped", "why": f"{PROVIDER_KEYS[provider]} not set"})
                continue
            for attempt in range(1, self.attempts_per_model + 1):
                payload = {"model": name, "temperature": temperature, "max_tokens": max_tokens,
                           "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
                if json_mode and provider != "nvidia":
                    payload["response_format"] = {"type": "json_object"}
                try:
                    body = request_json(base_url(provider) + "/chat/completions",
                                        headers={"Authorization": f"Bearer {key}"}, payload=payload,
                                        timeout=self.timeout)
                    text = body["choices"][0]["message"]["content"]
                    if not isinstance(text, str) or not text.strip():
                        raise HttpError(502, "empty completion", base_url(provider))
                except (HttpError, KeyError, IndexError, TypeError) as exc:
                    retry = isinstance(exc, HttpError) and exc.retryable
                    self.log.append({"model": model, "status": "error", "attempt": attempt, "why": str(exc)[:200]})
                    errors.append(f"{model}: {exc}")
                    if retry and attempt < self.attempts_per_model:
                        self.sleep(self.backoff * attempt)
                        continue
                    break
                self.log.append({"model": model, "status": "ok", "attempt": attempt})
                return text, model
        raise AllModelsFailed("no model answered: " + "; ".join(errors[-4:]) if errors else
                              "no model answered: no API key set for any model in " + ", ".join(models))


def parse_json(text: str):
    """The first JSON object in a model answer, tolerating a code fence or chatter around it."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
    candidates = [fence.group(1)] if fence else []
    candidates.append(text)
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        candidates.append(text[start:end + 1])
    for cand in candidates:
        try:
            value = json.loads(cand)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise ValueError("no JSON object in the model answer")
