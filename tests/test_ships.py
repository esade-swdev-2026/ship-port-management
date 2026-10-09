from ship_port_management.ships import cargo_within_capacity, is_duplicate_ship


def test_cargo_below_capacity() -> None:
    assert cargo_within_capacity(capacity=500, cargo_units=40)


def test_cargo_above_capacity() -> None:
    assert not cargo_within_capacity(capacity=500, cargo_units=501)


def test_cargo_exactly_at_capacity_allowed() -> None:
    assert cargo_within_capacity(capacity=500, cargo_units=500)


def test_empty_ship_within_capacity() -> None:
    assert cargo_within_capacity(capacity=500, cargo_units=0)


def test_negative_cargo() -> None:
    assert not cargo_within_capacity(capacity=500, cargo_units=-5)


def test_duplicate_ship() -> None:
    assert is_duplicate_ship(ship_id="IMO9074729", existing_ids={"IMO9012328", "IMO9074729"})


def test_not_duplicate_ship() -> None:
    assert not is_duplicate_ship(ship_id="IMO9074729", existing_ids={"IMO9012328", "IMO0674755"})


def test_no_ships_registered_means_no_duplicate() -> None:
    assert not is_duplicate_ship(ship_id="IMO9074729", existing_ids=set())
