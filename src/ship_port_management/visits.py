from dataclasses import dataclass

from ship_port_management.departures import Departure
from ship_port_management.ships import Ship, find_ship

UNLOADED = "unloaded"
LOADED = "loaded"
DIRECTIONS = (UNLOADED, LOADED)


@dataclass(frozen=True)
class CargoTransfer:
    ship_id: str
    docked_at: str
    warehouse_id: str
    direction: str
    units: int


@dataclass(frozen=True)
class Visit:
    ship_id: str
    dock_id: str
    arrived_at: str
    docked_at: str
    departed_at: str
    units_unloaded: int
    units_loaded: int
    docking_fee: float


def record_transfer(
    new_transfer: CargoTransfer, transfers: list[CargoTransfer]
) -> list[CargoTransfer]:
    if new_transfer.direction not in DIRECTIONS:
        raise ValueError(f"direction must be {UNLOADED} or {LOADED}, got {new_transfer.direction}")
    if new_transfer.units <= 0:
        raise ValueError(f"units moved must be positive, got {new_transfer.units}")
    return transfers + [new_transfer]


def units_moved(
    ship_id: str, docked_at: str, direction: str, transfers: list[CargoTransfer]
) -> int:
    return sum(
        transfer.units
        for transfer in transfers
        if transfer.ship_id == ship_id
        and transfer.docked_at == docked_at
        and transfer.direction == direction
    )


def visit_history(
    departures: list[Departure], ships: list[Ship], transfers: list[CargoTransfer]
) -> list[Visit]:
    return [
        Visit(
            ship_id=departure.ship_id,
            dock_id=departure.dock_id,
            arrived_at=find_ship(departure.ship_id, ships).arrival_time,
            docked_at=departure.docked_at,
            departed_at=departure.departed_at,
            units_unloaded=units_moved(departure.ship_id, departure.docked_at, UNLOADED, transfers),
            units_loaded=units_moved(departure.ship_id, departure.docked_at, LOADED, transfers),
            docking_fee=departure.docking_fee,
        )
        for departure in departures
    ]


def describe_visit(visit: Visit) -> str:
    return (
        f"{visit.ship_id}  arrived {visit.arrived_at}  at {visit.dock_id} "
        f"from {visit.docked_at} to {visit.departed_at}  "
        f"unloaded {visit.units_unloaded}  loaded {visit.units_loaded}  "
        f"docking fee {visit.docking_fee:.2f}"
    )
