import asyncio
from pathlib import Path

import pytest
from textual.widgets import DataTable, Input, Label, TabbedContent

from ship_port_management import cli
from ship_port_management.tui import FormScreen, HarbourApp, HelpScreen, fill_bar, run_command


@pytest.fixture(autouse=True)
def work_in_empty_folder(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)


def fill_form(app: HarbourApp, values: dict[str, str]) -> None:
    assert isinstance(app.screen, FormScreen)
    for key, value in values.items():
        app.screen.query_one(f"#field-{key}", Input).value = value
    app.screen.query(Input).last().focus()


def test_run_command_returns_the_cli_success_message() -> None:
    succeeded, message = run_command(lambda: cli.add_dock("D1", 500, 120))
    assert succeeded
    assert message.startswith("Dock D1 successfully added")


def test_run_command_returns_the_cli_error_message() -> None:
    succeeded, message = run_command(lambda: cli.load_cargo("MV-GHOST", "W-NORTH", 1))
    assert not succeeded
    assert message == "could not load MV-GHOST: ship MV-GHOST is not registered"


def test_fill_bar_shows_used_over_total() -> None:
    assert fill_bar(20, 200).plain.endswith("20/200")


def test_fill_bar_shows_a_little_cargo_as_one_segment() -> None:
    assert fill_bar(1, 500).plain.count("━") == 1


def test_fill_bar_of_nothing_is_empty() -> None:
    assert fill_bar(0, 500).plain.count("━") == 0


def test_empty_port_summary() -> None:
    async def scenario() -> str:
        app = HarbourApp()
        async with app.run_test():
            return str(app.query_one("#summary", Label).render())

    assert asyncio.run(scenario()) == "0 ships · 0/0 docks free · 0% stored"


def test_tables_show_saved_port_data() -> None:
    cli.register_vessel("MV-ATLAS", "Atlas", 500, 40, "2026-10-18T09:30")
    cli.add_dock("D1", 500, 120)
    cli.dock_vessel("MV-ATLAS", "D1", "2026-10-18T10:00")

    async def scenario() -> tuple[int, int, str]:
        app = HarbourApp()
        async with app.run_test():
            ships_table = app.query_one("#ships-table", DataTable)
            docks_table = app.query_one("#docks-table", DataTable)
            summary = str(app.query_one("#summary", Label).render())
            return ships_table.row_count, docks_table.row_count, summary

    ship_rows, dock_rows, summary = asyncio.run(scenario())
    assert (ship_rows, dock_rows) == (1, 1)
    assert summary.startswith("1 ship · 0/1 docks free")


def test_register_form_saves_the_ship() -> None:
    async def scenario() -> int:
        app = HarbourApp()
        async with app.run_test() as pilot:
            await pilot.press("n")
            fill_form(app, {"ship_id": "MV-ATLAS", "name": "Atlas", "capacity": "500"})
            await pilot.press("enter")
            await pilot.pause()
            return app.query_one("#ships-table", DataTable).row_count

    assert asyncio.run(scenario()) == 1
    assert "MV-ATLAS" in Path("data/ships.csv").read_text()


def test_form_with_a_bad_number_saves_nothing() -> None:
    async def scenario() -> None:
        app = HarbourApp()
        async with app.run_test() as pilot:
            await pilot.press("n")
            fill_form(app, {"ship_id": "MV-ATLAS", "name": "Atlas", "capacity": "lots"})
            await pilot.press("enter")
            await pilot.pause()

    asyncio.run(scenario())
    assert not Path("data/ships.csv").exists()


def test_form_with_a_missing_field_stays_open() -> None:
    async def scenario() -> bool:
        app = HarbourApp()
        async with app.run_test() as pilot:
            await pilot.press("n")
            fill_form(app, {"ship_id": "MV-ATLAS", "capacity": "500"})
            await pilot.press("enter")
            await pilot.pause()
            return isinstance(app.screen, FormScreen)

    assert asyncio.run(scenario())


def test_escape_closes_the_form_without_saving() -> None:
    async def scenario() -> bool:
        app = HarbourApp()
        async with app.run_test() as pilot:
            await pilot.press("n")
            fill_form(app, {"ship_id": "MV-ATLAS", "name": "Atlas", "capacity": "500"})
            await pilot.press("escape")
            await pilot.pause()
            return isinstance(app.screen, FormScreen)

    assert not asyncio.run(scenario())
    assert not Path("data/ships.csv").exists()


def test_dock_form_starts_with_the_selected_ship() -> None:
    cli.register_vessel("MV-ATLAS", "Atlas", 500, 40, "2026-10-18T09:30")

    async def scenario() -> str:
        app = HarbourApp()
        async with app.run_test() as pilot:
            await pilot.press("d")
            await pilot.pause()
            return app.screen.query_one("#field-ship_id", Input).value

    assert asyncio.run(scenario()) == "MV-ATLAS"


def ship_cursor_row(app: HarbourApp) -> int:
    return app.query_one("#ships-table", DataTable).cursor_row


def register_three_ships() -> None:
    for ship_id in ("MV-ATLAS", "MV-NOVA", "MV-ORION"):
        cli.register_vessel(ship_id, ship_id.title(), 500, 0, "2026-10-18T09:30")


def test_vim_keys_do_nothing_until_vim_mode_is_on() -> None:
    register_three_ships()

    async def scenario() -> int:
        app = HarbourApp()
        async with app.run_test() as pilot:
            await pilot.press("j", "j")
            return ship_cursor_row(app)

    assert asyncio.run(scenario()) == 0


def test_v_turns_vim_mode_on_and_off() -> None:
    async def scenario() -> list[str]:
        app = HarbourApp()
        summaries = []
        async with app.run_test() as pilot:
            for _ in range(2):
                await pilot.press("v")
                await pilot.pause()
                summaries.append(str(app.query_one("#summary", Label).render()))
        return summaries

    turned_on, turned_off = asyncio.run(scenario())
    assert turned_on.endswith("· vim")
    assert not turned_off.endswith("· vim")


def test_vim_j_k_move_between_rows() -> None:
    register_three_ships()

    async def scenario() -> list[int]:
        app = HarbourApp(vim=True)
        rows = []
        async with app.run_test() as pilot:
            for key in ("j", "j", "j", "k"):
                await pilot.press(key)
                rows.append(ship_cursor_row(app))
        return rows

    assert asyncio.run(scenario()) == [1, 2, 2, 1]


def test_vim_capital_g_and_gg_jump_to_last_and_first_row() -> None:
    register_three_ships()

    async def scenario() -> list[int]:
        app = HarbourApp(vim=True)
        async with app.run_test() as pilot:
            await pilot.press("G")
            last = ship_cursor_row(app)
            await pilot.press("g")
            after_one_g = ship_cursor_row(app)
            await pilot.press("g")
            return [last, after_one_g, ship_cursor_row(app)]

    assert asyncio.run(scenario()) == [2, 2, 0]


def test_vim_h_l_move_between_tabs() -> None:
    async def scenario() -> list[str]:
        app = HarbourApp(vim=True)
        tabs = app.query_one
        seen = []
        async with app.run_test() as pilot:
            for key in ("l", "l", "h", "h", "h"):
                await pilot.press(key)
                seen.append(tabs(TabbedContent).active)
        return seen

    assert asyncio.run(scenario()) == ["docks", "warehouses", "docks", "ships", "ships"]


def test_l_loads_normally_and_p_loads_in_vim_mode() -> None:
    async def form_title(vim: bool, key: str) -> str:
        app = HarbourApp(vim=vim)
        async with app.run_test() as pilot:
            await pilot.press(key)
            await pilot.pause()
            assert isinstance(app.screen, FormScreen)
            return app.screen.form.title

    assert asyncio.run(form_title(False, "l")) == "Load cargo"
    assert asyncio.run(form_title(True, "p")) == "Load cargo"


def test_typing_vim_keys_into_a_form_only_types_them() -> None:
    async def scenario() -> str:
        app = HarbourApp(vim=True)
        async with app.run_test() as pilot:
            await pilot.press("n")
            await pilot.press(*"jklhgq")
            await pilot.pause()
            assert isinstance(app.screen, FormScreen)
            return app.screen.query_one("#field-ship_id", Input).value

    assert asyncio.run(scenario()) == "jklhgq"


def test_vim_form_normal_mode_moves_between_boxes_and_saves() -> None:
    async def scenario() -> None:
        app = HarbourApp(vim=True)
        async with app.run_test() as pilot:
            await pilot.press("n", *"MV-ATLAS", "escape", "j", "i", *"Atlas")
            await pilot.press("escape", "j", "a", *"500", "escape", "enter")
            await pilot.pause()
            assert not isinstance(app.screen, FormScreen)

    asyncio.run(scenario())
    assert "MV-ATLAS,Atlas" in Path("data/ships.csv").read_text()


def test_vim_form_q_in_normal_mode_cancels() -> None:
    async def scenario() -> bool:
        app = HarbourApp(vim=True)
        async with app.run_test() as pilot:
            await pilot.press("n", "escape", "q")
            await pilot.pause()
            return isinstance(app.screen, FormScreen)

    assert not asyncio.run(scenario())


def form_texts(app: HarbourApp, css_class: str) -> list[str]:
    return [str(label.render()) for label in app.screen.query(f".{css_class}").results(Label)]


def test_bad_input_keeps_the_form_open_with_the_error_inside() -> None:
    async def scenario() -> tuple[bool, str]:
        app = HarbourApp()
        async with app.run_test() as pilot:
            await pilot.press("n")
            fill_form(app, {"ship_id": "MV-ATLAS", "name": "Atlas", "capacity": "0"})
            await pilot.press("enter")
            await pilot.pause()
            error = str(app.screen.query_one("#form-error", Label).render())
            return isinstance(app.screen, FormScreen), error

    still_open, error = asyncio.run(scenario())
    assert still_open
    assert error == "could not register MV-ATLAS: capacity must be positive, got 0"


def test_optional_boxes_are_labelled_and_time_boxes_say_empty_means_now() -> None:
    async def scenario() -> tuple[list[str], list[str], str]:
        app = HarbourApp()
        async with app.run_test() as pilot:
            await pilot.press("n")
            placeholder = app.screen.query_one("#field-arrival_time", Input).placeholder
            return form_texts(app, "field-label"), form_texts(app, "field-note"), placeholder

    labels, notes, placeholder = asyncio.run(scenario())
    assert "cargo on board (units) (optional)" in labels
    assert "arrival time (optional)" in labels
    assert "e.g. 2026-10-18T09:30, empty = now" in notes
    assert placeholder == "empty = now"


def test_dock_form_lists_waiting_ships_and_free_docks() -> None:
    register_three_ships()
    cli.add_dock("D1", 500, 120)
    cli.add_dock("D2", 500, 90)
    cli.dock_vessel("MV-ATLAS", "D1", "2026-10-18T10:00")

    async def scenario() -> list[str]:
        app = HarbourApp()
        async with app.run_test() as pilot:
            await pilot.press("d")
            await pilot.pause()
            return form_texts(app, "field-note")

    notes = asyncio.run(scenario())
    assert "ships waiting: MV-NOVA, MV-ORION" in notes
    assert "free docks: D2" in notes


def test_question_mark_shows_the_keys_and_escape_closes_them() -> None:
    async def scenario() -> list[bool]:
        app = HarbourApp()
        async with app.run_test() as pilot:
            await pilot.press("question_mark")
            opened = isinstance(app.screen, HelpScreen)
            await pilot.press("escape")
            return [opened, isinstance(app.screen, HelpScreen)]

    assert asyncio.run(scenario()) == [True, False]
