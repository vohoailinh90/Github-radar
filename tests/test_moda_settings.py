"""`.claude/settings.json`: the standing permission for Moda reports, and what it must never contain.

The owner gave Claude full authority to create reports in Moda without asking again and again. The questions come from Claude Code's
own tool-permission prompts, so the authority is a list of tools in the project settings. This pins the list: every entry is a Moda tool
that creates, edits, reads or exports a report canvas, and none of the tools that delete, publish, spend credits or hand the work to
someone else is in it. Those stay the owner's decision (CLAUDE.md, "Moda reports").
"""

import json
from pathlib import Path

SETTINGS = Path(__file__).resolve().parent.parent / ".claude" / "settings.json"
PREFIX = "mcp__Moda_-_Slides_and_Designs__"
MAKES_AND_READS_A_REPORT = {
    "moda_bootstrap", "load_skill", "ask_expert", "canvas_create", "canvas_apply_markup", "canvas_edit", "canvas_read", "canvas_list",
    "canvas_search", "canvas_screenshot", "export", "task_status", "template_list", "template_search", "brand_list", "brand_show"}
NEVER = {
    "canvas_delete": "deletes",
    "drive_delete": "deletes",
    "task_cancel": "stops work in progress",
    "canvas_share": "publishes outside the account",
    "site_list": "belongs to publishing sites",
    "site_show": "belongs to publishing sites",
    "canvas_update": "its template flag publishes the canvas to the whole team",
    "drive_organize": "can set visibility to team",
    "canvas_edit_image": "spends Moda credits",
    "task_delegate": "spends Moda credits",
    "media_remove_background": "spends Moda credits",
    "media_fetch_logo": "fetches from the web on the owner's account",
    "media_video_frames": "media work, not a report",
    "upload": "makes Moda fetch a URL server-side",
    "brand_create": "changes the owner's brand kits",
    "brand_update": "changes the owner's brand kits",
    "brand_delete": "deletes",
    "canvas_import_pages": "copies pages out of other canvases",
    "canvas_comments": "can post to other people's threads",
    "edit_apply": "video timeline, not a report",
    "edit_read": "video timeline, not a report",
    "file_list": "not needed to make a report",
    "file_read": "not needed to make a report",
    "file_search": "not needed to make a report",
    "drive_tree": "not needed to make a report",
}


def allowed():
    return json.loads(SETTINGS.read_text(encoding="utf-8"))["permissions"]["allow"]


def test_the_file_grants_permissions_and_nothing_else():
    data = json.loads(SETTINGS.read_text(encoding="utf-8"))
    assert list(data) == ["permissions"] and list(data["permissions"]) == ["allow"]       # no hooks, no env, no deny that hides a gap


def test_every_entry_is_one_named_moda_tool_that_makes_or_reads_a_report():
    entries = allowed()
    assert len(entries) == len(set(entries))
    assert all(e.startswith(PREFIX) for e in entries), [e for e in entries if not e.startswith(PREFIX)]
    assert {e.removeprefix(PREFIX) for e in entries} == MAKES_AND_READS_A_REPORT


def test_what_deletes_publishes_spends_or_hands_the_work_over_is_not_granted():
    granted = {e.removeprefix(PREFIX) for e in allowed()}
    for tool, why in NEVER.items():
        assert tool not in granted, f"{tool} must stay a question for the owner: {why}"
    assert not any("*" in e or e == PREFIX.rstrip("_") for e in allowed())                 # no wildcard that would grant the rest


def test_enough_is_granted_to_make_a_report_start_to_finish():
    granted = {e.removeprefix(PREFIX) for e in allowed()}
    assert {"canvas_create", "canvas_apply_markup", "canvas_screenshot", "export"} <= granted
