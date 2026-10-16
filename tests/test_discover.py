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
    picked = discover.pick(ranked, {**CFG, "picks_per_run": 3}, TODAY)
    assert [c["full_name"] for c in picked if c.get("slot")] == ["o/new"]                 # only the pick that used the slot carries the flag
    assert not [c for c in ranked if c.get("slot")]                                       # the ranked candidates themselves are not marked
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


def _search_paths(srv):
    return [c["path"] for c in srv.calls if c["path"].startswith("/search")]


def test_a_busy_topic_cannot_hide_the_young_repositories_between_the_two_floors():
    hot = [make_repo(f"hot-{i}", "llm", 2000 + i, age_days=30) for i in range(16)]          # young and already above min_stars
    emerging = make_repo("sample-emerging", "llm", 600, age_days=40)                           # young, between 300 and 1500
    srv = fake_github([make_repo("giant", "llm", 90000, age_days=2000)] + hot + [emerging])
    try:
        ranked, _ = discover.candidates(GitHub(base=srv.url), CFG, {}, TODAY)
    finally:
        srv.close()
    assert "example-org/sample-emerging" in [c["full_name"] for c in ranked]               # the first rising page was all >= 2000
    band = [q for q in _search_paths(srv) if "stars%3A300..1499" in q]
    assert len(band) == 1 and "topic%3Allm" in band[0] and "created%3A%3E%3D2026-06-16" in band[0]    # one extra call, for this topic only


def test_a_quiet_topic_or_equal_floors_cost_no_extra_search():
    few = [make_repo(f"hot-{i}", "llm", 2000 + i, age_days=30) for i in range(3)] + [make_repo("sample-emerging", "llm", 600, age_days=40)]
    srv = fake_github(few)
    try:
        ranked, _ = discover.candidates(GitHub(base=srv.url), CFG, {}, TODAY)
    finally:
        srv.close()
    assert "example-org/sample-emerging" in [c["full_name"] for c in ranked]               # the unbounded rising query already reached it
    assert not [q for q in _search_paths(srv) if "..1499" in q]
    full = [make_repo(f"hot-{i}", "llm", 2000 + i, age_days=30) for i in range(16)]
    same = {**CFG, "rising": {**CFG["rising"], "min_stars": 1500}}                             # no band between equal floors
    srv = fake_github(full)
    try:
        discover.candidates(GitHub(base=srv.url), same, {}, TODAY)
    finally:
        srv.close()
    assert not [q for q in _search_paths(srv) if ".." in q]


def test_the_band_query_also_runs_when_a_lower_band_repo_that_is_already_covered_fills_the_last_place_of_the_page():
    hot = [make_repo(f"hot-{i}", "llm", 2000 + i, age_days=30) for i in range(14)]
    covered = make_repo("covered-lower", "llm", 700, age_days=40)                           # takes place 15 of the rising page
    emerging = make_repo("sample-emerging", "llm", 600, age_days=40)                         # hidden beyond it
    srv = fake_github([make_repo("giant", "llm", 90000, age_days=2000)] + hot + [covered, emerging])
    try:
        ranked, _ = discover.candidates(GitHub(base=srv.url), CFG, {"example-org/covered-lower": {"covered": "2026-09-01"}}, TODAY)
    finally:
        srv.close()
    assert "example-org/sample-emerging" in [c["full_name"] for c in ranked]
    assert len([q for q in _search_paths(srv) if "stars%3A300..1499" in q]) == 1             # a full page that reaches above the floor


def test_a_fast_climbing_repository_below_the_floor_wins_the_rising_slot_over_slower_proven_ones():
    # the lower-floor pass is not decoration: with measured velocity its repository outscores young repos above the floor
    hot = [make_repo(f"hot-{i}", "llm", 2000 + i, age_days=30) for i in range(5)]
    repos = [make_repo("giant", "llm", 90000, age_days=2000), make_repo("classic", "llm", 50000, age_days=2000),
             make_repo("sample-emerging", "llm", 1400, age_days=40)] + hot
    hist = {f"example-org/hot-{i}": {day(6): 1980 + i} for i in range(5)}                     # +20 stars in 6 days
    hist["example-org/sample-emerging"] = {day(6): 500}                                       # +900 stars in 6 days
    cfg = {**CFG, "picks_per_run": 2}
    srv = fake_github(repos)
    try:
        ranked, _ = discover.candidates(GitHub(base=srv.url), cfg, {}, TODAY, hist)
    finally:
        srv.close()
    names = [c["full_name"] for c in discover.pick(ranked, cfg, TODAY)]
    assert "example-org/sample-emerging" in names and not [n for n in names if "hot-" in n]
    assert "example-org/sample-emerging" not in [c["full_name"] for c in discover.pick(ranked, {**cfg, "rising": {**CFG["rising"], "slots": 0}}, TODAY)]


def test_one_pick_cannot_use_a_slot_so_the_rising_queries_are_not_sent():
    srv = fake_github([make_repo("old", "llm", 9000), young()])
    try:
        ranked, _ = discover.candidates(GitHub(base=srv.url), {**CFG, "picks_per_run": 1}, {}, TODAY)
    finally:
        srv.close()
    assert not [q for q in _search_paths(srv) if "created" in q]                      # half of one pick is zero slots
    assert [c["full_name"] for c in ranked] == ["example-org/old"]
