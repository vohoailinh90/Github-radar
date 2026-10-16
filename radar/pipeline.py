"""One scheduled run: discover -> facts -> write/check/gates -> digests -> studio bundle -> report."""

from __future__ import annotations

import datetime as dt
import json
import re
import shutil
import tempfile
import time
from pathlib import Path

from . import contract, digest, discover, facts as factslib, gates, history, studio_export
from .llm import AllModelsFailed, Gateway
from .net import HttpError
from .write import write_one


RUN_SLUG = re.compile(r"\d{4}-\d{2}-\d{2}(?:-\d+)?")      # what `run_slug` produces; nothing else is a run folder


def read_bundle(root: Path) -> dict[str, str]:
    base = root / "export" / "studio"
    return {p.relative_to(base).as_posix(): p.read_text(encoding="utf-8") for p in sorted(base.rglob("*.yaml"))} \
        if base.exists() else {}


def run_slug(root: Path, date: str) -> str:
    """`2026-10-14`, or `2026-10-14-2` for a second run the same day, so a run never overwrites another's digests or campaign."""
    slug, n = date, 1
    while (root / "digests" / slug).exists() or (root / "export" / "studio" / "campaigns" / f"radar-{slug}").exists():
        n += 1
        slug = f"{date}-{n}"
    return slug


def run(cfg: dict, gh, gw: Gateway, root: Path, today: dt.date, *, dry_run: bool = False,
        pace: float = 0.0, sleep=time.sleep, clock=time.monotonic, only: str | None = None, bucket: str | None = None) -> dict:
    """`only` (owner/name or a link) covers that one repository instead of searching: see discover.requested."""
    date = today.isoformat()
    started, budget = clock(), float(cfg.get("max_run_minutes", 35)) * 60
    seen_path = root / "state" / "seen.json"
    seen = factslib.load_seen(seen_path)
    stars_path = root / "state" / "stars.json"
    hist = history.load(stars_path)
    if only:
        cand, request_warnings = discover.requested(gh, only, cfg, seen, today, bucket, hist)
        ranked, dropped, picks = [cand], {}, [cand]
    else:
        ranked, dropped = discover.candidates(gh, cfg, seen, today, hist)
        picks = discover.pick(ranked, cfg, today)
    measured = sum(c["velocity"]["source"] == "measured" for c in ranked)
    if ranked and not dry_run:
        # Saved before any model work: a snapshot is worth keeping even when the run later times out or holds every draft.
        for c in ranked:
            history.record(hist, c["full_name"], today, c["repo"]["stargazers_count"])
        history.prune(hist, today, int(cfg["history_days"]))
        history.save(stars_path, hist)
    picked = {c["full_name"] for c in picks}
    report = {"date": date, "dry_run": dry_run, "langs": cfg["langs"], "candidates": len(ranked), "dropped": dropped,
              "picks": [{"repo": c["full_name"], "bucket": c["bucket"], "score": c["score"], "stars": c["repo"]["stargazers_count"],
                         "rising": c["rising"], "stars_per_30d": round(c["velocity"]["per_30d"]),
                         "velocity": c["velocity"]["source"], "flags": c["flags"]} for c in picks],
              # What came next, so the owner can see how close it was and tune radar.yaml without guessing.
              "shortlist": [{"repo": c["full_name"], "bucket": c["bucket"], "score": c["score"], "stars": c["repo"]["stargazers_count"],
                             "rising": c["rising"], "flags": c["flags"]}
                            for c in [c for c in ranked if c["full_name"] not in picked][:5]],
              "history": {"tracked": len(hist), "measured": measured},
              "written": [], "held": [], "export_errors": [], "aborted": None, "ok": True}
    if only:
        report["requested"] = {"repo": cand["full_name"], "bucket": cand["bucket"], "warnings": request_warnings}
    if dry_run or not picks:
        report["ok"] = bool(picks) or dry_run
        return report

    entries = []
    for cand in picks:
        try:
            facts = factslib.build(gh, cand, cfg, today)
        except (HttpError, KeyError, ValueError, TypeError) as exc:
            # One repository's GitHub error (rate limit, deleted, odd answer) holds that repository only.
            report["held"].append({"repo": cand["full_name"], "lang": "-", "problems": [f"GitHub: {str(exc)[:200]}"], "blockers": []})
            continue
        drafts = {}
        for lang in cfg["langs"]:
            if clock() - started > budget:
                # The job has a hard timeout that would cancel it and lose everything: stop starting work, keep what is done.
                report["aborted"] = f"time budget of {cfg.get('max_run_minutes', 35)} minutes used before {facts['full_name']} [{lang}]"
                break
            try:
                res = write_one(gw, cfg, facts, lang)
            except AllModelsFailed as exc:
                # Every model failed: the rest of the run would burn the same quota for nothing.
                report["aborted"] = f"{facts['full_name']} [{lang}]: {exc}"
                break
            if not (cand is picks[-1] and lang == cfg["langs"][-1]):
                sleep(pace)                          # keeps the checker under its tokens-per-minute cap; not needed after the last call
            if res["status"] == "ok":
                drafts[lang] = res["draft"]
                report["written"].append({"repo": facts["full_name"], "lang": lang, "writer": res["writer"],
                                          "checker": res["checker"], "independent_checker": res["independent"],
                                          "fixed": res["fixed"]})
            else:
                report["held"].append({"repo": facts["full_name"], "lang": lang, "problems": [str(p) for p in res["problems"]
                                       if p.level == "error"][:8], "blockers": res["issues"][:4]})
        if cfg["langs"][0] in drafts:               # the primary language decides; others may be missing and are reported
            entries.append({"facts": facts, "drafts": drafts})
        if report["aborted"]:
            break
    report["models_log"] = gw.log[-60:]
    report["warnings"] = [f"{w['repo']} [{w['lang']}]: checker shares the writer's model family"
                          for w in report["written"] if not w["independent_checker"]]

    slug = run_slug(root, date)
    if entries:
        for lang in cfg["langs"]:
            have = [e for e in entries if lang in e["drafts"]]
            for e in have:
                digest.render_repo(root, slug, e["facts"], {lang: e["drafts"][lang]}, position=entries.index(e) + 1)
            if have:
                digest.render_index(root, slug, have, lang)
        digest.render_global_index(root)
        files = studio_export.bundle(entries, cfg, slug)
        report["export_errors"] = contract.validate(files)
        if not report["export_errors"]:
            out = root / "export" / "studio"
            for rel, text in files.items():
                target = out / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(text, encoding="utf-8")
            # Remembered only once the posts exist: a repository whose bundle was refused is offered again next run.
            for e in entries:
                seen[e["facts"]["full_name"]] = {"covered": date, "stars": e["facts"]["stars"], "bucket": e["facts"]["bucket"]}
            factslib.save_seen(seen_path, seen)
    report["campaign"] = f"radar-{slug}" if entries and not report["export_errors"] else None
    report["ok"] = bool(entries) and not report["export_errors"] and not report["aborted"]
    runs = root / "state" / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    (runs / f"{slug}.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def load_entries(root: Path, slug: str) -> list[dict]:
    """The stored drafts of one run as pipeline entries, in the order the run numbered them (01, 02, ...)."""
    day = root / "digests" / slug
    entries = []
    for folder in sorted(p for p in day.iterdir() if p.is_dir()) if day.is_dir() else []:
        drafts, facts, position, note = {}, None, None, None
        for path in sorted(folder.glob("draft-*.json")):
            stored = json.loads(path.read_text(encoding="utf-8"))
            facts = facts or stored["facts"]
            position = position or stored.get("position")
            note = note or stored.get("note")
            drafts[stored["lang"]] = stored["draft"]
        if drafts:
            entries.append({"facts": facts, "drafts": drafts, "position": position or 999, "note": note})
    return sorted(entries, key=lambda e: (e["position"], e["facts"]["full_name"]))


def rerender(cfg: dict, root: Path, slug: str | None = None) -> dict:
    """Draw digests, diagrams and the studio bundle again from the stored drafts, with the current renderer.

    Nothing is fetched and no model is called. Everything is drawn into a temporary folder first: a run whose bundle the
    studio contract refuses, whose stored draft no longer fits the schema, or whose drawing fails is left exactly as it was."""
    if slug is not None and not RUN_SLUG.fullmatch(slug):
        raise ValueError(f"a run slug looks like 2026-10-12 or 2026-10-12-2, got {slug!r}")
    base = root / "digests"
    slugs = [slug] if slug else sorted(p.name for p in base.iterdir() if p.is_dir() and RUN_SLUG.fullmatch(p.name)) if base.is_dir() else []
    report = {"rerendered": [], "skipped": {}}
    for name in slugs:
        entries = load_entries(root, name)
        if not entries:
            report["skipped"][name] = "no stored drafts (written before drafts were kept)"
            continue
        bad = [f"{e['facts']['full_name']} [{lang}]: {p}" for e in entries for lang, d in e["drafts"].items()
               for p in gates.schema(d) if p.level == "error"]
        if bad:
            report["skipped"][name] = "a stored draft no longer fits the schema: " + "; ".join(bad[:2])
            continue
        present = {lang for e in entries for lang in e["drafts"]}
        langs = [l for l in cfg["langs"] if l in present] + sorted(present - set(cfg["langs"]))
        try:
            files = studio_export.bundle(entries, {**cfg, "langs": langs}, name)
            errors = contract.validate(files)
            if errors:
                report["skipped"][name] = "the studio contract refuses the new bundle: " + "; ".join(errors[:3])
                continue
            tmp = tempfile.TemporaryDirectory()
            stage = Path(tmp.name)
            for lang in langs:
                have = [e for e in entries if lang in e["drafts"]]
                for e in have:
                    digest.render_repo(stage, name, e["facts"], {lang: e["drafts"][lang]}, position=entries.index(e) + 1, note=e.get("note"))
                digest.render_index(stage, name, have, lang)
            for rel, text in files.items():
                target = stage / "export" / "studio" / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(text, encoding="utf-8")
        except Exception as exc:  # noqa: BLE001 - nothing has been written to the repository yet
            report["skipped"][name] = f"failed while drawing, nothing was changed: {type(exc).__name__}: {exc}"
            continue
        with tmp:                                       # drawing succeeded: only now copy over the repository
            shutil.copytree(stage / "digests" / name, root / "digests" / name, dirs_exist_ok=True)
            shutil.copytree(stage / "export", root / "export", dirs_exist_ok=True)
        report["rerendered"].append(name)
    digest.render_global_index(root)
    return report
