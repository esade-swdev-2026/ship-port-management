import contextlib
import io
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

import typer
from rich.text import Text
from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.theme import Theme
from textual.widget import Widget
from textual.widgets import DataTable, Footer, Input, Label, TabbedContent, TabPane

from ship_port_management import cli, ship_art, storage
from ship_port_management.csv_handling import (
    read_dockings,
    read_docks,
    read_ships,
    read_stored_cargo,
    read_warehouses,
)

BAR_WIDTH = 12
TIDE_SECONDS = 0.1
TIDE_STEP = 0.12
MIN_HEIGHT_FOR_SHIP = 34

TERMINAL = Theme(
    name="terminal",
    ansi=True,
    primary="ansi_default",
    secondary="ansi_default",
    accent="ansi_default",
    foreground="ansi_default",
    background="ansi_default",
    surface="ansi_default",
    panel="ansi_default",
    boost="ansi_default",
    success="ansi_default",
    warning="ansi_default",
    error="ansi_red",
    dark=True,
    variables={
        "ansi-background": "ansi_default",
        "ansi-foreground": "ansi_default",
        "input-cursor-text-style": "reverse",
        "input-selection-background": "ansi_bright_black",
        "input-selection-foreground": "ansi_default",
        "screen-selection-background": "ansi_bright_black",
        "screen-selection-foreground": "ansi_default",
        "footer-background": "ansi_default",
        "footer-key-foreground": "ansi_default",
        "footer-description-foreground": "ansi_default",
        "block-cursor-foreground": "ansi_default",
        "block-cursor-background": "ansi_default",
        "input-cursor-foreground": "ansi_default",
        "input-cursor-background": "ansi_default",
        "border": "ansi_default",
        "border-blurred": "ansi_default",
    },
)

SELECTION_FIELD = {"ships": "ship_id", "docks": "dock_id", "warehouses": "warehouse_id"}


def whole_number(text: str, name: str) -> int:
    try:
        return int(text)
    except ValueError:
        raise ValueError(f"{name} must be a whole number, got {text!r}") from None


def number(text: str, name: str) -> float:
    try:
        return float(text)
    except ValueError:
        raise ValueError(f"{name} must be a number, got {text!r}") from None


def run_command(command: Callable[[], None]) -> tuple[bool, str]:
    out, err = io.StringIO(), io.StringIO()
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            command()
    except typer.Exit:
        return False, err.getvalue().strip()
    except ValueError as error:
        return False, str(error)
    return True, out.getvalue().strip()


def fill_bar(used: int, total: int) -> Text:
    filled = max(1, round(BAR_WIDTH * used / total)) if used and total else 0
    bar = Text("━" * filled)
    bar.append("─" * (BAR_WIDTH - filled), style="dim")
    bar.append(f"  {used}/{total}", style="dim")
    return bar


@dataclass(frozen=True)
class Field:
    key: str
    label: str
    placeholder: str = ""
    optional: bool = False


@dataclass(frozen=True)
class Form:
    title: str
    fields: tuple[Field, ...]
    submit: Callable[[dict[str, str]], None]


REGISTER_SHIP = Form(
    "Register ship",
    (
        Field("ship_id", "id", "MV-ATLAS"),
        Field("name", "name", "Atlas"),
        Field("capacity", "capacity", "500"),
        Field("cargo_units", "cargo", "0", optional=True),
        Field("arrival_time", "arrived", "now", optional=True),
    ),
    lambda v: cli.register_vessel(
        v["ship_id"],
        v["name"],
        whole_number(v["capacity"], "capacity"),
        whole_number(v["cargo_units"] or "0", "cargo"),
        v["arrival_time"],
    ),
)

ADD_DOCK = Form(
    "Add dock",
    (
        Field("dock_id", "id", "D1"),
        Field("max_ship_size", "max ship size", "500"),
        Field("hourly_rate", "rate / hour", "120"),
    ),
    lambda v: cli.add_dock(
        v["dock_id"],
        whole_number(v["max_ship_size"], "max ship size"),
        number(v["hourly_rate"], "rate"),
    ),
)

ADD_WAREHOUSE = Form(
    "Add warehouse",
    (
        Field("warehouse_id", "id", "W-NORTH"),
        Field("capacity", "capacity", "200"),
        Field("daily_rate_per_unit", "rate / unit / day", "1.5"),
    ),
    lambda v: cli.add_warehouse(
        v["warehouse_id"],
        whole_number(v["capacity"], "capacity"),
        number(v["daily_rate_per_unit"], "rate"),
    ),
)

DOCK_SHIP = Form(
    "Dock ship",
    (
        Field("ship_id", "ship", "MV-ATLAS"),
        Field("dock_id", "dock", "D1"),
        Field("docked_at", "docked", "now", optional=True),
    ),
    lambda v: cli.dock_vessel(v["ship_id"], v["dock_id"], v["docked_at"]),
)

UNLOAD_CARGO = Form(
    "Unload cargo",
    (
        Field("ship_id", "ship", "MV-ATLAS"),
        Field("warehouse_id", "warehouse", "W-NORTH"),
        Field("units", "units", "30"),
        Field("stored_at", "stored", "now", optional=True),
    ),
    lambda v: cli.unload_cargo(
        v["ship_id"], v["warehouse_id"], whole_number(v["units"], "units"), v["stored_at"]
    ),
)

LOAD_CARGO = Form(
    "Load cargo",
    (
        Field("ship_id", "ship", "MV-ATLAS"),
        Field("warehouse_id", "warehouse", "W-NORTH"),
        Field("units", "units", "10"),
    ),
    lambda v: cli.load_cargo(v["ship_id"], v["warehouse_id"], whole_number(v["units"], "units")),
)

NEW_FORM_FOR_TAB = {"ships": REGISTER_SHIP, "docks": ADD_DOCK, "warehouses": ADD_WAREHOUSE}


class ShipArt(Widget):
    def __init__(self) -> None:
        super().__init__()
        self.phase = 0.0

    def on_mount(self) -> None:
        self.set_interval(TIDE_SECONDS, self.roll)

    def roll(self) -> None:
        self.phase += TIDE_STEP
        self.refresh()

    def render(self) -> Text:
        art = Text()
        for ship_row, motion_row in zip(
            ship_art.ship_cells(), ship_art.motion_rows(self.phase), strict=True
        ):
            for (ship_cell, color), motion_cell in zip(ship_row, motion_row, strict=True):
                if ship_cell != " ":
                    art.append(ship_cell, style=color)
                else:
                    art.append(motion_cell, style="dim")
            art.append("\n")
        art.rstrip()
        return art


class FormScreen(ModalScreen[dict[str, str] | None]):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, form: Form, prefill: dict[str, str]) -> None:
        super().__init__()
        self.form = form
        self.prefill = prefill

    def compose(self) -> ComposeResult:
        with Vertical(id="form"):
            yield Label(self.form.title, id="form-title")
            for field in self.form.fields:
                yield Label(field.label, classes="field-label")
                yield Input(
                    value=self.prefill.get(field.key, ""),
                    placeholder=field.placeholder,
                    id=f"field-{field.key}",
                )
            yield Label("", id="form-error")
            yield Label("enter save · esc cancel", id="form-hint")

    def on_mount(self) -> None:
        inputs = list(self.query(Input))
        next((box for box in inputs if not box.value), inputs[-1]).focus()

    def value(self, field: Field) -> str:
        return self.query_one(f"#field-{field.key}", Input).value.strip()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input is not list(self.query(Input))[-1]:
            self.focus_next()
            return
        missing = [f for f in self.form.fields if not f.optional and not self.value(f)]
        if missing:
            error = self.query_one("#form-error", Label)
            error.update(f"{missing[0].label} is required")
            error.add_class("shown")
            self.query_one(f"#field-{missing[0].key}", Input).focus()
            return
        self.dismiss({field.key: self.value(field) for field in self.form.fields})

    def action_cancel(self) -> None:
        self.dismiss(None)


class HarbourApp(App[None]):
    TITLE = "Harbour Master"
    ENABLE_COMMAND_PALETTE = False
    CSS = """
    Screen { background: ansi_default; }
    ShipArt { width: auto; height: auto; margin: 1 0 0 3; }
    #summary { margin: 1 0 0 3; text-style: dim; }
    TabbedContent { margin: 1 2 0 2; height: 1fr; }
    Tab { text-style: dim; }
    Tab.-active { text-style: bold; }
    Tab:hover { text-style: none; }
    Underline > .underline--bar { color: ansi_default; background: ansi_default; }
    TabPane { padding: 1 0 0 0; }
    DataTable { background: ansi_default; height: 1fr; scrollbar-size-vertical: 1; }
    DataTable:focus { background-tint: ansi_default 0%; }
    DataTable > .datatable--header { background: ansi_default; text-style: dim; }
    DataTable > .datatable--cursor { background: ansi_default; text-style: reverse; }
    DataTable > .datatable--hover { background: ansi_default; }
    FormScreen { align: center middle; background: ansi_default; }
    #form { width: 46; height: auto; padding: 1 3; border: round ansi_default; }
    #form-title { text-style: bold; margin-bottom: 1; }
    .field-label { text-style: dim; }
    #form Input {
        height: 1; padding: 0 1; margin-bottom: 1; border: none;
        background: ansi_default; border-left: outer ansi_bright_black;
    }
    #form Input:focus { border-left: outer ansi_default; text-style: bold; }
    #form Input > .input--placeholder { text-style: dim; }
    #form-error { color: ansi_red; display: none; }
    #form-error.shown { display: block; }
    #form-hint { text-style: dim; margin-top: 1; }
    Footer { background: ansi_default; }
    FooterKey { background: ansi_default; }
    FooterKey .footer-key--key { background: ansi_default; text-style: bold; }
    FooterKey .footer-key--description { text-style: dim; }
    Toast { background: ansi_default; border-left: outer ansi_default; }
    Toast.-error { border-left: outer ansi_red; }
    Toast .toast--title { text-style: bold; }
    """
    BINDINGS = [
        Binding("n", "new", "new"),
        Binding("d", "open_form('dock')", "dock"),
        Binding("u", "open_form('unload')", "unload"),
        Binding("l", "open_form('load')", "load"),
        Binding("q", "quit", "quit"),
        Binding("r", "refresh", show=False),
        Binding("1", "show_tab('ships')", show=False),
        Binding("2", "show_tab('docks')", show=False),
        Binding("3", "show_tab('warehouses')", show=False),
        Binding("4", "show_tab('fees')", show=False),
    ]
    FORMS = {"dock": DOCK_SHIP, "unload": UNLOAD_CARGO, "load": LOAD_CARGO}

    def __init__(self) -> None:
        super().__init__()
        self.register_theme(TERMINAL)
        self.theme = TERMINAL.name

    def compose(self) -> ComposeResult:
        yield ShipArt()
        yield Label("", id="summary")
        with TabbedContent(initial="ships"):
            for tab_id, title in [
                ("ships", "Ships"),
                ("docks", "Docks"),
                ("warehouses", "Warehouses"),
                ("fees", "Fees"),
            ]:
                with TabPane(title, id=tab_id):
                    yield DataTable(
                        id=f"{tab_id}-table",
                        cursor_type="row",
                        cursor_foreground_priority="renderable",
                    )
        yield Footer()

    def on_mount(self) -> None:
        columns = {
            "ships": ("ship", "name", "arrived", "cargo", "dock"),
            "docks": ("dock", "max size", "rate / h", "ship"),
            "warehouses": ("warehouse", "fill", "free", "rate / unit / day"),
            "fees": ("ship", "units stored", "owed"),
        }
        for tab_id, names in columns.items():
            self.table(tab_id).add_columns(*names)
        self.action_refresh()
        self.table("ships").focus()

    def on_resize(self, event: events.Resize) -> None:
        self.query_one(ShipArt).display = event.size.height >= MIN_HEIGHT_FOR_SHIP

    def table(self, tab_id: str) -> DataTable[str | Text]:
        return self.query_one(f"#{tab_id}-table", DataTable)

    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        event.pane.query_one(DataTable).focus()

    def action_show_tab(self, tab_id: str) -> None:
        self.query_one(TabbedContent).active = tab_id

    def action_refresh(self) -> None:
        try:
            port_ships = read_ships(cli.SHIPS_FILE)
            port_docks = read_docks(cli.DOCKS_FILE)
            port_warehouses = read_warehouses(cli.WAREHOUSES_FILE)
            port_dockings = read_dockings(cli.DOCKINGS_FILE)
            stored = read_stored_cargo(cli.STORED_CARGO_FILE)
            fees = storage.fees_by_ship(
                stored, port_warehouses, datetime.now().isoformat(timespec="minutes")
            )
        except (OSError, ValueError) as error:
            self.notify(f"could not read the port files: {error}", severity="error")
            return

        dock_of_ship = {docking.ship_id: docking.dock_id for docking in port_dockings}
        ship_at_dock = {docking.dock_id: docking.ship_id for docking in port_dockings}

        ships_table = self.table("ships")
        ships_table.clear()
        for ship in port_ships:
            ships_table.add_row(
                Text(ship.ship_id, style="bold"),
                ship.name,
                Text(ship.arrival_time.replace("T", " "), style="dim"),
                fill_bar(ship.cargo_units, ship.capacity),
                dock_of_ship.get(ship.ship_id, Text("·", style="dim")),
                key=ship.ship_id,
            )

        docks_table = self.table("docks")
        docks_table.clear()
        for dock in port_docks:
            docks_table.add_row(
                Text(dock.dock_id, style="bold"),
                str(dock.max_ship_size),
                Text(f"{dock.hourly_rate:.2f}", style="dim"),
                ship_at_dock.get(dock.dock_id, Text("free", style="dim")),
                key=dock.dock_id,
            )

        warehouses_table = self.table("warehouses")
        warehouses_table.clear()
        for warehouse in port_warehouses:
            warehouses_table.add_row(
                Text(warehouse.warehouse_id, style="bold"),
                fill_bar(warehouse.stored_units, warehouse.capacity),
                str(warehouse.capacity - warehouse.stored_units),
                Text(f"{warehouse.daily_rate_per_unit:.2f}", style="dim"),
                key=warehouse.warehouse_id,
            )

        fees_table = self.table("fees")
        fees_table.clear()
        for ship_id, fee in sorted(fees.items()):
            units = sum(cargo.units for cargo in stored if cargo.ship_id == ship_id)
            fees_table.add_row(
                Text(ship_id, style="bold"),
                str(units),
                Text(f"{fee:.2f}", style="" if fee else "dim"),
                key=ship_id,
            )

        stored_units = sum(warehouse.stored_units for warehouse in port_warehouses)
        storage_room = sum(warehouse.capacity for warehouse in port_warehouses)
        stored_share = round(100 * stored_units / storage_room) if storage_room else 0
        free_docks = len(port_docks) - len(ship_at_dock)
        ship_count = f"{len(port_ships)} ship" + ("" if len(port_ships) == 1 else "s")
        self.query_one("#summary", Label).update(
            f"{ship_count} · {free_docks}/{len(port_docks)} docks free · {stored_share}% stored"
        )

    def selection(self) -> dict[str, str]:
        tab_id = self.query_one(TabbedContent).active
        if tab_id not in SELECTION_FIELD:
            return {}
        table = self.table(tab_id)
        if not table.row_count:
            return {}
        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
        return {SELECTION_FIELD[tab_id]: str(row_key.value)}

    def action_new(self) -> None:
        form = NEW_FORM_FOR_TAB.get(self.query_one(TabbedContent).active)
        if form is None:
            self.notify("fees come from stored cargo")
            return
        self.open(form, {})

    def action_open_form(self, name: str) -> None:
        self.open(self.FORMS[name], self.selection())

    def open(self, form: Form, prefill: dict[str, str]) -> None:
        def submit(values: dict[str, str] | None) -> None:
            if values is None:
                return
            succeeded, message = run_command(lambda: form.submit(values))
            self.notify(message, severity="information" if succeeded else "error")
            if succeeded:
                self.action_refresh()

        self.push_screen(FormScreen(form, prefill), submit)
