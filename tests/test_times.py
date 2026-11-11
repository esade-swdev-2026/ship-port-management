from datetime import datetime

import pytest

from ship_port_management.times import current_time, parse_time


def test_iso_time_is_parsed() -> None:
    assert parse_time("2026-10-18T09:30", "arrival time") == datetime(2026, 10, 18, 9, 30)


def test_word_is_refused_with_its_label() -> None:
    with pytest.raises(ValueError, match="arrival time must look like"):
        parse_time("banana", "arrival time")


def test_empty_text_is_refused() -> None:
    with pytest.raises(ValueError, match="must look like"):
        parse_time("", "arrival time")


def test_impossible_date_is_refused() -> None:
    with pytest.raises(ValueError, match="must look like"):
        parse_time("2026-13-01T09:30", "arrival time")


def test_time_with_timezone_is_refused() -> None:
    with pytest.raises(ValueError, match="without a timezone"):
        parse_time("2026-10-18T10:00+01:00", "arrival time")


def test_current_time_can_be_parsed_back() -> None:
    assert parse_time(current_time(), "now").tzinfo is None
