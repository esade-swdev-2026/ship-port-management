import pytest

from ship_port_management.departures import Departure
from ship_port_management.ships import Ship
from ship_port_management.visits import (
    LOADED,
    UNLOADED,
    CargoTransfer,
    Visit,
    describe_visit,
    record_transfer,
    units_moved,
    visit_history,
)

ARRIVED_AT = "2026-10-18T09:30"
FIRST_DOCKING = "2026-10-18T10:00"
SECOND_DOCKING = "2026-10-20T08:00"
ATLAS = Ship("MV-ATLAS", "Atlas", ARRIVED_AT, 500, 40)
FIRST_VISIT = Departure("MV-ATLAS", "D1", FIRST_DOCKING, "2026-10-18T15:20", 6, 720.0)
SECOND_VISIT = Departure("MV-ATLAS", "D2", SECOND_DOCKING, "2026-10-20T09:00", 1, 90.0)
UNLOAD_30 = CargoTransfer("MV-ATLAS", FIRST_DOCKING, "W-NORTH", UNLOADED, 30)
LOAD_10 = CargoTransfer("MV-ATLAS", FIRST_DOCKING, "W-NORTH", LOADED, 10)
UNLOAD_5_LATER = CargoTransfer("MV-ATLAS", SECOND_DOCKING, "W-NORTH", UNLOADED, 5)


def test_record_transfer_adds_it_at_the_end() -> None:
    assert record_transfer(LOAD_10, [UNLOAD_30]) == [UNLOAD_30, LOAD_10]


def test_record_transfer_leaves_the_original_list_unchanged() -> None:
    transfers = [UNLOAD_30]
    record_transfer(LOAD_10, transfers)
    assert transfers == [UNLOAD_30]


def test_unknown_direction_is_refused() -> None:
    sideways = CargoTransfer("MV-ATLAS", FIRST_DOCKING, "W-NORTH", "sideways", 5)
    with pytest.raises(ValueError, match="direction must be unloaded or loaded"):
        record_transfer(sideways, [])


@pytest.mark.parametrize("units", [0, -5])
def test_transfer_of_no_units_is_refused(units: int) -> None:
    nothing = CargoTransfer("MV-ATLAS", FIRST_DOCKING, "W-NORTH", UNLOADED, units)
    with pytest.raises(ValueError, match="must be positive"):
        record_transfer(nothing, [])


def test_units_moved_counts_only_that_visit_and_direction() -> None:
    transfers = [UNLOAD_30, LOAD_10, UNLOAD_5_LATER]
    assert units_moved("MV-ATLAS", FIRST_DOCKING, UNLOADED, transfers) == 30
    assert units_moved("MV-ATLAS", FIRST_DOCKING, LOADED, transfers) == 10
    assert units_moved("MV-ATLAS", SECOND_DOCKING, UNLOADED, transfers) == 5


def test_units_moved_without_transfers_is_zero() -> None:
    assert units_moved("MV-ATLAS", FIRST_DOCKING, UNLOADED, []) == 0


def test_visit_history_has_one_visit_per_departure() -> None:
    history = visit_history(
        [FIRST_VISIT, SECOND_VISIT], [ATLAS], [UNLOAD_30, LOAD_10, UNLOAD_5_LATER]
    )
    assert history == [
        Visit("MV-ATLAS", "D1", ARRIVED_AT, FIRST_DOCKING, "2026-10-18T15:20", 30, 10, 720.0),
        Visit("MV-ATLAS", "D2", ARRIVED_AT, SECOND_DOCKING, "2026-10-20T09:00", 5, 0, 90.0),
    ]


def test_visit_history_without_departures_is_empty() -> None:
    assert visit_history([], [ATLAS], [UNLOAD_30]) == []


def test_visit_of_an_unknown_ship_is_refused() -> None:
    with pytest.raises(ValueError, match="not registered"):
        visit_history([FIRST_VISIT], [], [])


def test_describe_visit_shows_times_cargo_and_fee() -> None:
    visit = Visit("MV-ATLAS", "D1", ARRIVED_AT, FIRST_DOCKING, "2026-10-18T15:20", 30, 10, 720.0)
    assert describe_visit(visit) == (
        "MV-ATLAS  arrived 2026-10-18T09:30  at D1 from 2026-10-18T10:00 to 2026-10-18T15:20  "
        "unloaded 30  loaded 10  docking fee 720.00"
    )
