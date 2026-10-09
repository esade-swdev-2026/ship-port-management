def cargo_within_capacity(capacity: int, cargo_units: int) -> bool:
    return 0 <= cargo_units <= capacity


def is_duplicate_ship(ship_id: str, existing_ids: set[str]) -> bool:
    return ship_id in existing_ids
