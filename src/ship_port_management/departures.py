import math
from dataclasses import dataclass

from ship_port_management.dockings import Docking
from ship_port_management.docks import Dock, find_dock
from ship_port_management.times import parse_time

SECONDS_PER_HOUR = 3600


@dataclass(frozen=True)
class Departure:
    ship_id: str
    dock_id: str
    docked_at: str
    departed_at: str
    hours: int
    docking_fee: float


@dataclass(frozen=True)
class DepartureResult:
    dockings: list[Docking]
    departure: Departure


def hours_at_dock(docked_at: str, departed_at: str) -> int:
    """Counts every started hour, so 10:00 to 10:01 is 1 hour."""
    docking_time = parse_time(docked_at, "docking time")
    departure_time = parse_time(departed_at, "departure time")
    if departure_time < docking_time:
        raise ValueError(
            f"departure time ({departed_at}) can't be before docking time ({docked_at})"
        )
    seconds_at_dock = (departure_time - docking_time).total_seconds()
    return math.ceil(seconds_at_dock / SECONDS_PER_HOUR)


def record_departure(new_departure: Departure, departures: list[Departure]) -> list[Departure]:
    hours = hours_at_dock(new_departure.docked_at, new_departure.departed_at)
    if new_departure.hours != hours:
        raise ValueError(
            f"hours must be {hours} for a stay from {new_departure.docked_at} "
            f"to {new_departure.departed_at}, got {new_departure.hours}"
        )
    if not (math.isfinite(new_departure.docking_fee) and new_departure.docking_fee >= 0):
        raise ValueError(
            f"docking fee must be a number of 0 or more, got {new_departure.docking_fee}"
        )
    return departures + [new_departure]


def find_docking(ship_id: str, dockings: list[Docking]) -> Docking:
    for docking in dockings:
        if docking.ship_id == ship_id:
            return docking
    raise ValueError(f"ship {ship_id} is not docked")


def depart_ship(
    ship_id: str, departed_at: str, dockings: list[Docking], docks: list[Dock]
) -> DepartureResult:
    docking = find_docking(ship_id, dockings)
    dock = find_dock(docking.dock_id, docks)
    hours = hours_at_dock(docking.docked_at, departed_at)
    departure = Departure(
        ship_id=ship_id,
        dock_id=dock.dock_id,
        docked_at=docking.docked_at,
        departed_at=departed_at,
        hours=hours,
        docking_fee=hours * dock.hourly_rate,
    )
    remaining_dockings = [
        other_docking for other_docking in dockings if other_docking.ship_id != ship_id
    ]
    return DepartureResult(dockings=remaining_dockings, departure=departure)


def describe_departure(departure: Departure) -> str:
    hours_text = "1 hour" if departure.hours == 1 else f"{departure.hours} hours"
    return (
        f"{departure.ship_id} left {departure.dock_id} after {hours_text}, "
        f"docking fee {departure.docking_fee:.2f}"
    )
