from ship_port_management.times import is_valid_iso_time


def test_iso_time_is_valid() -> None:
    assert is_valid_iso_time("2026-10-18T09:30")


def test_word_is_not_a_valid_time() -> None:
    assert not is_valid_iso_time("banana")


def test_empty_text_is_not_a_valid_time() -> None:
    assert not is_valid_iso_time("")


def test_impossible_date_is_not_a_valid_time() -> None:
    assert not is_valid_iso_time("2026-13-01T09:30")
