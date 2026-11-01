import pytest

from ship_port_management.warehouses import (
    Warehouse,
    add_warehouse,
    describe_warehouse,
    free_units,
    is_duplicate_warehouse,
    stored_within_capacity,
)

NORTH_CAPACITY = 200
NORTH_DAILY_RATE = 1.5

NORTH = Warehouse("W-NORTH", NORTH_CAPACITY, NORTH_DAILY_RATE)
SOUTH = Warehouse("W-SOUTH", 100, 2.0)


def north_storing(stored_units: int) -> Warehouse:
    return Warehouse("W-NORTH", NORTH_CAPACITY, NORTH_DAILY_RATE, stored_units)


def north_with_capacity(capacity: int) -> Warehouse:
    return Warehouse("W-NORTH", capacity, NORTH_DAILY_RATE)


def north_with_daily_rate(daily_rate_per_unit: float) -> Warehouse:
    return Warehouse("W-NORTH", NORTH_CAPACITY, daily_rate_per_unit)


def test_new_warehouse_starts_empty() -> None:
    assert NORTH.stored_units == 0


def test_stored_exactly_at_capacity_allowed() -> None:
    assert stored_within_capacity(north_storing(NORTH_CAPACITY))


def test_stored_above_capacity_not_allowed() -> None:
    assert not stored_within_capacity(north_storing(NORTH_CAPACITY + 1))


def test_negative_stored_units_not_allowed() -> None:
    assert not stored_within_capacity(north_storing(-1))


def test_free_units_of_empty_warehouse_is_capacity() -> None:
    assert free_units(NORTH) == NORTH_CAPACITY


def test_free_units_of_full_warehouse_is_zero() -> None:
    assert free_units(north_storing(NORTH_CAPACITY)) == 0


def test_duplicate_id_detected() -> None:
    assert is_duplicate_warehouse("W-NORTH", {"W-NORTH", "W-SOUTH"})


def test_new_id_is_not_duplicate() -> None:
    assert not is_duplicate_warehouse("W-NORTH", {"W-SOUTH"})


def test_add_warehouse_to_empty_list() -> None:
    assert add_warehouse(NORTH, []) == [NORTH]


def test_add_warehouse_appends_to_existing() -> None:
    assert add_warehouse(SOUTH, [NORTH]) == [NORTH, SOUTH]


def test_add_warehouse_leaves_original_list_unchanged() -> None:
    warehouses = [NORTH]
    add_warehouse(SOUTH, warehouses)
    assert warehouses == [NORTH]


def test_duplicate_warehouse_is_refused() -> None:
    with pytest.raises(ValueError):
        add_warehouse(north_storing(0), [NORTH])


def test_capacity_of_one_is_accepted() -> None:
    smallest = north_with_capacity(1)
    assert add_warehouse(smallest, []) == [smallest]


def test_zero_capacity_is_refused() -> None:
    with pytest.raises(ValueError):
        add_warehouse(north_with_capacity(0), [])


def test_negative_capacity_is_refused() -> None:
    with pytest.raises(ValueError):
        add_warehouse(north_with_capacity(-NORTH_CAPACITY), [])


def test_zero_daily_rate_is_refused() -> None:
    with pytest.raises(ValueError):
        add_warehouse(north_with_daily_rate(0.0), [])


def test_negative_daily_rate_is_refused() -> None:
    with pytest.raises(ValueError):
        add_warehouse(north_with_daily_rate(-NORTH_DAILY_RATE), [])


def test_stored_above_capacity_is_refused() -> None:
    with pytest.raises(ValueError):
        add_warehouse(north_storing(NORTH_CAPACITY + 1), [])


def test_describe_warehouse_shows_used_and_free_units() -> None:
    assert describe_warehouse(north_storing(50)) == (
        "W-NORTH  used 50/200  free 150  rate 1.5 per unit per day"
    )


@pytest.mark.parametrize("daily_rate_per_unit", [float("nan"), float("inf")])
def test_non_finite_daily_rate_is_refused(daily_rate_per_unit: float) -> None:
    with pytest.raises(ValueError, match="positive number"):
        add_warehouse(north_with_daily_rate(daily_rate_per_unit), [])
