#!/usr/bin/env python3
"""Claims on shared work: so two sessions never work the same item at once.

Several Claude or Codex sessions can work in this repository at the same time, each in its own checkout, so none of them can
see what another is doing. A claim is the answer: before starting an item (a repository `owner/name`, a report folder
`docs/reports/<name>`, a file path) a session claims it, and finishes by releasing it.

    python3 scripts/claim.py claim docs/reports/genai-agents --note "deck on Moda"
    python3 scripts/claim.py renew docs/reports/genai-agents
    python3 scripts/claim.py release docs/reports/genai-agents
    python3 scripts/claim.py list            # every item that has a claim, with its state
    python3 scripts/claim.py check KEY...    # exit 1 if another live session holds one (writes nothing)
    python3 scripts/claim.py prune           # the owner's tidy-up: delete old finished claim branches

Exit codes: 0 done, 1 held by another live session (or overlapping), 2 usage, 3 the remote cannot be reached or refused (the message says
whether anything was claimed: usually nothing, but a failed yield or rollback can leave a claim standing until it expires).

How it works. The ledger is one git branch per item on the remote, `claims/<slug>`. Its commits are an append-only log: each one has
an empty tree and carries the claim as JSON in its message, and the tip says who holds the item now. Every change (claim, renew,
release, take over) is a plain fast-forward push of a new commit on top of the tip the session just read. The server accepts exactly
one of any number of simultaneous pushes on one tip, so of several sessions that claim one item exactly one wins: that guarantee is
git's, not this script's. Nothing needs a force-push, a delete, a tag or a ref outside `refs/heads/`, which Claude Code on the web
refuses (tried: HTTP 403). No file is added to any tree, and CI runs only for `main` and pull requests, so a claim starts no run.

A claim expires (`--ttl`, default 2h; `renew` extends it), so a session that died does not block an item for ever. Only an expired or
released item can be claimed by another session. A folder claim and a claim on a file inside it overlap: the push is atomic for one
item, the overlap is not, so after pushing a claimant lists the live claims and yields (pushes a release) whenever another session's
live claim overlaps. Both may yield and retry; both can never stand.

Limits. Expiry compares clocks of different machines (skew shifts it by the skew). A finished item keeps its branch (a session on the
web cannot delete one): `prune` removes the old ones from a machine that may. Nothing forces an agent to call this script: it is the
tool the rules in CLAUDE.md ask for. `CLAIM_NOW` (UTC, `2026-10-24T23:50:00Z`) replaces the clock; the tests use it.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import secrets
import subprocess
import sys
import time
from dataclasses import dataclass

REF = "refs/heads/claims/"
CACHE = "refs/claims-cache/"          # local copy of the ledger, refreshed by every command
DEFAULT_TTL = 2 * 3600
MAX_TTL = 24 * 3600
RETRIES = 4
OK, HELD, USAGE, REMOTE = 0, 1, 2, 3
TIME = "%Y-%m-%dT%H:%M:%SZ"
SAFE_KEY = re.compile(r"[a-z0-9._/-]+")
SAFE_ID = re.compile(r"[A-Za-z0-9._:-]{1,64}")
SAFE_AGENT = re.compile(r"[a-z0-9_-]{1,20}")
IDENTITY = {"GIT_AUTHOR_NAME": "github-radar claims", "GIT_AUTHOR_EMAIL": "claims@users.noreply.github.com",
            "GIT_COMMITTER_NAME": "github-radar claims", "GIT_COMMITTER_EMAIL": "claims@users.noreply.github.com"}


class Usage(Exception):
    pass


class Remote(Exception):
    def __init__(self, text: str, partial: bool = False):
        super().__init__(text)
        self.partial = partial               # True: a claim of this session may still stand although the call failed


def now() -> dt.datetime:
    fixed = os.environ.get("CLAIM_NOW")
    return dt.datetime.strptime(fixed, TIME).replace(tzinfo=dt.timezone.utc) if fixed else dt.datetime.now(dt.timezone.utc)


def stamp(when: dt.datetime) -> str:
    return when.strftime(TIME)


def git(*args: str, data: str | None = None, env: dict | None = None) -> subprocess.CompletedProcess:
    full = {**os.environ, "GIT_TERMINAL_PROMPT": "0", **(env or {})}
    return subprocess.run(["git", *args], input=data, capture_output=True, text=True, env=full)


def plain(text: str) -> str:
    """Text read from the remote (a key, a note, a holder), safe to print: no terminal escape or other control character."""
    return re.sub(r"[\x00-\x1f\x7f-\x9f]", "?", str(text))


def failure(proc: subprocess.CompletedProcess) -> str:
    """One short line of what git said, without any credential a URL may carry."""
    text = (proc.stderr or proc.stdout or "git failed").strip().splitlines()
    return re.sub(r"://[^/@\s]+@", "://***@", text[-1] if text else "git failed")[:200]


def settle(proc: subprocess.CompletedProcess) -> bool:
    """For a push git refused: False when it only lost a race (the tip moved, the branch appeared first, the lease no longer holds), so
    reading the ledger again settles it. A refusal for any other reason (a hook, a policy, a missing right) raises Remote: retrying cannot help."""
    for line in proc.stdout.splitlines():
        if line.startswith("!\t"):
            detail = line.split("\t", 2)[-1]
            if detail.startswith("[rejected]") or any(s in detail for s in ("failed to update ref", "already exists", "cannot lock ref")):
                return False
            raise Remote(re.sub(r"://[^/@\s]+@", "://***@", detail)[:200])
    raise Remote(failure(proc))


def normalise(key: str) -> tuple[str, str, tuple[str, ...]]:
    """(key, slug, path segments). Lower case, one `/`-separated path of letters, digits, `.`, `_` and `-`: it becomes part of a
    branch name, so anything else, an absolute path and any `..` are refused."""
    text = "-".join(key.lower().split())
    if not text or len(text) > 300 or text.startswith("/") or ".." in text or not SAFE_KEY.fullmatch(text):
        raise Usage(f"{key[:60]!r} is not an item: use letters, digits . _ - and / (a repository, a folder or a file path), no ..")
    parts = tuple(p for p in text.split("/") if p not in ("", "."))
    if not parts:
        raise Usage(f"{key[:60]!r} is not an item")
    norm = "/".join(parts)
    readable = re.sub(r"-{2,}", "-", norm.replace("/", "-"))[:80].strip("-.")
    # the hash of the whole key makes the branch name unique per item: `a/b` and `a-b` read alike but are two items, and the name never
    # ends in `.lock`. The readable part is only for people looking at the branch list.
    return norm, "-".join(x for x in (readable, hashlib.sha1(norm.encode()).hexdigest()[:10]) if x), parts


def overlaps(a: tuple[str, ...], b: tuple[str, ...]) -> bool:
    n = min(len(a), len(b))
    return a[:n] == b[:n]


def span(text: str, flag: str, top: int, units: str = "smh") -> int:
    """Seconds from `90m`, `2h`, `30d` or a bare number of seconds, between 1 second and `top`."""
    m = re.fullmatch(r"(\d{1,6})([smhd]?)", text.strip())
    seconds = int(m[1]) * {"": 1, "s": 1, "m": 60, "h": 3600, "d": 86400}[m[2]] if m and (m[2] in units or not m[2]) else 0
    if not 1 <= seconds <= top:
        raise Usage(f"{flag} {text[:20]!r}: use a number with one of {', '.join(units)} (up to {top // 3600}h), for example 90m")
    return seconds


@dataclass
class Claim:
    slug: str
    sha: str                     # the tip of the item's branch
    record: dict | None          # None: the tip is not one of ours (a branch someone else made under claims/)
    committed: int | None        # commit time (epoch)

    @property
    def session(self) -> str | None:
        return self.record["session"] if self.record else None

    @property
    def key(self) -> str:
        return plain(self.record["key"]) if self.record else f"({self.slug})"

    @property
    def released(self) -> bool:
        return bool(self.record) and self.record.get("state") == "released"

    @property
    def segments(self) -> tuple[str, ...] | None:
        return tuple(self.record["key"].split("/")) if self.record else None

    def taken(self) -> dt.datetime | None:
        if self.record:
            return dt.datetime.strptime(self.record["taken_at"], TIME).replace(tzinfo=dt.timezone.utc)
        return dt.datetime.fromtimestamp(self.committed, dt.timezone.utc) if self.committed is not None else None

    def expires(self) -> dt.datetime | None:
        """None: never (a branch of unknown origin with no commit time)."""
        start = self.taken()
        if start is None:
            return None
        return start + dt.timedelta(seconds=self.record["ttl_s"] if self.record else DEFAULT_TTL)

    def live(self, at: dt.datetime) -> bool:
        if self.released:
            return False
        end = self.expires()
        return end is None or at < end

    def state(self, at: dt.datetime) -> str:
        return "released" if self.released else ("live" if self.live(at) else "expired")

    def holder(self) -> str:
        if not self.record:
            return f"unknown (a branch made by hand: git push origin :{REF}{self.slug})"
        return plain(f"{self.record['session']} ({self.record.get('agent', 'unknown')})")


def valid(record) -> bool:
    try:
        return (isinstance(record, dict) and isinstance(record["key"], str) and isinstance(record["session"], str)
                and type(record["ttl_s"]) is int and 0 < record["ttl_s"] <= MAX_TTL
                and record.get("state", "claimed") in ("claimed", "released")
                and dt.datetime.strptime(record["taken_at"], TIME) is not None)
    except (KeyError, ValueError, TypeError):
        return False


class Ledger:
    def __init__(self, remote: str, session: str, agent: str):
        self.remote, self.session, self.agent = remote, session, agent

    def claims(self) -> dict[str, Claim]:
        """The tip of every item's branch, freshly fetched."""
        fetched = git("fetch", "-q", "--no-tags", "--prune", self.remote, f"+{REF}*:{CACHE}*")
        if fetched.returncode:
            time.sleep(0.3)                           # a server busy with another push can drop one request: ask once more
            fetched = git("fetch", "-q", "--no-tags", "--prune", self.remote, f"+{REF}*:{CACHE}*")
        if fetched.returncode:
            raise Remote(failure(fetched))
        listed = git("for-each-ref", "--format=%(refname)%1f%(objectname)%1f%(committerdate:unix)%1f%(contents:subject)%1e", CACHE)
        out: dict[str, Claim] = {}
        for row in listed.stdout.split("\x1e"):
            row = row.strip("\n")
            if not row:
                continue
            ref, sha, when, subject = (row.split("\x1f") + ["", "", "", ""])[:4]
            try:
                record = json.loads(subject)
            except ValueError:
                record = None
            out[ref[len(CACHE):]] = Claim(ref[len(CACHE):], sha, record if valid(record) else None, int(when) if when.isdigit() else None)
        return out

    def tip(self, slug: str) -> str | None:
        """Where the branch is on the remote right now (None: there is none)."""
        out = git("ls-remote", self.remote, f"{REF}{slug}")
        if out.returncode:
            raise Remote(failure(out))
        return out.stdout.split()[0] if out.stdout.strip() else None

    def push(self, slug: str, sha: str, parent: str | None) -> bool:
        """A fast-forward push of `sha`, built on `parent` (None: the first push of the branch). True: done. False: somebody else won
        the race. Remote: the server refused for another reason, or could not be reached.

        Who won is decided by where the branch is now, not by what git called the refusal (that text differs between git versions and
        servers, and a server that dies on a lock says nothing at all): if the branch is no longer where we built on it, we lost. Only a
        refusal with the branch unmoved (a hook, a policy, an outage) is an error, and it gets one more try first."""
        reason = "git push failed"
        for attempt in range(2):
            proc = git("push", "--porcelain", self.remote, f"{sha}:{REF}{slug}")
            if proc.returncode == 0:
                return True
            if self.tip(slug) != parent:
                return False
            try:
                if not settle(proc):
                    return False                      # git itself says it lost a race, and nothing contradicts it
            except Remote as exc:
                reason = str(exc)
            if attempt == 0:
                time.sleep(0.3)
        raise Remote(reason)

    def make(self, key: str, ttl: int, note: str, parent: str | None = None, state: str = "claimed") -> str:
        record = {"v": 1, "key": key, "session": self.session, "agent": self.agent, "taken_at": stamp(now()), "ttl_s": ttl,
                  "state": state, "note": note[:200], "nonce": secrets.token_hex(4)}
        tree = git("hash-object", "-t", "tree", "-w", "--stdin", data="").stdout.strip()
        when = {"GIT_AUTHOR_DATE": record["taken_at"], "GIT_COMMITTER_DATE": record["taken_at"]}
        made = git("commit-tree", tree, *(["-p", parent] if parent else []), "-m", json.dumps(record, sort_keys=True, separators=(",", ":")),
                   env={**IDENTITY, **when})
        if made.returncode:
            raise Remote(failure(made))
        return made.stdout.strip()

    def let_go(self, c: Claim, note: str) -> bool:
        """Release (or yield) by pushing a `released` commit on the tip we read."""
        return self.push(c.slug, self.make(c.record["key"] if c.record else c.slug, 1, note, parent=c.sha, state="released"), c.sha)

    def take(self, key: str, slug: str, segments: tuple[str, ...], ttl: int, note: str) -> tuple[str, Claim | None]:
        """('claimed' | 'renewed' | 'took over', None) or ('held' | 'overlap', the claim in the way)."""
        for _ in range(RETRIES):
            seen, at = self.claims().get(slug), now()
            if seen and seen.session != self.session and seen.live(at):
                return "held", seen
            sha = self.make(key, ttl, note, parent=seen.sha if seen else None)
            if seen is None or seen.released:
                how = "claimed"
            elif seen.session == self.session:
                how = "renewed" if seen.live(at) else "claimed"     # a lapsed claim of ours is not a renewal: somebody may have overlapped it since
            else:
                how = "took over"
            if not self.push(slug, sha, seen.sha if seen else None):
                continue                       # somebody pushed first, between our read and our write: read again
            if how != "renewed":
                try:
                    rival = self.rival(slug, segments)
                except Remote as exc:                      # pushed, but could not check for overlap: that is not a claim worth having
                    try:
                        self.push(slug, self.make(key, 1, "withdrawn: the overlap check failed", parent=sha, state="released"), sha)
                    except Remote:
                        raise Remote(f"{exc}; the claim on {key} may still stand until it expires", partial=True) from exc
                    raise
                if rival:
                    try:
                        self.push(slug, self.make(key, 1, "yielded: overlaps another claim", parent=sha, state="released"), sha)
                    except Remote as exc:
                        raise Remote(f"{exc}; the claim on {key} may still stand until it expires", partial=True) from exc
                    return "overlap", rival
            return how, None
        raise Remote("the ledger kept changing under this claim; try again")

    def rival(self, slug: str, segments: tuple[str, ...]) -> Claim | None:
        at = now()
        for other in self.claims().values():
            if other.slug != slug and other.session != self.session and other.live(at) \
                    and other.segments and overlaps(segments, other.segments):
                return other
        return None


def session_id(given: str | None) -> str:
    chosen = given or next((os.environ[v] for v in ("CLAIM_SESSION", "CLAUDE_SESSION_ID", "CODEX_SESSION_ID") if os.environ.get(v)), "")
    if not chosen:
        where = git("rev-parse", "--absolute-git-dir")
        if where.returncode:
            raise Usage("not inside a git checkout")
        path = os.path.join(where.stdout.strip(), "claim-session")
        try:
            with open(path, encoding="utf-8") as fh:
                chosen = fh.read().strip()
        except OSError:
            chosen = ""
        if not SAFE_ID.fullmatch(chosen):
            chosen = "s-" + secrets.token_hex(4)
            try:
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(chosen + "\n")
            except OSError as exc:
                raise Usage(f"cannot keep a session id in {os.path.dirname(path)} ({exc.strerror}): pass --session") from exc
    if not SAFE_ID.fullmatch(chosen):
        raise Usage(f"session id {chosen[:30]!r}: use letters, digits . _ : - (at most 64)")
    return chosen


def until(c: Claim) -> str:
    end = c.expires()
    return stamp(end) if end else "never"


def give_back(led: Ledger, slugs: list[str]) -> list[str]:
    """Release what this call took (all or nothing). Best effort: the slugs that could not be released are returned."""
    stuck = []
    for slug in slugs:
        try:
            mine = led.claims().get(slug)
            if mine and mine.session == led.session and not mine.released and not led.let_go(mine, "rolled back: the call did not complete"):
                stuck.append(slug)
        except Remote:
            stuck.append(slug)
    return stuck


def cmd_claim(led: Ledger, args) -> int:
    ttl, items, fresh = span(args.ttl, "--ttl", MAX_TTL), [normalise(k) for k in args.keys], []
    for key, slug, segments in items:
        try:
            how, other = led.take(key, slug, segments, ttl, args.note)
        except Remote as exc:
            stuck = give_back(led, fresh)
            if stuck or exc.partial:
                raise Remote(f"{exc}; claims that may still stand until they expire: {', '.join(stuck) or key}", partial=True) from exc
            raise
        if other:
            stuck = give_back(led, fresh)            # all or nothing: give back what this call took
            why = "overlaps a claim of" if how == "overlap" else "is held by"
            print(f"HELD {key}: {why} {other.key} -> {other.holder()} until {until(other)}")
            if stuck:
                print(f"claim: could not give back {', '.join(stuck)}; they stand until they expire (release them when the ledger answers)", file=sys.stderr)
            return HELD
        if how != "renewed":
            fresh.append(slug)
        print(f"{how} {key} until {stamp(now() + dt.timedelta(seconds=ttl))} (session {led.session})")
    return OK


def cmd_renew(led: Ledger, args) -> int:
    ttl, items = span(args.ttl, "--ttl", MAX_TTL), [normalise(k) for k in args.keys]
    claims = led.claims()
    for key, slug, _ in items:
        mine = claims.get(slug)
        if not mine or mine.released or mine.session != led.session:
            print(f"NOT YOURS {key}: " + (f"held by {mine.holder()}" if mine and not mine.released else "nobody holds it"))
            return HELD
    for key, slug, segments in items:
        how, other = led.take(key, slug, segments, ttl, args.note)
        if other:
            print(f"HELD {key}: {other.key} -> {other.holder()}")
            return HELD
        print(f"{how} {key} until {stamp(now() + dt.timedelta(seconds=ttl))}")
    return OK


def cmd_release(led: Ledger, args) -> int:
    claims, code = led.claims(), OK
    for key, slug, _ in [normalise(k) for k in args.keys]:
        mine = claims.get(slug)
        if not mine or mine.released:
            print(f"not held {key}")
        elif mine.session != led.session and mine.live(now()) and not args.force:
            print(f"REFUSED {key}: held by {mine.holder()}; only its holder releases it while it lasts (the owner may use --force)")
            code = HELD
        elif led.let_go(mine, "released" if mine.session == led.session else "released by force"):
            print(f"released {key}")
        else:
            print(f"changed {key}: someone else updated it just now; nothing released")
    return code


def cmd_check(led: Ledger, args) -> int:
    claims, at, code = led.claims(), now(), OK
    for key, slug, segments in [normalise(k) for k in args.keys]:
        blockers = [c for c in claims.values() if c.session != led.session and c.live(at)
                    and (c.slug == slug or (c.segments and overlaps(segments, c.segments)))]
        if blockers:
            print(f"HELD {key}: {blockers[0].key} -> {blockers[0].holder()} until {until(blockers[0])}")
            code = HELD
        else:
            print(f"free {key}")
    return code


def cmd_list(led: Ledger, args) -> int:
    at, rows = now(), []
    for c in sorted(led.claims().values(), key=lambda c: c.slug):
        state = c.state(at)
        if args.live and state != "live":
            continue
        rows.append({"key": c.key, "state": state, "holder": c.holder(), "until": until(c),
                     "note": plain((c.record or {}).get("note", "")), "mine": c.session == led.session})
    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return OK
    if not rows:
        print("no claims")
    for r in rows:
        print(f"{r['state']:<8} {r['key']:<40} {r['holder']}  until {r['until']}" + ("  (you)" if r["mine"] else "")
              + (f"  {r['note']}" if r["note"] else ""))
    return OK


def cmd_prune(led: Ledger, args) -> int:
    """Delete the branch of every item that was released or expired at least `--older` ago. Needs a machine that may delete branches."""
    older, at, code = span(args.older, "--older", 365 * 86400, units="smhd"), now(), OK
    for c in sorted(led.claims().values(), key=lambda c: c.slug):
        since = c.taken()
        if c.record is None or c.live(at) or since is None or (at - since).total_seconds() < older:
            continue                                  # a branch someone made by hand under claims/ is theirs to delete
        if args.dry_run:
            print(f"would delete {c.key} ({c.state(at)} since {stamp(since)})")
            continue
        proc = git("push", "--porcelain", f"--force-with-lease={REF}{c.slug}:{c.sha}", led.remote, f":{REF}{c.slug}")
        try:
            if proc.returncode == 0:
                print(f"deleted {c.key}")
            else:
                settle(proc)                          # a lost race returns; any other refusal raises
                print(f"changed {c.key}: updated just now; kept")
        except Remote as exc:
            print(f"claim: cannot delete {c.key} from here ({exc}); run prune on a machine that may delete branches", file=sys.stderr)
            return REMOTE
    return code


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--remote", default="origin", help="the git remote that holds the ledger (default: origin)")
    common.add_argument("--session", default=None, help="this session's id (default: CLAIM_SESSION, CLAUDE_SESSION_ID, "
                        "CODEX_SESSION_ID, else a random id kept in this checkout's git dir); give each session sharing one checkout its own")
    common.add_argument("--agent", default=os.environ.get("CLAIM_AGENT", "unknown"), help="claude, codex, human ... (a label)")
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], allow_abbrev=False)
    sub = parser.add_subparsers(dest="command", required=True)
    for name, fn, text in (("claim", cmd_claim, "take every item or none"), ("renew", cmd_renew, "extend claims you hold"),
                           ("release", cmd_release, "give claims back"), ("check", cmd_check, "is any item held by another live session? (writes nothing)")):
        p = sub.add_parser(name, parents=[common], help=text, description=text, allow_abbrev=False)
        p.add_argument("keys", nargs="+", metavar="ITEM")
        p.set_defaults(fn=fn)
        if name in ("claim", "renew"):
            p.add_argument("--ttl", default=f"{DEFAULT_TTL // 3600}h", help="how long the claim lasts, e.g. 90m (default 2h, at most 24h)")
            p.add_argument("--note", default="", help="a few words on what you are doing")
        if name == "release":
            p.add_argument("--force", action="store_true", help="release a claim of another session (the owner's call)")
    p = sub.add_parser("list", parents=[common], help="show the claims", allow_abbrev=False)
    p.add_argument("--live", action="store_true", help="only claims that have not expired or been released")
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_list)
    p = sub.add_parser("prune", parents=[common], help="delete the branches of old finished claims (the owner's tidy-up)", allow_abbrev=False)
    p.add_argument("--older", default="30d", help="finished at least this long ago (default 30d)")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(fn=cmd_prune)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if not SAFE_AGENT.fullmatch(args.agent):
            raise Usage("--agent: use lower-case letters, digits, _ and - (at most 20)")
        if git("rev-parse", "--git-dir").returncode:
            raise Usage("not inside a git checkout")
        return args.fn(Ledger(args.remote, session_id(args.session), args.agent), args)
    except Usage as exc:
        print(f"claim: {exc}", file=sys.stderr)
        return USAGE
    except Remote as exc:
        left = "a claim of yours may still stand until it expires: run list, and release it when the ledger answers" if exc.partial else "nothing was claimed"
        print(f"claim: the ledger cannot be used ({exc}); {left}. Do not work the item unclaimed: report it.", file=sys.stderr)
        return REMOTE


if __name__ == "__main__":
    sys.exit(main())
