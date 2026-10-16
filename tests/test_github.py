import pytest

from radar.github import GitHub
from radar.net import HttpError
from tests.support import _Server


def scripted(*answers):
    """A server that gives these (status, body, headers) in order and then repeats the last."""
    it = iter(answers)
    last = []

    def handle(call):
        try:
            last[:] = [next(it)]
        except StopIteration:
            pass
        return last[0]
    return _Server(handle)


def test_searches_are_spaced_by_the_configured_interval():
    srv = scripted((200, {"items": []}))
    now, waits = [100.0], []

    def sleep(s):
        waits.append(round(s, 2))
        now[0] += s
    try:
        gh = GitHub(base=srv.url, sleep=sleep, clock=lambda: now[0], search_interval=2.1)
        gh.search("q1")
        gh.search("q2")                                        # right after the first: waits the full interval
        now[0] += 5.0
        gh.search("q3")                                        # 5 s later: nothing to wait for
    finally:
        srv.close()
    assert waits == [2.1] and len(srv.calls) == 3


def test_no_interval_means_no_waiting():
    srv = scripted((200, {"items": []}))
    waits = []
    try:
        gh = GitHub(base=srv.url, sleep=waits.append)
        gh.search("a")
        gh.search("b")
    finally:
        srv.close()
    assert waits == []


def test_a_secondary_rate_limit_waits_for_retry_after_then_succeeds():
    srv = scripted((403, {"message": "secondary rate limit"}, {"Retry-After": "7"}), (200, {"items": [{"full_name": "o/a"}]}))
    waits = []
    try:
        assert GitHub(base=srv.url, sleep=waits.append).search("q") == [{"full_name": "o/a"}]
    finally:
        srv.close()
    assert waits == [8] and len(srv.calls) == 2


def test_a_retry_after_longer_than_a_minute_fails_fast_instead_of_stalling_the_run():
    srv = scripted((429, {"message": "slow down"}, {"Retry-After": "900"}))
    waits = []
    try:
        with pytest.raises(HttpError) as err:
            GitHub(base=srv.url, sleep=waits.append).search("q")
    finally:
        srv.close()
    assert err.value.status == 429 and waits == [2, 4] and len(srv.calls) == 3          # only the ordinary backoff for a 429


def test_a_plain_403_is_not_retried():
    srv = scripted((403, {"message": "API rate limit exceeded"}))
    waits = []
    try:
        with pytest.raises(HttpError) as err:
            GitHub(base=srv.url, sleep=waits.append).search("q")
    finally:
        srv.close()
    assert err.value.status == 403 and waits == [] and len(srv.calls) == 1
