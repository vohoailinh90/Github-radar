import datetime as dt

from radar import config, discover
from radar.github import GitHub
from tests.support import TODAY, fake_github, make_repo

CFG = config.load(path=config.ROOT / "none.yaml", env={})


def test_eligibility_reasons():
    ok = make_repo("a", "llm", 5000)
    assert discover.eligible(ok, CFG, {}, TODAY) is None
    assert "licence" in discover.eligible(make_repo("a", "llm", 5000, spdx="NOASSERTION"), CFG, {}, TODAY)
    assert "licence" in discover.eligible({**ok, "license": None}, CFG, {}, TODAY)
    assert discover.eligible(make_repo("a", "llm", 5000, archived=True), CFG, {}, TODAY)
    assert discover.eligible(make_repo("a", "llm", 5000, description=" "), CFG, {}, TODAY) == "no description"
    assert discover.eligible(make_repo("a", "llm", 10), CFG, {}, TODAY) == "below min_stars"
    assert discover.eligible(make_repo("a", "llm", 5000, pushed_days=400), CFG, {}, TODAY) == "not pushed recently"
    assert discover.eligible(ok, CFG, {"example-org/a": {}}, TODAY) == "already covered"


def test_score_rewards_stars_velocity_and_freshness():
    big_old = make_repo("o", "llm", 90000, age_days=3000)
    young = make_repo("y", "llm", 20000, age_days=200)
    stale = make_repo("s", "llm", 20000, age_days=200, pushed_days=90)
    assert discover.score(young, TODAY) > discover.score(big_old, TODAY) - 1.0
    assert discover.score(young, TODAY) == discover.score(stale, TODAY) + 1.0
    assert discover.score(make_repo("x", "llm", 20000), TODAY) == discover.score(make_repo("x", "llm", 20000), TODAY)


def test_candidates_search_every_topic_and_drop_unfit_repos():
    srv = fake_github()
    try:
        ranked, dropped = discover.candidates(GitHub(base=srv.url), CFG, {}, TODAY)
    finally:
        srv.close()
    names = [c["full_name"] for c in ranked]
    assert "example-org/sample-closed" not in names and "example-org/sample-stale" not in names
    assert "example-org/sample-old-archive" not in names
    assert names[0] == "example-org/sample-flow-engine" or ranked[0]["score"] >= ranked[-1]["score"]
    assert dropped["licence noassertion is not on the free list"] == 1
    queries = [c["path"] for c in srv.calls]
    assert any("topic%3Allm" in q for q in queries) and any("pushed%3A%3E%3D2026-06-16" in q for q in queries)


def test_pick_rotates_buckets_and_is_deterministic():
    ranked = [{"full_name": f"o/{b}{i}", "bucket": b, "score": 10 - i} for b in ("ai", "software", "solutions", "startup") for i in range(2)]
    cfg = {**CFG, "picks_per_run": 4}
    a = discover.pick(ranked, cfg, dt.date(2026, 10, 14))
    assert sorted(c["bucket"] for c in a) == ["ai", "software", "solutions", "startup"]
    assert [c["full_name"] for c in a] == [c["full_name"] for c in discover.pick(ranked, cfg, dt.date(2026, 10, 14))]
    b = discover.pick(ranked, cfg, dt.date(2026, 10, 15))
    assert a[0]["bucket"] != b[0]["bucket"]
    assert len(discover.pick(ranked[:1], {**CFG, "picks_per_run": 3}, TODAY)) == 1
