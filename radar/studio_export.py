"""A bundle in the exact shape tool-marketing-studio loads, so `studio.py check` passes on it.

Everything the studio forbids is avoided by construction: no URL in a post (the repo link goes
through `links:` + `{link}` in the first comment), at most 10 slides, a Facebook hook under 125
characters, and the same numbers in every language. Posts are `status: draft`: approving and
publishing stay the owner's act inside the studio.
"""

from __future__ import annotations

import re

import yaml

from . import svg
from .facts import slug
from .labels import L

EMOJI_PARTS = ["🧩", "⚙️", "🔌", "📦", "🧠", "📡"]


def shorten(text: str, limit: int) -> str:
    """Whole sentences up to `limit` characters; otherwise a clean cut with an ellipsis."""
    text = re.sub(r"\s+", " ", str(text)).strip().replace("*", "")
    if len(text) <= limit:
        return text
    cut = text[:limit]
    for mark in (". ", "。", "! ", "? ", "; "):
        i = cut.rfind(mark)
        if i >= limit * 0.3:
            return cut[:i + len(mark.strip())].strip()
    return cut[:limit - 1].rstrip(" ,;:") + "…"


def dump(data: dict) -> str:
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=100)


def post(facts: dict, draft: dict, lang: str, number: int, link_id: str, date: str, cfg: dict) -> tuple[str, dict]:
    t = L[lang]
    hiw = draft["how_it_works"]
    emoji = next((b["emoji"] for b in cfg["buckets"] if b["id"] == facts["bucket"]), "📡")
    pid = f"{number:02d}-{slug(facts['full_name'])}"
    stat_caption = " · ".join(x for x in (facts["license"], facts["language"]) if x)
    slides = [
        {"layout": "cover", "emoji": emoji, "eyebrow": f"{t['series']} · {t['bucket'][facts['bucket']]}",
         "title": shorten(draft["title"], 70), "subtitle": shorten(draft["one_liner"], 160)},
        {"layout": "stat", "eyebrow": t["scan_note"], "value": svg.fmt_int(facts["stars"], t["sep"]), "label": t["stars_label"],
         "caption": stat_caption},
        {"layout": "quote", "text": shorten(draft["problem"], 230), "author": t["problem"]},
        {"layout": "flow", "variant": "after", "title": t["flow_slide"],
         "steps": [{"text": shorten(f"{s['title']}: {s['text']}", 110)} for s in hiw["steps"][:6]]},
        {"layout": "features", "title": t["parts_slide"],
         "items": [{"emoji": EMOJI_PARTS[i % len(EMOJI_PARTS)], "title": shorten(c["name"], 40),
                    "text": shorten(c["role"], 95)} for i, c in enumerate(hiw["components"][:6])]},
        {"layout": "checklist", "title": t["learn_slide"], "tone": "ok",
         "items": [shorten(x, 110) for x in draft["learn"][:5]]},
        {"layout": "pains", "title": t["caveat_slide"], "tone": "accent",
         "items": [{"emoji": "⚠️", "text": shorten(x, 110)} for x in draft["caveats"][:4]]},
        {"layout": "cta", "emoji": "📌", "title": t["save"], "text": t["save_text"], "show_link": False},
    ]
    caption = draft["facebook"]["caption"].strip()
    tags = [re.sub(r"[^\w]", "", str(x)) for x in draft["facebook"].get("hashtags", [])]
    data = {
        "id": pid, "status": "draft", "format": "portrait", "series": f"{t['series']} · {date}", "link": link_id,
        "slides": slides,
        "platforms": {"facebook": {"caption": f"{caption}\n\n{t['disclaimer']}",
                                   "first_comment": f"{t['repo_link']}: {{link}}",
                                   "hashtags": [x for x in tags if x][:5]}},
    }
    return pid, data


def bundle(entries: list[dict], cfg: dict, date: str) -> dict[str, str]:
    """entries: [{"facts": ..., "drafts": {lang: draft}}] -> {relative path: file text}."""
    studio = cfg["studio"]
    langs = [lang for lang in cfg["langs"] if any(lang in e["drafts"] for e in entries)]
    campaign = f"radar-{date}"
    files: dict[str, str] = {}
    links: dict[str, str] = {}
    for number, entry in enumerate(entries, 1):
        facts = entry["facts"]
        link_id = f"{number:02d}-{slug(facts['full_name'])}"
        links[link_id] = facts["url"]
        for lang, draft in entry["drafts"].items():
            pid, data = post(facts, draft, lang, number, link_id, date, cfg)
            files[f"campaigns/{campaign}/posts/{lang}/{pid}.yaml"] = dump(data)
    files[f"campaigns/{campaign}/campaign.yaml"] = dump({
        "tool": studio["tool"], "langs": langs, "platforms": studio["platforms"],
        "goal": f"Share what {len(entries)} popular free GitHub projects teach, scanned on {date}: "
                "one clear explanation per project, so readers learn the idea and save the post.",
        "links": links, "utm": {"medium": "social", "campaign": campaign}, "schedule": []})
    files[f"tools/{studio['tool']}/brief.yaml"] = dump({
        "slug": studio["tool"], "name": studio["name"], "status": "launched",
        "brand": {"emoji": "📡", "accent": studio["accent"]},
        "what_it_is": "A twice-weekly series that picks well-rated free GitHub projects and explains how each one works, "
                      "with diagrams. Summaries are AI-written from the project's README and file layout and checked "
                      "by script; the projects belong to their authors.",
        "limitations": ["Not an endorsement or a security review of any project",
                        "Star counts are as of the scan date"]})
    for lang in langs:
        t = L[lang]
        files[f"tools/{studio['tool']}/positioning/{lang}.yaml"] = dump({
            "one_liner": t["save_text"], "audience": {"vi": "Dân văn phòng và lập trình viên mới", "en": "Curious builders and beginners",
                                                      "ja": "学び始めのエンジニアと会社員"}[lang],
            "pains": [{"vi": "Không biết repo nào đáng học giữa hàng triệu repo", "en": "No time to find which repositories are worth studying",
                       "ja": "学ぶ価値のあるリポジトリを探す時間がない"}[lang]]})
    return files
