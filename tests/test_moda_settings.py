"""`.claude/settings.json`: the standing permission for the Moda and Canva MCP servers.

The owner gave Claude full authority over the Moda and Canva connectors, so the project settings allow each server as a whole
(`mcp__<server>` covers every tool of that server) and the tool prompts stop. This pins the file: permissions only, exactly these
two servers, no hooks, no env, no deny that hides a gap. Narrowing it again to single tools is the owner's decision (CLAUDE.md, "Moda reports").
"""

import json
from pathlib import Path

SETTINGS = Path(__file__).resolve().parent.parent / ".claude" / "settings.json"
SERVERS = {"mcp__Moda_-_Slides_and_Designs", "mcp__Canva"}


def allowed():
    return json.loads(SETTINGS.read_text(encoding="utf-8"))["permissions"]["allow"]


def test_the_file_grants_permissions_and_nothing_else():
    data = json.loads(SETTINGS.read_text(encoding="utf-8"))
    assert list(data) == ["permissions"] and list(data["permissions"]) == ["allow"]       # no hooks, no env, no deny that hides a gap


def test_the_grant_is_exactly_the_moda_and_canva_servers():
    entries = allowed()
    assert len(entries) == len(set(entries))
    assert set(entries) == SERVERS
