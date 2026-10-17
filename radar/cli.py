"""Command line: scan, run, doctor, models, handoff, check."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.parse
from pathlib import Path

from . import conditions, config, contract, history, pipeline
from .github import GitHub
from .llm import PROVIDER_KEYS, Gateway, base_url, family, has_key, native_base, split_model
from .net import HttpError, request_json

ROOT = config.ROOT


def _date(value: str | None) -> dt.date:
    return dt.date.fromisoformat(value) if value else dt.datetime.now(dt.timezone.utc).date()


def _github(cfg) -> GitHub:
    return GitHub(search_interval=float(cfg["search_interval_seconds"]))


def cmd_scan(args, cfg) -> int:
    from . import discover, facts
    gh = _github(cfg)
    seen = facts.load_seen(ROOT / "state" / "seen.json")
    ranked, dropped = discover.candidates(gh, cfg, seen, _date(args.date), history.load(ROOT / "state" / "stars.json"))
    print("score    bucket       stars   stars/30d  repo   (* = measured from stored snapshots, else the lifetime average)")
    for c in ranked[:20]:
        mark = "*" if c["velocity"]["source"] == "measured" else " "
        on = cfg["rising"]["enabled"] and int(cfg["rising"]["slots"]) > 0
        tags = (["rising"] if c["rising"] and on else []) + [f"!{f}" for f in c["flags"]]
        print(f"{c['score']:7.3f}  {c['bucket']:<10} {c['repo']['stargazers_count']:>7,}  {c['velocity']['per_30d']:>7,.0f}{mark}  "
              f"{c['full_name']}" + (f"  [{' '.join(tags)}]" if tags else ""))
    print(f"dropped: {json.dumps(dropped, ensure_ascii=False)}")
    return 0 if ranked else 1


def cmd_run(args, cfg) -> int:
    # A flag that was given wins over the variable, even as "" (= the normal scan); only an omitted flag (None) falls back.
    # RADAR_REPO is how the workflow passes its input (never through the shell command line).
    only = (os.environ.get("RADAR_REPO", "") if args.repo is None else args.repo).strip() or None
    bucket = (os.environ.get("RADAR_BUCKET", "") if args.bucket is None else args.bucket).strip() or None
    report = pipeline.run(cfg, _github(cfg), Gateway(), ROOT, _date(args.date), dry_run=args.dry_run,
                          pace=float(cfg.get("pace_seconds", 3)), only=only, bucket=bucket)
    print(json.dumps({k: v for k, v in report.items() if k != "models_log"}, indent=2, ensure_ascii=False))
    return 0 if report["ok"] else 1


def cmd_presets(args, cfg) -> int:
    """Saved scan conditions and what each would cost. Nothing is fetched."""
    for name, item in sorted(conditions.load_presets().items()):
        try:
            effective = config.load(args.config, {**os.environ, "RADAR_PRESET": name, "RADAR_CONDITIONS": ""})
        except ValueError as exc:
            print(f"FAIL  {name}: {exc}")
            return 1
        cost = conditions.estimate(effective)
        print(f"{name:<18} {item['label']}")
        print(f"{'':<18} {cost['searches']} searches (~{cost['search_seconds']} s), {cost['model_calls']}+ model calls, "
              f"~{cost['pace_seconds']} s of pauses between posts; conditions: {json.dumps(item['conditions'], ensure_ascii=False)}")
    return 0


def cmd_doctor(args, cfg) -> int:
    bad = 0
    models = {role: cfg["models"][role] for role in ("writer", "checker")}
    for role, ids in models.items():
        for model in ids:
            try:
                provider, _ = split_model(model)
            except ValueError as exc:
                print(f"FAIL  {role}: {exc}")
                bad += 1
                continue
            print(f"{'ok  ' if has_key(model) else 'WARN'}  {role}: {model}"
                  + ("" if has_key(model) else f"  ({PROVIDER_KEYS[provider]} not set; this model will be skipped)"))
    usable = {role: [m for m in ids if _safe(has_key, m)] for role, ids in models.items()}
    for role, ids in usable.items():
        if not ids:
            print(f"FAIL  no {role} model has a key")
            bad += 1
    if usable["writer"] and usable["checker"] and {family(m) for m in usable["writer"]} == {family(m) for m in usable["checker"]} \
            and len({family(m) for m in usable["writer"]}) == 1:
        print("WARN  writer and checker are one model family; the checker shares the writer's blind spots")
    print(f"{'ok  ' if os.environ.get('GITHUB_TOKEN') else 'WARN'}  GITHUB_TOKEN {'set' if os.environ.get('GITHUB_TOKEN') else 'not set (60 requests/hour)'}")
    if args.ping:
        for provider in sorted({split_model(m)[0] for ids in models.values() for m in ids if _safe(has_key, m)}):
            try:
                listed = _list_models(provider)
            except HttpError as exc:
                print(f"FAIL  {provider}: {exc}")
                bad += 1
                continue
            missing = False
            for model in sorted({m for ids in models.values() for m in ids if m.startswith(provider + "/")}):
                found = split_model(model)[1] in listed
                print(f"{'ok  ' if found else 'FAIL'}  {model} {'is offered' if found else 'is not offered by ' + provider + ' any more'}")
                bad += not found
                missing = missing or not found
            if missing:
                # A retired model id is the usual cause; the replacement is among the ids this key can really call.
                print(f"      {provider} offers: " + ", ".join(sorted(listed)[:60]))
        # Information only: a missing record never fails the doctor (the models above already did the pass or fail).
        for model in sorted({m for ids in models.values() for m in ids if m.startswith("google/") and _safe(has_key, m)}):
            try:
                print(f"info  {model} record: {_describe(_model_record(model), split_model(model)[1])}")
            except HttpError as exc:
                print(f"WARN  {model}: no model record from Google (HTTP {exc.status})")
    return 1 if bad else 0


def _model_record(model: str) -> dict:
    """Google's own record of one model. The key travels in a header, never in the URL, so no error message or log can show it."""
    provider, name = split_model(model)
    body = request_json(f"{native_base(provider)}/models/{urllib.parse.quote(name, safe='')}",
                        headers={"x-goog-api-key": os.environ.get(PROVIDER_KEYS[provider], "")}, timeout=30)
    return body if isinstance(body, dict) else {}


def _one_line(value, limit: int) -> str:
    """Provider text on one printable line: no control character, no line break, at most `limit` characters."""
    return " ".join(re.sub(r"[\x00-\x1f\x7f]", " ", str(value)).split())[:limit]


def _describe(record: dict, requested: str) -> str:
    """The fields of the record Google keeps for `requested`. For a `-latest` alias this can be the alias's own metadata
    (same name, a generic description) and not the model behind it, so a `-latest` alias whose record carries the requested name says so;
    a pinned id (`...-001`) returns its own name too and is not an alias."""
    parts = [f"{label}={_one_line(record[key], 60)}" for label, key in (("name", "name"), ("version", "version"), ("display", "displayName"))
             if record.get(key) not in (None, "")]
    if isinstance(record.get("thinking"), bool):
        parts.append(f"thinking={record['thinking']}")
    limits = (record.get("inputTokenLimit"), record.get("outputTokenLimit"))
    if all(type(n) is int for n in limits):
        parts.append(f"tokens in/out={limits[0]}/{limits[1]}")
    text = " ".join(parts) or "the record has no name, version or limits"
    description = _one_line(record.get("description") or "", 200)
    text = f"{text} | {description}" if description else text
    if requested.endswith("-latest") and str(record.get("name") or "").removeprefix("models/") == requested:   # a pinned id returns its own name too
        text += "  [the record of the alias itself: it does not say which model the alias points to]"
    return text


def _safe(fn, *a):
    try:
        return fn(*a)
    except ValueError:
        return False


def _list_models(provider: str) -> set[str]:
    key = os.environ.get(PROVIDER_KEYS[provider], "")
    body = request_json(base_url(provider) + "/models", headers={"Authorization": f"Bearer {key}"}, timeout=30)
    items = body.get("data", []) if isinstance(body, dict) else []
    return {str(i.get("id", "")).removeprefix("models/") for i in items}


def cmd_models(args, cfg) -> int:
    for name in sorted(_list_models(args.provider)):
        if not args.free or name.endswith(":free"):
            print(f"{args.provider}/{name}")
    return 0


def cmd_check(args, cfg) -> int:
    files = pipeline.read_bundle(ROOT)
    if not files:
        print("no export/studio bundle yet")
        return 0
    errors = contract.validate(files)
    print("\n".join(errors) or "export/studio satisfies the studio contract")
    return 1 if errors else 0


def cmd_rerender(args, cfg) -> int:
    report = pipeline.rerender(cfg, ROOT, args.slug)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if args.slug and args.slug in report["skipped"] else 0


def cmd_slides(args, cfg) -> int:
    from . import slides
    report = slides.write(ROOT, args.digests, everything=args.all, langs=args.lang)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if report["skipped"] else 0


def cmd_publish(args, cfg) -> int:
    """Push the results commit in the current checkout to a new branch and open a pull request (see radar/publish.py)."""
    from . import publish
    repo = args.repo or os.environ.get("GITHUB_REPOSITORY", "")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    run_url = f"{os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/{repo}/actions/runs/{run_id}" if repo and run_id.isdigit() else ""
    result = publish.publish(repo=repo, token=os.environ.get("RADAR_PR_TOKEN", ""), cwd=Path.cwd(), base=args.base,
                             automerge=os.environ.get("RADAR_AUTOMERGE", "").lower() == "true", run_url=run_url,
                             run_id=run_id, attempt=os.environ.get("GITHUB_RUN_ATTEMPT", "1"))
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] in ("opened", "branch-exists") else 1


def cmd_handoff(args, cfg) -> int:
    from . import handoff
    token = os.environ.get("STUDIO_REPO_TOKEN", "")
    if not token and not args.remote.startswith(("/", "file:")):
        print("STUDIO_REPO_TOKEN is not set: bundle stays in export/studio/ (copy it into the studio by hand)")
        return 0
    files = pipeline.read_bundle(ROOT)
    campaign = args.campaign or max((p.split("/")[1] for p in files if p.startswith("campaigns/")), default="")
    if not campaign:
        print("nothing to hand off")
        return 0
    errors = contract.validate({p: t for p, t in files.items() if p.startswith(f"campaigns/{campaign}/") or p.startswith("tools/")})
    if errors:
        print("\n".join(errors))
        return 1
    chosen = {p: t for p, t in files.items() if p.startswith(f"campaigns/{campaign}/") or p.startswith("tools/")}
    result = handoff.open_pr(chosen, remote=args.remote, repo=args.repo, campaign=campaign, token=token, base=args.base,
                             title=f"radar: {campaign} (draft posts)",
                             body="Draft posts from github-radar. Nothing is approved or published: review each post in the studio first.")
    print(json.dumps(result, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="radar", description="Scan top free GitHub repos, write visual digests, hand them to the studio.")
    parser.add_argument("--config", type=Path, default=None)
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name, fn, extra in (("scan", cmd_scan, ()), ("run", cmd_run, ("dry",)), ("doctor", cmd_doctor, ("ping",)),
                            ("check", cmd_check, ())):
        p = sub.add_parser(name)
        p.set_defaults(fn=fn)
        p.add_argument("--date", default=None, help="YYYY-MM-DD (default: today, UTC)")
        if name in ("scan", "run"):
            p.add_argument("--preset", default=None, help="saved scan conditions (python3 radar.py presets)")
            p.add_argument("--conditions", default=None, help="one-off conditions as JSON, e.g. '{\"picks_per_run\": 2}' (wins over --preset)")
        if "dry" in extra:
            p.add_argument("--dry-run", action="store_true", help="discover and rank only: no model calls, nothing written")
            p.add_argument("--repo", default=None, help="cover this one repository (owner/name or a github.com link) instead of searching")
            p.add_argument("--bucket", default=None, help="with --repo: ai, software, solutions or startup (default: from the repository's topics)")
        if "ping" in extra:
            p.add_argument("--ping", action="store_true", help="ask each provider whether the configured models still exist")
    p = sub.add_parser("presets", help="list the saved scan conditions and what each costs")
    p.set_defaults(fn=cmd_presets)
    p = sub.add_parser("models")
    p.set_defaults(fn=cmd_models)
    p.add_argument("provider", choices=sorted(PROVIDER_KEYS))
    p.add_argument("--free", action="store_true")
    p = sub.add_parser("rerender", help="draw digests, diagrams and studio posts again from the stored drafts (no model, no GitHub)")
    p.set_defaults(fn=cmd_rerender)
    p.add_argument("--slug", default=None, help="one run, e.g. 2026-10-12 (default: every run that has stored drafts)")
    p = sub.add_parser("slides", help="draw slides-<lang>.pptx beside the stored drafts of the chosen digests (no model, no GitHub, no Moda)")
    p.set_defaults(fn=cmd_slides)
    p.add_argument("digests", nargs="*", help="a run (2026-10-17-2) or one repository of it (2026-10-17-2/orca); several allowed")
    p.add_argument("--all", action="store_true", help="every stored digest (instead of naming them)")
    p.add_argument("--lang", action="append", default=None, help="only this language (repeatable); default: every stored draft")
    p = sub.add_parser("publish", help="push the committed results to a new branch and open a pull request (token: RADAR_PR_TOKEN)")
    p.set_defaults(fn=cmd_publish)
    p.add_argument("--repo", default=None, help="owner/name (default: GITHUB_REPOSITORY)")
    p.add_argument("--base", default="main")
    p = sub.add_parser("handoff")
    p.set_defaults(fn=cmd_handoff)
    p.add_argument("campaign", nargs="?", default="")
    p.add_argument("--remote", default="https://github.com/vohoailinh90/tool-marketing-studio.git")
    p.add_argument("--repo", default="vohoailinh90/tool-marketing-studio", help="owner/name for the pull request API")
    p.add_argument("--base", default="main")
    args = parser.parse_args(argv)
    try:
        # --preset / --conditions are the same conditions a workflow input carries (radar/conditions.py), given on the command line
        env = {**os.environ}
        if getattr(args, "preset", None) is not None:
            env["RADAR_PRESET"] = args.preset
        if getattr(args, "conditions", None) is not None:
            env["RADAR_CONDITIONS"] = args.conditions
        cfg = config.load(args.config, env)
        return args.fn(args, cfg)
    except (ValueError, HttpError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
