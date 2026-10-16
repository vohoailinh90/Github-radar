"""Read-only GitHub REST client for public repositories."""

from __future__ import annotations

import base64
import os
import time
import urllib.parse

from .net import HttpError, request_json


MAX_RATE_WAIT = 60       # seconds a "Retry-After" may ask for before we give up instead of stalling the run


class GitHub:
    """`search_interval`: minimum seconds between the *starts* of two Search API calls (a slow call shortens the real gap).
    The search limit is 30 a minute, and GitHub also answers a quick burst with a secondary limit (403/429 plus
    Retry-After), so scans space their searches out."""

    def __init__(self, token: str | None = None, base: str | None = None, sleep=time.sleep, clock=time.monotonic,
                 search_interval: float = 0.0):
        self.token = token if token is not None else os.environ.get("GITHUB_TOKEN", "")
        self.base = (base or os.environ.get("GITHUB_API_URL") or "https://api.github.com").rstrip("/")
        self.sleep = sleep
        self.clock = clock
        self.search_interval = search_interval
        self._last_search: float | None = None

    def get(self, path: str, **params):
        url = self.base + path + (("?" + urllib.parse.urlencode(params)) if params else "")
        headers = {"X-GitHub-Api-Version": "2022-11-28", "Accept": "application/vnd.github+json",
                   "User-Agent": "github-radar"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        for attempt in (1, 2, 3):
            try:
                return request_json(url, headers=headers, timeout=30)
            except HttpError as exc:
                told = exc.retry_after
                if exc.status in (403, 429) and told is not None and told <= MAX_RATE_WAIT and attempt < 3:
                    self.sleep(told + 1)             # the secondary rate limit says how long to wait: that, plus a second of margin
                    continue
                if exc.retryable and attempt < 3:
                    self.sleep(2 * attempt)
                    continue
                raise

    def search(self, query: str, per_page: int = 15) -> list[dict]:
        if self._last_search is not None:
            wait = self.search_interval - (self.clock() - self._last_search)
            if wait > 0:
                self.sleep(wait)
        self._last_search = self.clock()
        data = self.get("/search/repositories", q=query, sort="stars", order="desc", per_page=per_page)
        return data.get("items", []) if isinstance(data, dict) else []

    def readme(self, full_name: str) -> str:
        try:
            data = self.get(f"/repos/{full_name}/readme")
        except HttpError as exc:
            if exc.status == 404:
                return ""
            raise
        if isinstance(data, dict) and data.get("encoding") == "base64":
            return base64.b64decode(data.get("content", "")).decode("utf-8", "replace")
        return ""

    def languages(self, full_name: str) -> dict:
        data = self.get(f"/repos/{full_name}/languages")
        return data if isinstance(data, dict) else {}

    def tree(self, full_name: str, branch: str) -> list[str]:
        """Top-level paths, directories with a trailing slash."""
        data = self.get(f"/repos/{full_name}/git/trees/{urllib.parse.quote(branch)}")
        items = data.get("tree", []) if isinstance(data, dict) else []
        return [i["path"] + ("/" if i.get("type") == "tree" else "") for i in items if i.get("path")]

    def children(self, full_name: str, branch: str, directory: str) -> list[str]:
        data = self.get(f"/repos/{full_name}/git/trees/{urllib.parse.quote(branch)}:{urllib.parse.quote(directory)}")
        items = data.get("tree", []) if isinstance(data, dict) else []
        return [f"{directory}/{i['path']}" + ("/" if i.get("type") == "tree" else "") for i in items if i.get("path")]
