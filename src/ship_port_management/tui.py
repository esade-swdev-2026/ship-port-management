import contextlib
import io
import time
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
G_CHORD_SECONDS = 1.0
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
VIM_ACTIONS = {
    "cursor_down",
    "cursor_up",
    "first_row",
    "last_row",
    "half_page_down",
    "half_page_up",
    "previous_tab",
    "next_tab",
    "put",
}
PLAIN_ACTIONS = {"load"}
FORM_NORMAL_ACTIONS = {"next_field", "previous_field", "insert", "append", "save", "cancel"}
TIME_NOTE = "e.g. 2026-10-18T09:30, empty = now"
PLAIN_HINT = "enter save · esc cancel"
INSERT_HINT = "-- INSERT --\nesc normal mode · enter next box"
NORMAL_HINT = "-- NORMAL --\nj/k box · i/a type · enter save · q cancel"


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


class FormBox(Vertical, can_focus=True):
    pass


def field_note(field: Field, port: Port | None) -> str:
    if field.choices is None or port is None:
        return field.note
    return field.choices(port)


class FormScreen(ModalScreen[str | None]):
    BINDINGS = [
        Binding("escape", "escape", "cancel"),
        Binding("j", "next_field", show=False),
        Binding("k", "previous_field", show=False),
        Binding("i", "insert", show=False),
        Binding("a", "append", show=False),
        Binding("enter", "save", show=False),
        Binding("q", "cancel", show=False),
    ]

    def __init__(
        self, form: Form, prefill: dict[str, str], port: Port | None, vim: bool = False
    ) -> None:
        super().__init__()
        self.form = form
        self.prefill = prefill
        self.port = port
        self.vim = vim
        self.field_index = 0

    def compose(self) -> ComposeResult:
        with FormBox(id="form"):
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

    def in_normal_mode(self) -> bool:
        return self.vim and isinstance(self.focused, FormBox)

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action in FORM_NORMAL_ACTIONS:
            return self.in_normal_mode()
        return True

    def on_descendant_focus(self, event: events.DescendantFocus) -> None:
        if isinstance(self.focused, Input):
            self.field_index = self.inputs().index(self.focused)
        self.show_mode()

    def show_mode(self) -> None:
        normal = self.in_normal_mode()
        hint = PLAIN_HINT if not self.vim else NORMAL_HINT if normal else INSERT_HINT
        self.query_one("#form-hint", Label).update(hint)
        for index, box in enumerate(self.inputs()):
            box.set_class(normal and index == self.field_index, "-selected")

    def action_escape(self) -> None:
        if self.vim and isinstance(self.focused, Input):
            self.query_one(FormBox).focus()
            return
        self.dismiss(None)

    def select_field(self, index: int) -> None:
        self.field_index = max(0, min(len(self.inputs()) - 1, index))
        self.show_mode()

    def action_next_field(self) -> None:
        self.select_field(self.field_index + 1)

    def action_previous_field(self) -> None:
        self.select_field(self.field_index - 1)

    def type_into_field(self, at_end: bool) -> None:
        box = self.inputs()[self.field_index]
        box.focus()
        box.cursor_position = len(box.value) if at_end else 0

    def action_insert(self) -> None:
        self.type_into_field(at_end=False)

    def action_append(self) -> None:
        self.type_into_field(at_end=True)

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
    ("v", "turn vim mode on"),
    ("?", "show this help"),
    ("q", "quit"),
)
VIM_KEYS = (
    ("j k", "move between rows"),
    ("gg G", "first / last row"),
    ("ctrl+d ctrl+u", "half a page down / up"),
    ("h l", "previous / next tab"),
    ("1 2 3 4", "jump to a tab"),
    ("n", "add a ship, dock or warehouse, on its tab"),
    ("d", "dock the selected ship"),
    ("u", "unload cargo into a warehouse"),
    ("p", "load cargo onto a ship (put)"),
    ("v", "turn vim mode off"),
    ("?", "show this help"),
    ("q", "quit"),
)
FORM_KEYS = (
    ("enter", "next box, saves on the last one"),
    ("esc", "cancel"),
)
VIM_FORM_KEYS = (
    ("esc", "normal mode, esc again cancels"),
    ("j k", "previous / next box"),
    ("i a", "type at the start / end of the box"),
    ("enter", "save"),
    ("q", "cancel"),
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

    def __init__(self, vim: bool) -> None:
        super().__init__()
        self.vim = vim

    def compose(self) -> ComposeResult:
        with Vertical(id="help"):
            yield Label("Keys" + (" · vim mode" if self.vim else ""), id="help-title")
            yield Label(key_list("tables", VIM_KEYS if self.vim else PLAIN_KEYS))
            yield Label(
                key_list("forms", VIM_FORM_KEYS if self.vim else FORM_KEYS), id="help-forms"
            )
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
    #form Input:focus, #form Input.-selected { border-left: outer ansi_default; text-style: bold; }
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
        Binding("l", "load", "load"),
        Binding("p", "put", "load"),
        Binding("j", "cursor_down", "move", key_display="hjkl"),
        Binding("k", "cursor_up", show=False),
        Binding("h", "previous_tab", show=False),
        Binding("l", "next_tab", show=False),
        Binding("g", "first_row", show=False),
        Binding("G", "last_row", show=False),
        Binding("ctrl+d", "half_page_down", show=False),
        Binding("ctrl+u", "half_page_up", show=False),
        Binding("v", "toggle_vim", "vim"),
        Binding("question_mark", "help", "help", key_display="?"),
        Binding("q", "quit", "quit"),
        Binding("r", "refresh", show=False),
        Binding("1", "show_tab('ships')", show=False),
        Binding("2", "show_tab('docks')", show=False),
        Binding("3", "show_tab('warehouses')", show=False),
        Binding("4", "show_tab('fees')", show=False),
    ]
    FORMS = {"dock": DOCK_SHIP, "unload": UNLOAD_CARGO, "load": LOAD_CARGO}
    SHOW_SHIP = True

    def __init__(self, vim: bool = False) -> None:
        super().__init__()
        self.register_theme(TERMINAL)
        self.theme = TERMINAL.name
        self.vim_mode = vim
        self.last_g_press = 0.0
        self.port: Port | None = None

    def compose(self) -> ComposeResult:
        if self.SHOW_SHIP:
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
        for art in self.query(ShipArt):
            art.display = event.size.height >= MIN_HEIGHT_FOR_SHIP

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action in VIM_ACTIONS:
            return self.vim_mode
        if action in PLAIN_ACTIONS:
            return not self.vim_mode
        return True

    def after_change(self) -> None:
        pass

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        self.after_change()

    def table(self, tab_id: str) -> DataTable[str | Text]:
        return self.query_one(f"#{tab_id}-table", DataTable)

    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        event.pane.query_one(DataTable).focus()
        self.after_change()

    def action_show_tab(self, tab_id: str) -> None:
        self.query_one(TabbedContent).active = tab_id

    def active_table(self) -> DataTable[str | Text]:
        return self.table(self.query_one(TabbedContent).active)

    def move_to_row(self, row: int) -> None:
        table = self.active_table()
        if table.row_count:
            table.move_cursor(row=max(0, min(table.row_count - 1, row)))

    def action_cursor_down(self) -> None:
        self.move_to_row(self.active_table().cursor_row + 1)

    def action_cursor_up(self) -> None:
        self.move_to_row(self.active_table().cursor_row - 1)

    def action_half_page_down(self) -> None:
        table = self.active_table()
        self.move_to_row(table.cursor_row + max(1, table.size.height // 2))

    def action_half_page_up(self) -> None:
        table = self.active_table()
        self.move_to_row(table.cursor_row - max(1, table.size.height // 2))

    def action_first_row(self) -> None:
        pressed_at = time.monotonic()
        if pressed_at - self.last_g_press <= G_CHORD_SECONDS:
            self.move_to_row(0)
            self.last_g_press = 0.0
        else:
            self.last_g_press = pressed_at

    def action_last_row(self) -> None:
        self.move_to_row(self.active_table().row_count - 1)

    def move_tab(self, step: int) -> None:
        index = TABS.index(self.query_one(TabbedContent).active) + step
        self.action_show_tab(TABS[max(0, min(len(TABS) - 1, index))])

    def action_next_tab(self) -> None:
        self.move_tab(1)

    def action_previous_tab(self) -> None:
        self.move_tab(-1)

    def action_help(self) -> None:
        self.push_screen(HelpScreen(self.vim_mode))

    def action_toggle_vim(self) -> None:
        self.vim_mode = not self.vim_mode
        self.refresh_bindings()
        self.action_refresh()
        self.notify("vim mode on" if self.vim_mode else "vim mode off")

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
        self.after_change()

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
        self.query_one("#summary", Label).update(summary + (" · vim" if self.vim_mode else ""))

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

    def action_load(self) -> None:
        self.action_open_form("load")

    def action_put(self) -> None:
        self.action_open_form("load")

    def open(self, form: Form, prefill: dict[str, str]) -> None:
        def saved(message: str | None) -> None:
            if message is not None:
                self.notify(message)
                self.action_refresh()

        self.push_screen(FormScreen(form, prefill, self.port, self.vim_mode), saved)
