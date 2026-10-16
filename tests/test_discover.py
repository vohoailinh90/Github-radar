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


# ---- measured velocity, flags, and the rising pass --------------------------------------------------------------------

def day(n: int) -> str:
    return (TODAY - dt.timedelta(days=n)).isoformat()


def test_momentum_is_measured_when_a_snapshot_exists_and_lifetime_otherwise():
    repo = make_repo("a", "llm", 12000, age_days=1200)
    lifetime = discover.momentum(repo, TODAY)
    assert lifetime["source"] == "lifetime" and round(lifetime["per_30d"]) == 300           # 12000 / 1200 * 30
    hist = {"example-org/a": {day(6): 11400}}
    measured = discover.momentum(repo, TODAY, hist)
    assert measured["source"] == "measured" and measured["gap_days"] == 6 and measured["gained"] == 600
    assert round(measured["per_30d"]) == 3000                                              # 100 a day
    assert discover.score(repo, TODAY, hist) > discover.score(repo, TODAY)
    assert discover.score(repo, TODAY, {}) == discover.score(repo, TODAY)                   # no history: the old score exactly
    # the pre-snapshot formula by hand: ln(1+20000) + 0.5*ln(1 + 20000/700*30) + 1 (pushed 5 days ago)
    assert discover.score(make_repo("x", "llm", 20000), TODAY) == 14.2809


def test_a_repository_that_lost_stars_scores_like_one_that_gained_none():
    repo = make_repo("a", "llm", 12000)
    flat = discover.score(repo, TODAY, {"example-org/a": {day(5): 12000}})
    assert discover.score(repo, TODAY, {"example-org/a": {day(5): 12500}}) == flat


def test_flags_report_a_spike_and_few_forks_but_never_change_the_score():
    repo = {**make_repo("a", "llm", 10000), "forks_count": 20}                              # 2 forks per 1,000 stars
    hist = {"example-org/a": {day(5): 7000}}                                                # +30% in 5 days
    mom = discover.momentum(repo, TODAY, hist)
    assert discover.flags(repo, mom) == ["few-forks", "star-spike"]
    assert discover.flags(make_repo("b", "llm", 10000), discover.momentum(make_repo("b", "llm", 10000), TODAY)) == []
    assert discover.flags({**repo, "forks_count": 500}, discover.momentum(repo, TODAY)) == []   # lifetime numbers never spike


def young(name="sample-young-agent", stars=600, topic="llm", age=40, **kw):
    return make_repo(name, topic, stars, age_days=age, **kw)


def test_the_rising_pass_finds_young_repositories_below_the_stars_floor():
    srv = fake_github([make_repo("old", "llm", 9000), young()])
    try:
        ranked, dropped = discover.candidates(GitHub(base=srv.url), CFG, {}, TODAY)
    finally:
        srv.close()
    by = {c["full_name"]: c for c in ranked}
    assert by["example-org/sample-young-agent"]["rising"] is True and by["example-org/old"]["rising"] is False
    assert "below min_stars" not in dropped
    queries = [c["path"] for c in srv.calls if c["path"].startswith("/search")]
    assert any("created%3A%3E%3D2026-06-16" in q and "stars%3A%3E%3D300" in q for q in queries)
    assert any("stars%3A%3E%3D1500" in q and "created" not in q for q in queries)
    assert len(queries) == 2 * sum(len(b["topics"]) for b in CFG["buckets"])                  # two passes per topic


def test_the_rising_pass_can_be_switched_off():
    cfg = {**CFG, "rising": {**CFG["rising"], "slots": 0}}
    srv = fake_github([make_repo("old", "llm", 9000), young()])
    try:
        ranked, _ = discover.candidates(GitHub(base=srv.url), cfg, {}, TODAY)
    finally:
        srv.close()
    assert [c["full_name"] for c in ranked] == ["example-org/old"]
    assert not any("created" in c["path"] for c in srv.calls)


def test_an_old_repository_returned_by_the_rising_query_is_not_rising():
    class Stub:                                                  # a search that ignores created:>= (API noise)
        def search(self, query, per_page=15):
            return [make_repo("old-small", "llm", 400)]
    ranked, dropped = discover.candidates(Stub(), CFG, {}, TODAY)
    assert ranked == [] and dropped == {"below min_stars": sum(len(b["topics"]) for b in CFG["buckets"])}           # only the top pass counted it


def test_pick_reserves_a_slot_for_a_rising_repository_that_stars_alone_would_never_pick():
    top = [{"full_name": f"o/top{b}", "bucket": b, "score": 20, "rising": False} for b in ("ai", "software", "solutions", "startup")]
    rising = {"full_name": "o/new", "bucket": "startup", "score": 8, "rising": True}
    ranked = sorted(top + [rising], key=lambda c: -c["score"])
    names = [c["full_name"] for c in discover.pick(ranked, {**CFG, "picks_per_run": 3}, TODAY)]
    assert names[0] == "o/new" and len(names) == 3 and len(set(names)) == 3
    assert "o/new" not in [c["full_name"] for c in discover.pick(ranked, {**CFG, "picks_per_run": 1}, TODAY)]   # 1 pick: no slot
    off = {**CFG, "picks_per_run": 3, "rising": {**CFG["rising"], "slots": 0}}
    assert "o/new" not in [c["full_name"] for c in discover.pick(ranked, off, TODAY)]
    none = [c for c in ranked if not c["rising"]]
    assert len(discover.pick(none, {**CFG, "picks_per_run": 3}, TODAY)) == 3                  # nothing rising: the slot is not wasted


def test_a_rising_slot_reserves_at_most_half_the_picks():
    rising = [{"full_name": f"o/r{i}", "bucket": "ai", "score": 5 - i * 0.1, "rising": True} for i in range(4)]
    tops = [{"full_name": f"o/t{i}", "bucket": "ai", "score": 30 - i, "rising": False} for i in range(4)]
    cfg = {**CFG, "picks_per_run": 4, "rising": {**CFG["rising"], "slots": 4}}
    assert len(discover.pick(rising, cfg, TODAY)) == 4                                         # nothing else to take: they fill the run
    picked = discover.pick(sorted(rising + tops, key=lambda c: -c["score"]), cfg, TODAY)
    assert [c["full_name"] for c in picked] == ["o/r0", "o/r1", "o/t0", "o/t1"]               # 2 reserved of 4, the rest by score


def test_the_rising_slot_goes_to_a_repository_the_plain_ranking_did_not_pick():
    # one bucket: a classic, a young repository that already wins on merit, and a smaller young one the stars ranking never reaches
    ranked = [{"full_name": "o/classic", "bucket": "ai", "score": 20, "rising": False},
              {"full_name": "o/young-big", "bucket": "ai", "score": 15, "rising": True},
              {"full_name": "o/young-small", "bucket": "ai", "score": 8, "rising": True}]
    cfg = {**CFG, "picks_per_run": 2}
    off = {**cfg, "rising": {**CFG["rising"], "slots": 0}}
    assert {c["full_name"] for c in discover.pick(ranked, off, TODAY)} == {"o/classic", "o/young-big"}
    on = discover.pick(ranked, cfg, TODAY)
    assert {c["full_name"] for c in on} == {"o/classic", "o/young-small"}          # the reservation changed the picks, as documented
    assert on[0]["full_name"] == "o/young-small"                                    # the slot's pick comes first
    # nothing outside the plain picks to offer: they stay as they are
    assert {c["full_name"] for c in discover.pick(ranked[:2], cfg, TODAY)} == {"o/classic", "o/young-big"}
