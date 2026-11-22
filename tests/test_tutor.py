import asyncio
from pathlib import Path

import pytest
from textual.pilot import Pilot
from textual.widgets import Input

from ship_port_management.tui import FormScreen
from ship_port_management.tutor import LESSONS, TutorApp, seed_practice_port


@pytest.fixture(autouse=True)
def practice_port(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    seed_practice_port()


async def type_into_form(pilot: Pilot[None], values: dict[str, str]) -> None:
    app = pilot.app
    assert isinstance(app.screen, FormScreen)
    for key, value in values.items():
        app.screen.query_one(f"#field-{key}", Input).value = value
    app.screen.query(Input).last().focus()
    await pilot.press("enter")
    await pilot.pause()


def test_practice_port_has_a_docked_and_an_undocked_ship() -> None:
    ships = Path("data/ships.csv").read_text()
    assert "MV-ATLAS" in ships and "MV-NOVA" in ships
    assert "MV-ATLAS,D1" in Path("data/dockings.csv").read_text()


def test_tutor_starts_on_the_first_lesson() -> None:
    async def scenario() -> int:
        app = TutorApp()
        async with app.run_test():
            return app.lesson_index

    assert asyncio.run(scenario()) == 0


def test_a_wrong_key_does_not_move_the_lesson_on() -> None:
    async def scenario() -> int:
        app = TutorApp()
        async with app.run_test() as pilot:
            await pilot.press("3")
            await pilot.pause()
            return app.lesson_index

    assert asyncio.run(scenario()) == 0


def test_following_every_lesson_reaches_the_end() -> None:
    async def scenario() -> list[int]:
        app = TutorApp()
        reached = []
        async with app.run_test(size=(100, 40)) as pilot:

            async def press(*keys: str) -> None:
                await pilot.press(*keys)
                await pilot.pause()
                reached.append(app.lesson_index)

            await press("down")
            await press("2")
            await press("1")
            await pilot.press("n")
            await type_into_form(pilot, {"ship_id": "MV-ORION", "name": "Orion", "capacity": "300"})
            reached.append(app.lesson_index)
            await press("up", "down")
            await pilot.press("d")
            await type_into_form(pilot, {"dock_id": "D2"})
            reached.append(app.lesson_index)
            await press("up")
            await pilot.press("u")
            await type_into_form(pilot, {"warehouse_id": "W-NORTH", "units": "10"})
            reached.append(app.lesson_index)
            await pilot.press("l")
            await type_into_form(pilot, {"warehouse_id": "W-NORTH", "units": "5"})
            reached.append(app.lesson_index)
            await press("v")
            await press("j")
            await press("k")
            await press("G")
            await press("g", "g")
            await press("l")
            await press("h")
            await pilot.press("p")
            await type_into_form(pilot, {"warehouse_id": "W-NORTH", "units": "5"})
            reached.append(app.lesson_index)
        return reached

    reached = asyncio.run(scenario())
    assert reached[-1] == len(LESSONS) - 1
    assert sorted(set(reached)) == list(range(1, len(LESSONS)))
