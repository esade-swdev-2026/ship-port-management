import pytest

from ship_port_management.departures import (
    Departure,
    depart_ship,
    describe_departure,
    hours_at_dock,
)
from ship_port_management.dockings import Docking
from ship_port_management.docks import Dock

DOCKED_AT = "2026-10-14T10:00"
NORTH = Dock("North", 500, 120.0)
SOUTH = Dock("South", 300, 80.5)
ATLAS_AT_NORTH = Docking("IMO9074729", "North", DOCKED_AT)
NOVA_AT_SOUTH = Docking("IMO9012328", "South", DOCKED_AT)
DOCKINGS = [ATLAS_AT_NORTH, NOVA_AT_SOUTH]
DOCKS = [NORTH, SOUTH]


def test_whole_hours_are_counted_exactly() -> None:
    assert hours_at_dock(DOCKED_AT, "2026-10-14T12:00") == 2


def test_a_partial_hour_rounds_up() -> None:
    assert hours_at_dock(DOCKED_AT, "2026-10-14T15:20") == 6


def test_one_minute_past_the_docking_time_is_a_started_hour() -> None:
    assert hours_at_dock(DOCKED_AT, "2026-10-14T10:01") == 1


def test_departing_at_the_docking_time_costs_nothing() -> None:
    departure = depart_ship("IMO9074729", DOCKED_AT, DOCKINGS, DOCKS).departure
    assert departure.hours == 0
    assert departure.docking_fee == 0.0


def test_departing_before_docking_is_refused() -> None:
    with pytest.raises(ValueError, match="before docking time"):
        hours_at_dock(DOCKED_AT, "2026-10-14T09:00")


def test_departure_time_that_is_not_a_time_is_refused() -> None:
    with pytest.raises(ValueError, match="departure time"):
        hours_at_dock(DOCKED_AT, "banana")


def test_departure_time_with_timezone_is_refused() -> None:
    with pytest.raises(ValueError, match="without a timezone"):
        hours_at_dock(DOCKED_AT, "2026-10-14T12:00+01:00")


def test_docking_fee_is_hours_times_hourly_rate() -> None:
    departure = depart_ship("IMO9012328", "2026-10-14T14:00", DOCKINGS, DOCKS).departure
    assert departure.docking_fee == 322.0


def test_departing_frees_only_the_ships_dock() -> None:
    result = depart_ship("IMO9074729", "2026-10-14T12:00", DOCKINGS, DOCKS)
    assert result.dockings == [NOVA_AT_SOUTH]


def test_depart_ship_leaves_the_original_list_unchanged() -> None:
    dockings = [ATLAS_AT_NORTH, NOVA_AT_SOUTH]
    depart_ship("IMO9074729", "2026-10-14T12:00", dockings, DOCKS)
    assert dockings == [ATLAS_AT_NORTH, NOVA_AT_SOUTH]


def test_departing_an_undocked_ship_is_refused() -> None:
    with pytest.raises(ValueError, match="is not docked"):
        depart_ship("IMO9074729", "2026-10-14T12:00", [NOVA_AT_SOUTH], DOCKS)


def test_departing_from_a_dock_that_no_longer_exists_is_refused() -> None:
    with pytest.raises(ValueError, match="does not exist"):
        depart_ship("IMO9074729", "2026-10-14T12:00", DOCKINGS, [SOUTH])


def test_describe_departure_shows_the_hours_and_fee() -> None:
    departure = Departure("IMO9074729", "North", DOCKED_AT, "2026-10-14T15:20", 6, 720.0)
    assert describe_departure(departure) == (
        "IMO9074729 left North after 6 hours, docking fee 720.00"
    )


def test_describe_departure_says_hour_for_a_single_hour() -> None:
    departure = Departure("IMO9074729", "North", DOCKED_AT, "2026-10-14T10:01", 1, 120.0)
    assert describe_departure(departure) == (
        "IMO9074729 left North after 1 hour, docking fee 120.00"
    )
