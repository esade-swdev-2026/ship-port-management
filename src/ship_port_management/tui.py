import contextlib
import io
from collections.abc import Callable
from dataclasses import dataclass

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

from ship_port_management import cli, ship_art, status, storage
from ship_port_management.csv_handling import (
    read_dockings,
    read_docks,
    read_ships,
    read_stored_cargo,
    read_warehouses,
)
from ship_port_management.dockings import Docking, is_ship_docked, occupied_dock_ids
from ship_port_management.docks import Dock
from ship_port_management.ships import Ship
from ship_port_management.storage import StoredCargo
from ship_port_management.times import current_time
from ship_port_management.warehouses import Warehouse, free_units

BAR_WIDTH = 12
TIDE_SECONDS = 0.1
TIDE_STEP = 0.12
MIN_HEIGHT_FOR_SHIP = 34
TABS = ("ships", "docks", "warehouses", "fees")

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
TIME_NOTE = "e.g. 2026-10-18T09:30, empty = now"
PLAIN_HINT = "enter save · esc cancel"


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


def listed(name: str, ids: list[str]) -> str:
    return f"{name}: {', '.join(ids)}" if ids else f"no {name} yet"


@dataclass(frozen=True)
class Port:
    ships: list[Ship]
    docks: list[Dock]
    warehouses: list[Warehouse]
    dockings: list[Docking]
    stored: list[StoredCargo]


def read_port() -> Port:
    return Port(
        ships=read_ships(cli.SHIPS_FILE),
        docks=read_docks(cli.DOCKS_FILE),
        warehouses=read_warehouses(cli.WAREHOUSES_FILE),
        dockings=read_dockings(cli.DOCKINGS_FILE),
        stored=read_stored_cargo(cli.STORED_CARGO_FILE),
    )


def docked_ship_ids(port: Port) -> list[str]:
    return [ship.ship_id for ship in port.ships if is_ship_docked(ship.ship_id, port.dockings)]


def waiting_ship_ids(port: Port) -> list[str]:
    return [ship.ship_id for ship in port.ships if not is_ship_docked(ship.ship_id, port.dockings)]


def free_dock_ids(port: Port) -> list[str]:
    occupied = occupied_dock_ids(port.dockings)
    return [dock.dock_id for dock in status.available_docks(port.docks, occupied)]


def warehouse_ids(port: Port) -> list[str]:
    return [warehouse.warehouse_id for warehouse in port.warehouses]


@dataclass(frozen=True)
class Field:
    key: str
    label: str
    placeholder: str = ""
    optional: bool = False
    note: str = ""
    choices: Callable[[Port], str] | None = None


@dataclass(frozen=True)
class Form:
    title: str
    fields: tuple[Field, ...]
    submit: Callable[[dict[str, str]], None]


def time_field(key: str, label: str) -> Field:
    return Field(key, label, "empty = now", optional=True, note=TIME_NOTE)


DOCKED_SHIP = Field(
    "ship_id",
    "ship ID",
    "MV-ATLAS",
    choices=lambda port: listed("docked ships", docked_ship_ids(port)),
)
WAREHOUSE = Field(
    "warehouse_id",
    "warehouse ID",
    "W-NORTH",
    choices=lambda port: listed("warehouses", warehouse_ids(port)),
)

REGISTER_SHIP = Form(
    "Register ship",
    (
        Field("ship_id", "ship ID", "MV-ATLAS"),
        Field("name", "ship name", "Atlas"),
        Field("capacity", "cargo capacity (units)", "500"),
        Field("cargo_units", "cargo on board (units)", "0", optional=True, note="empty = 0"),
        time_field("arrival_time", "arrival time"),
    ),
    lambda v: cli.register_vessel(
        v["ship_id"],
        v["name"],
        whole_number(v["capacity"], "cargo capacity"),
        whole_number(v["cargo_units"] or "0", "cargo on board"),
        v["arrival_time"],
    ),
)

ADD_DOCK = Form(
    "Add dock",
    (
        Field("dock_id", "dock ID", "D1"),
        Field("max_ship_size", "max ship size (cargo units)", "500"),
        Field("hourly_rate", "hourly rate (per hour docked)", "120"),
    ),
    lambda v: cli.add_dock(
        v["dock_id"],
        whole_number(v["max_ship_size"], "max ship size"),
        number(v["hourly_rate"], "hourly rate"),
    ),
)

ADD_WAREHOUSE = Form(
    "Add warehouse",
    (
        Field("warehouse_id", "warehouse ID", "W-NORTH"),
        Field("capacity", "storage capacity (units)", "200"),
        Field("daily_rate_per_unit", "daily rate (per unit per day)", "1.5"),
    ),
    lambda v: cli.add_warehouse(
        v["warehouse_id"],
        whole_number(v["capacity"], "storage capacity"),
        number(v["daily_rate_per_unit"], "daily rate"),
    ),
)

DOCK_SHIP = Form(
    "Dock ship",
    (
        Field(
            "ship_id",
            "ship ID",
            "MV-ATLAS",
            choices=lambda port: listed("ships waiting", waiting_ship_ids(port)),
        ),
        Field(
            "dock_id",
            "dock ID",
            "D1",
            choices=lambda port: listed("free docks", free_dock_ids(port)),
        ),
        time_field("docked_at", "docked at"),
    ),
    lambda v: cli.dock_vessel(v["ship_id"], v["dock_id"], v["docked_at"]),
)

UNLOAD_CARGO = Form(
    "Unload cargo",
    (
        DOCKED_SHIP,
        WAREHOUSE,
        Field("units", "units to unload", "30"),
        time_field("stored_at", "stored at"),
    ),
    lambda v: cli.unload_cargo(
        v["ship_id"], v["warehouse_id"], whole_number(v["units"], "units"), v["stored_at"]
    ),
)

LOAD_CARGO = Form(
    "Load cargo",
    (
        DOCKED_SHIP,
        WAREHOUSE,
        Field("units", "units to load", "10"),
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


def field_note(field: Field, port: Port | None) -> str:
    if field.choices is None or port is None:
        return field.note
    return field.choices(port)


class FormScreen(ModalScreen[str | None]):
    BINDINGS = [Binding("escape", "cancel", "cancel")]

    def __init__(self, form: Form, prefill: dict[str, str], port: Port | None) -> None:
        super().__init__()
        self.form = form
        self.prefill = prefill
        self.port = port

    def compose(self) -> ComposeResult:
        with Vertical(id="form"):
            yield Label(self.form.title, id="form-title")
            for field in self.form.fields:
                label = f"{field.label} (optional)" if field.optional else field.label
                yield Label(label, classes="field-label")
                yield Input(
                    value=self.prefill.get(field.key, ""),
                    placeholder=field.placeholder,
                    id=f"field-{field.key}",
                )
                note = field_note(field, self.port)
                if note:
                    yield Label(note, classes="field-note")
            yield Label("", id="form-error")
            yield Label(PLAIN_HINT, id="form-hint")

    def on_mount(self) -> None:
        inputs = list(self.query(Input))
        next((box for box in inputs if not box.value), inputs[-1]).focus()

    def inputs(self) -> list[Input]:
        return list(self.query(Input))

    def value(self, field: Field) -> str:
        return self.query_one(f"#field-{field.key}", Input).value.strip()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input is not self.inputs()[-1]:
            self.focus_next()
            return
        self.action_save()

    def show_error(self, message: str) -> None:
        error = self.query_one("#form-error", Label)
        error.update(message)
        error.add_class("shown")

    def action_save(self) -> None:
        missing = [f for f in self.form.fields if not f.optional and not self.value(f)]
        if missing:
            self.show_error(f"{missing[0].label} is required")
            self.query_one(f"#field-{missing[0].key}", Input).focus()
            return
        values = {field.key: self.value(field) for field in self.form.fields}
        succeeded, message = run_command(lambda: self.form.submit(values))
        if succeeded:
            self.dismiss(message)
        else:
            self.show_error(message)

    def action_cancel(self) -> None:
        self.dismiss(None)


PLAIN_KEYS = (
    ("↑ ↓", "move between rows"),
    ("1 2 3 4", "jump to a tab"),
    ("n", "add a ship, dock or warehouse, on its tab"),
    ("d", "dock the selected ship"),
    ("u", "unload cargo into a warehouse"),
    ("l", "load cargo onto a ship"),
    ("r", "reload the data files"),
    ("?", "show this help"),
    ("q", "quit"),
)
FORM_KEYS = (
    ("enter", "next box, saves on the last one"),
    ("esc", "cancel"),
)


def key_list(title: str, keys: tuple[tuple[str, str], ...]) -> Text:
    text = Text(title + "\n", style="dim")
    for key, meaning in keys:
        text.append(f"{key:<15}", style="bold")
        text.append(meaning + "\n")
    text.rstrip()
    return text


class HelpScreen(ModalScreen[None]):
    BINDINGS = [
        Binding("escape", "close"),
        Binding("q", "close"),
        Binding("question_mark", "close"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="help"):
            yield Label("Keys", id="help-title")
            yield Label(key_list("tables", PLAIN_KEYS))
            yield Label(key_list("forms", FORM_KEYS), id="help-forms")
            yield Label("esc, q or ? closes this", id="help-close")

    def action_close(self) -> None:
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
    #form { width: 52; height: auto; padding: 1 3; border: round ansi_default; }
    #form-title { text-style: bold; }
    .field-label { text-style: dim; margin-top: 1; }
    .field-note { text-style: dim; }
    #form Input {
        height: 1; padding: 0 1; border: none;
        background: ansi_default; border-left: outer ansi_bright_black;
    }
    #form Input:focus { border-left: outer ansi_default; text-style: bold; }
    #form Input > .input--placeholder { text-style: dim; }
    #form-error { color: ansi_red; display: none; width: 100%; margin-top: 1; }
    HelpScreen { align: center middle; background: ansi_default; }
    #help { width: 64; height: auto; padding: 1 3; border: round ansi_default; }
    #help-title { text-style: bold; margin-bottom: 1; }
    #help-forms, #help-close { margin-top: 1; }
    #help-close { text-style: dim; }
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
        Binding("question_mark", "help", "help", key_display="?"),
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
        self.port: Port | None = None

    def compose(self) -> ComposeResult:
        yield ShipArt()
        yield Label("", id="summary")
        with TabbedContent(initial="ships"):
            for tab_id in TABS:
                with TabPane(tab_id.capitalize(), id=tab_id):
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

    def action_help(self) -> None:
        self.push_screen(HelpScreen())

    def action_refresh(self) -> None:
        try:
            port = read_port()
            fees = storage.fees_by_ship(port.stored, port.warehouses, current_time())
        except (OSError, ValueError) as error:
            self.notify(f"could not read the port files: {error}", severity="error")
            return
        self.port = port
        self.fill_ships(port)
        self.fill_docks(port)
        self.fill_warehouses(port)
        self.fill_fees(port, fees)
        self.show_summary(port)

    def fill_ships(self, port: Port) -> None:
        table = self.table("ships")
        table.clear()
        for ship in port.ships:
            dock_id = status.current_dock_id(ship.ship_id, port.dockings)
            table.add_row(
                Text(ship.ship_id, style="bold"),
                ship.name,
                Text(ship.arrival_time.replace("T", " "), style="dim"),
                fill_bar(ship.cargo_units, ship.capacity),
                dock_id or Text("·", style="dim"),
                key=ship.ship_id,
            )

    def fill_docks(self, port: Port) -> None:
        ship_at_dock = {docking.dock_id: docking.ship_id for docking in port.dockings}
        table = self.table("docks")
        table.clear()
        for dock in port.docks:
            table.add_row(
                Text(dock.dock_id, style="bold"),
                str(dock.max_ship_size),
                Text(f"{dock.hourly_rate:.2f}", style="dim"),
                ship_at_dock.get(dock.dock_id, Text("free", style="dim")),
                key=dock.dock_id,
            )

    def fill_warehouses(self, port: Port) -> None:
        table = self.table("warehouses")
        table.clear()
        for warehouse in port.warehouses:
            table.add_row(
                Text(warehouse.warehouse_id, style="bold"),
                fill_bar(warehouse.stored_units, warehouse.capacity),
                str(free_units(warehouse)),
                Text(f"{warehouse.daily_rate_per_unit:.2f}", style="dim"),
                key=warehouse.warehouse_id,
            )

    def fill_fees(self, port: Port, fees: dict[str, float]) -> None:
        units = storage.units_stored_by_ship(port.stored)
        table = self.table("fees")
        table.clear()
        for ship_id, fee in sorted(fees.items()):
            table.add_row(
                Text(ship_id, style="bold"),
                str(units.get(ship_id, 0)),
                Text(f"{fee:.2f}", style="" if fee else "dim"),
                key=ship_id,
            )

    def show_summary(self, port: Port) -> None:
        summary = status.describe_port_summary(
            port.ships, port.docks, port.warehouses, port.dockings
        )
        self.query_one("#summary", Label).update(summary)

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
        def saved(message: str | None) -> None:
            if message is not None:
                self.notify(message)
                self.action_refresh()

        self.push_screen(FormScreen(form, prefill, self.port), saved)
