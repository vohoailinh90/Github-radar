"""One scheduled run: discover -> facts -> write/check/gates -> digests -> studio bundle -> report."""

from __future__ import annotations

import datetime as dt
import json
import time
from pathlib import Path

from . import contract, digest, discover, facts as factslib, studio_export
from .llm import AllModelsFailed, Gateway
from .write import write_one


def read_bundle(root: Path) -> dict[str, str]:
    base = root / "export" / "studio"
    return {p.relative_to(base).as_posix(): p.read_text(encoding="utf-8") for p in sorted(base.rglob("*.yaml"))} \
        if base.exists() else {}


def run(cfg: dict, gh, gw: Gateway, root: Path, today: dt.date, *, dry_run: bool = False,
        pace: float = 0.0, sleep=time.sleep) -> dict:
    date = today.isoformat()
    seen_path = root / "state" / "seen.json"
    seen = factslib.load_seen(seen_path)
    ranked, dropped = discover.candidates(gh, cfg, seen, today)
    picks = discover.pick(ranked, cfg, today)
    report = {"date": date, "dry_run": dry_run, "langs": cfg["langs"], "candidates": len(ranked), "dropped": dropped,
              "picks": [{"repo": c["full_name"], "bucket": c["bucket"], "score": c["score"],
                         "stars": c["repo"]["stargazers_count"]} for c in picks],
              "written": [], "held": [], "export_errors": [], "aborted": None, "ok": True}
    if dry_run or not picks:
        report["ok"] = bool(picks) or dry_run
        return report

    entries = []
    for cand in picks:
        facts = factslib.build(gh, cand, cfg, today)
        drafts = {}
        for lang in cfg["langs"]:
            try:
                res = write_one(gw, cfg, facts, lang)
            except AllModelsFailed as exc:
                # Every model failed: the rest of the run would burn the same quota for nothing.
                report["aborted"] = f"{facts['full_name']} [{lang}]: {exc}"
                break
            sleep(pace)
            if res["status"] == "ok":
                drafts[lang] = res["draft"]
                report["written"].append({"repo": facts["full_name"], "lang": lang, "writer": res["writer"],
                                          "checker": res["checker"], "fixed": res["fixed"]})
            else:
                report["held"].append({"repo": facts["full_name"], "lang": lang, "problems": [str(p) for p in res["problems"]
                                       if p.level == "error"][:8], "blockers": res["issues"][:4]})
        if report["aborted"]:
            break
        if cfg["langs"][0] in drafts:               # the primary language decides; others may be missing and are reported
            entries.append({"facts": facts, "drafts": drafts})
    report["models_log"] = gw.log[-60:]

    if entries:
        for lang in cfg["langs"]:
            have = [e for e in entries if lang in e["drafts"]]
            for e in have:
                digest.render_repo(root, date, e["facts"], {lang: e["drafts"][lang]})
            if have:
                digest.render_index(root, date, have, lang)
        digest.render_global_index(root)
        files = studio_export.bundle(entries, cfg, date)
        report["export_errors"] = contract.validate(files)
        if not report["export_errors"]:
            out = root / "export" / "studio"
            for rel, text in files.items():
                target = out / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(text, encoding="utf-8")
        for e in entries:
            seen[e["facts"]["full_name"]] = {"covered": date, "stars": e["facts"]["stars"], "bucket": e["facts"]["bucket"]}
        factslib.save_seen(seen_path, seen)
    report["ok"] = bool(entries) and not report["export_errors"] and not report["aborted"]
    runs = root / "state" / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    (runs / f"{date}.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report
