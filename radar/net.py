"""One small HTTP helper (stdlib only) shared by the GitHub and LLM clients.

Every base URL can be redirected with an environment variable so the tests talk to a
local fake server instead of the real service; nothing else changes between the two.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request


# urllib's own "Python-urllib/3.x" is refused by Cloudflare-fronted APIs (Groq answers HTTP 403, error 1010, "browser
# signature banned"), so every request names itself. A caller may still send its own User-Agent; it wins.
USER_AGENT = "github-radar/1.0 (+https://github.com/vohoailinh90/github-radar)"


class HttpError(RuntimeError):
    def __init__(self, status: int, body: str, url: str, retry_after: float | None = None, headers: dict | None = None):
        super().__init__(f"HTTP {status} from {url}: {body[:300]}")
        self.status = status
        self.body = body
        self.url = url
        self.retry_after = retry_after       # seconds, from a numeric Retry-After header when the server sent one
        self.headers = headers or {}         # only rate-limit related headers (limit/remaining/reset): they say WHY a 429 happened

    @property
    def retryable(self) -> bool:
        return self.status in (408, 425, 429) or self.status >= 500


def parse_retry_after(raw: str | None) -> float | None:
    """Seconds from a numeric Retry-After. An HTTP-date, a sign, an exponent or a non-ASCII digit is "not given"."""
    raw = (raw or "").strip()
    return float(raw) if re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", raw) else None


def request_json(url: str, *, headers: dict | None = None, payload: dict | None = None,
                 timeout: float = 60.0) -> dict | list:
    """GET (no payload) or POST (JSON payload) and decode a JSON answer."""
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method="POST" if data is not None else "GET")
    req.add_header("Accept", "application/json")
    req.add_header("User-Agent", USER_AGENT)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - https/http only, set by us
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        wait = parse_retry_after(exc.headers.get("Retry-After") if exc.headers else None)
        limits = {k.lower(): v[:60] for k, v in (exc.headers.items() if exc.headers else []) if re.match(r"(?i)(x-)?(rate-?limit|retry-after)", k)}
        raise HttpError(exc.code, exc.read().decode("utf-8", "replace"), url, wait, limits) from exc
    except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
        raise HttpError(599, str(exc), url) from exc
    except json.JSONDecodeError as exc:
        raise HttpError(502, f"not JSON: {exc}", url) from exc
