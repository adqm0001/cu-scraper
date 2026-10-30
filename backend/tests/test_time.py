from datetime import datetime, timedelta, timezone

from db import to_utc_iso


def test_naive_timestamp_is_marked_as_utc():
    assert to_utc_iso(datetime(2026, 10, 30, 6, 1)) == "2026-10-30T06:01:00+00:00"


def test_aware_timestamp_keeps_its_offset():
    eastern = timezone(timedelta(hours=-4))
    assert to_utc_iso(datetime(2026, 10, 30, 2, 1, tzinfo=eastern)) == "2026-10-30T02:01:00-04:00"


def test_missing_timestamp_returns_none():
    assert to_utc_iso(None) is None
