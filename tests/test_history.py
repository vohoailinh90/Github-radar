import datetime as dt

from radar import history

D = dt.date(2026, 10, 14)


def day(n: int) -> str:
    return (D - dt.timedelta(days=n)).isoformat()


def test_a_second_observation_the_same_day_replaces_the_first():
    h = {}
    history.record(h, "o/a", D, 100)
    history.record(h, "o/a", D, 120)
    assert h == {"o/a": {D.isoformat(): 120}}


def test_velocity_divides_by_the_real_gap_not_the_nominal_window():
    h = {"o/a": {day(4): 1000}}
    v = history.velocity(h, "o/a", 1100, D)
    assert v == {"per_day": 25.0, "gap_days": 4, "gained": 100}


def test_velocity_prefers_the_observation_closest_to_a_week():
    h = {"o/a": {day(3): 1090, day(8): 1000, day(20): 800}}
    assert history.velocity(h, "o/a", 1100, D)["gap_days"] == 8        # |8-7| beats |3-7|
    assert history.velocity({"o/a": {day(3): 1090, day(20): 800}}, "o/a", 1100, D)["gap_days"] == 3


def test_unknown_is_none_never_zero():
    assert history.velocity({}, "o/a", 1100, D) is None
    assert history.velocity({"o/b": {day(5): 1}}, "o/a", 1100, D) is None
    for gap in (0, 2, 22, 60):                                           # today's own point, too fresh, too old
        assert history.velocity({"o/a": {day(gap): 1000}}, "o/a", 1100, D) is None, gap


def test_a_repository_that_lost_stars_reports_a_negative_velocity_for_the_caller_to_clamp():
    assert history.velocity({"o/a": {day(5): 1000}}, "o/a", 990, D)["per_day"] == -2.0


def test_a_malformed_stored_date_is_ignored_not_fatal():
    assert history.velocity({"o/a": {"yesterday": 5, day(5): 1000}}, "o/a", 1100, D)["gained"] == 100


def test_prune_drops_old_points_and_empty_repositories():
    h = {"o/a": {day(100): 1, day(5): 2}, "o/gone": {day(100): 3}}
    history.prune(h, D, 60)
    assert h == {"o/a": {day(5): 2}}


def test_save_and_load_round_trip_and_a_missing_file_is_empty(tmp_path):
    path = tmp_path / "state" / "stars.json"
    assert history.load(path) == {}
    history.save(path, {"o/b": {"2026-10-01": 2}, "o/a": {"2026-10-01": 1}})
    assert history.load(path) == {"o/a": {"2026-10-01": 1}, "o/b": {"2026-10-01": 2}}
    assert path.read_text(encoding="utf-8").index('"o/a"') < path.read_text(encoding="utf-8").index('"o/b"')   # stable diffs
    assert not path.with_suffix(".tmp").exists()
