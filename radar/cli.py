"""Command line: scan, run, doctor, models, handoff, check."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

from . import config, contract, pipeline
from .github import GitHub
from .llm import PROVIDER_KEYS, Gateway, base_url, family, has_key, split_model
from .net import HttpError, request_json

ROOT = config.ROOT


def _date(value: str | None) -> dt.date:
    return dt.date.fromisoformat(value) if value else dt.datetime.now(dt.timezone.utc).date()


def cmd_scan(args, cfg) -> int:
    from . import discover, facts
    gh = GitHub()
    seen = facts.load_seen(ROOT / "state" / "seen.json")
    ranked, dropped = discover.candidates(gh, cfg, seen, _date(args.date))
    for c in ranked[:20]:
        print(f"{c['score']:7.3f}  {c['bucket']:<10} {c['repo']['stargazers_count']:>7,}  {c['full_name']}")
    print(f"dropped: {json.dumps(dropped, ensure_ascii=False)}")
    return 0 if ranked else 1


def cmd_run(args, cfg) -> int:
    report = pipeline.run(cfg, GitHub(), Gateway(), ROOT, _date(args.date), dry_run=args.dry_run,
                          pace=float(cfg.get("pace_seconds", 3)))
    print(json.dumps({k: v for k, v in report.items() if k != "models_log"}, indent=2, ensure_ascii=False))
    return 0 if report["ok"] else 1


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
            for model in {m for ids in models.values() for m in ids if m.startswith(provider + "/")}:
                found = split_model(model)[1] in listed
                print(f"{'ok  ' if found else 'FAIL'}  {model} {'is offered' if found else 'is not offered by ' + provider + ' any more'}")
                bad += not found
    return 1 if bad else 0


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
        if "dry" in extra:
            p.add_argument("--dry-run", action="store_true", help="discover and rank only: no model calls, nothing written")
        if "ping" in extra:
            p.add_argument("--ping", action="store_true", help="ask each provider whether the configured models still exist")
    p = sub.add_parser("models")
    p.set_defaults(fn=cmd_models)
    p.add_argument("provider", choices=sorted(PROVIDER_KEYS))
    p.add_argument("--free", action="store_true")
    p = sub.add_parser("rerender", help="draw digests, diagrams and studio posts again from the stored drafts (no model, no GitHub)")
    p.set_defaults(fn=cmd_rerender)
    p.add_argument("--slug", default=None, help="one run, e.g. 2026-10-12 (default: every run that has stored drafts)")
    p = sub.add_parser("handoff")
    p.set_defaults(fn=cmd_handoff)
    p.add_argument("campaign", nargs="?", default="")
    p.add_argument("--remote", default="https://github.com/vohoailinh90/tool-marketing-studio.git")
    p.add_argument("--repo", default="vohoailinh90/tool-marketing-studio", help="owner/name for the pull request API")
    p.add_argument("--base", default="main")
    args = parser.parse_args(argv)
    try:
        cfg = config.load(args.config)
        return args.fn(args, cfg)
    except (ValueError, HttpError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
