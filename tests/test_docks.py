import pytest

from ship_port_management.docks import Dock, add_dock, is_dock_available


def test_add_dock_list_not_changed() -> None:
    existing = Dock(dock_id="AA", max_ship_size=100, hourly_rate=100.0)
    new_dock = Dock(dock_id="BB", max_ship_size=100, hourly_rate=100.0)

    docks = [existing]
    add_dock(docks, new_dock)
    assert docks == [existing]


def test_add_dock_successfully() -> None:
    existing = Dock(dock_id="AA", max_ship_size=100, hourly_rate=100.0)
    new_dock = Dock(dock_id="BB", max_ship_size=100, hourly_rate=100.0)

    docks = [existing]
    assert add_dock(docks, new_dock) == [existing, new_dock]


def test_add_to_empty_list() -> None:
    new_dock = Dock(dock_id="AA", max_ship_size=100, hourly_rate=100.0)

    assert add_dock([], new_dock) == [new_dock]


def test_dock_available_when_none_occupied() -> None:
    dock = Dock(dock_id="AA", max_ship_size=100, hourly_rate=100.0)
    assert is_dock_available(dock, occupied_dock_ids=set())


def test_duplicate_dock_id_rejected() -> None:
    existing = Dock(dock_id="AA", max_ship_size=100, hourly_rate=100.0)
    new_dock = Dock(dock_id="AA", max_ship_size=50, hourly_rate=50.0)
    docks = [existing]

    with pytest.raises(ValueError):
        add_dock(docks, new_dock)


def test_zero_max_ship_size_rejected() -> None:
    new_dock = Dock(dock_id="AA", max_ship_size=0, hourly_rate=100.0)
    with pytest.raises(ValueError):
        add_dock([], new_dock)


def test_negative_max_ship_size_rejected() -> None:
    new_dock = Dock(dock_id="AA", max_ship_size=-100, hourly_rate=100.0)
    with pytest.raises(ValueError):
        add_dock([], new_dock)


def test_zero_hourly_rate_accepted() -> None:
    new_dock = Dock(dock_id="AA", max_ship_size=100, hourly_rate=0)
    assert add_dock([], new_dock) == [new_dock]


def test_negative_hourly_rate_rejected() -> None:
    new_dock = Dock(dock_id="AA", max_ship_size=100, hourly_rate=-100.0)
    with pytest.raises(ValueError):
        add_dock([], new_dock)


def test_occupied_dock_unavailable() -> None:
    dock = Dock(dock_id="AA", max_ship_size=100, hourly_rate=100.0)
    assert not is_dock_available(dock, occupied_dock_ids={"AA"})


def test_unoccupied_dock_available() -> None:
    dock = Dock(dock_id="AA", max_ship_size=100, hourly_rate=100.0)
    assert is_dock_available(dock, occupied_dock_ids={"BB", "CC"})
