"""One small HTTP helper (stdlib only) shared by the GitHub and LLM clients.

Every base URL can be redirected with an environment variable so the tests talk to a
local fake server instead of the real service; nothing else changes between the two.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request


class HttpError(RuntimeError):
    def __init__(self, status: int, body: str, url: str, retry_after: float | None = None):
        super().__init__(f"HTTP {status} from {url}: {body[:300]}")
        self.status = status
        self.body = body
        self.url = url
        self.retry_after = retry_after       # seconds, from a numeric Retry-After header when the server sent one

    @property
    def retryable(self) -> bool:
        return self.status in (408, 425, 429) or self.status >= 500


def request_json(url: str, *, headers: dict | None = None, payload: dict | None = None,
                 timeout: float = 60.0) -> dict | list:
    """GET (no payload) or POST (JSON payload) and decode a JSON answer."""
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method="POST" if data is not None else "GET")
    req.add_header("Accept", "application/json")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - https/http only, set by us
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = (exc.headers.get("Retry-After") or "").strip() if exc.headers else ""
        wait = float(raw) if raw.replace(".", "", 1).isdigit() else None
        raise HttpError(exc.code, exc.read().decode("utf-8", "replace"), url, wait) from exc
    except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
        raise HttpError(599, str(exc), url) from exc
    except json.JSONDecodeError as exc:
        raise HttpError(502, f"not JSON: {exc}", url) from exc
