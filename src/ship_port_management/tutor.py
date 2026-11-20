import contextlib
import tempfile
from collections.abc import Callable
from dataclasses import dataclass

from rich.text import Text
from textual.app import ComposeResult
from textual.widgets import Static, TabbedContent

from ship_port_management import cli
from ship_port_management.tui import TABS, HarbourApp, read_port, run_command


@dataclass(frozen=True)
class PortState:
    vim_mode: bool
    tab: str
    row: int
    rows: int
    ships: int
    docked: int
    stored: int


@dataclass(frozen=True)
class Lesson:
    text: str
    done: Callable[[PortState, PortState], bool]


def tab_moved(before: PortState, now: PortState) -> int:
    return TABS.index(now.tab) - TABS.index(before.tab)


LESSONS = (
    Lesson(
        "The arrow keys move between rows. Press [b]↓[/b].",
        lambda before, now: now.row > before.row,
    ),
    Lesson(
        "[b]1 2 3 4[/b] jump straight to a tab. Press [b]2[/b] to see the docks.",
        lambda before, now: now.tab == "docks",
    ),
    Lesson(
        "Press [b]1[/b] to go back to the ships.",
        lambda before, now: now.tab == "ships",
    ),
    Lesson(
        "[b]n[/b] adds something new to the tab you are on. Press [b]n[/b], fill in a ship, "
        "and press [b]enter[/b] on the last box to save it.",
        lambda before, now: now.ships > before.ships,
    ),
    Lesson(
        "[b]d[/b] docks the ship under the cursor. Move to MV-NOVA, press [b]d[/b], "
        "type D2 as the dock and press [b]enter[/b] until it saves.",
        lambda before, now: now.docked > before.docked,
    ),
    Lesson(
        "[b]u[/b] unloads cargo from a docked ship into a warehouse. Select MV-ATLAS, "
        "press [b]u[/b], type W-NORTH and 10 units, then save.",
        lambda before, now: now.stored > before.stored,
    ),
    Lesson(
        "[b]l[/b] loads cargo from a warehouse back onto a ship. "
        "Press [b]l[/b] and load 5 units from W-NORTH onto MV-ATLAS.",
        lambda before, now: now.stored < before.stored,
    ),
    Lesson(
        "Now vim mode. Press [b]v[/b] to turn it on. "
        "[b]v[/b] turns it off again whenever you like.",
        lambda before, now: now.vim_mode,
    ),
    Lesson(
        "[b]j[/b] moves down a row. Press [b]j[/b].",
        lambda before, now: now.row > before.row,
    ),
    Lesson(
        "[b]k[/b] moves up a row. Press [b]k[/b].",
        lambda before, now: now.row < before.row,
    ),
    Lesson(
        "[b]G[/b] jumps to the last row. Press [b]G[/b] (shift + g).",
        lambda before, now: now.row == now.rows - 1 and now.row > before.row,
    ),
    Lesson(
        "[b]gg[/b] jumps to the first row. Press [b]g[/b] twice.",
        lambda before, now: now.row == 0 and before.row > 0,
    ),
    Lesson(
        "[b]l[/b] moves to the next tab. Press [b]l[/b].",
        lambda before, now: tab_moved(before, now) > 0,
    ),
    Lesson(
        "[b]h[/b] moves to the previous tab. Press [b]h[/b] until you are back on Ships.",
        lambda before, now: now.tab == "ships",
    ),
    Lesson(
        "In vim mode [b]l[/b] changes tabs, so loading moves to [b]p[/b] (put). "
        "Press [b]p[/b]. In the form, [b]esc[/b] switches to normal mode: [b]j[/b] and [b]k[/b] "
        "move between boxes, [b]i[/b] starts typing again and [b]enter[/b] saves. "
        "Load 5 units onto MV-ATLAS.",
        lambda before, now: now.stored < before.stored,
    ),
    Lesson(
        "That's the whole tour. [b]?[/b] shows every key whenever you forget one. "
        "Press [b]q[/b] to leave. "
        "This was a practice port, so your real data was not touched.",
        lambda before, now: False,
    ),
)


def seed_practice_port() -> None:
    run_command(lambda: cli.register_vessel("MV-ATLAS", "Atlas", 500, 120, "2026-11-01T08:00"))
    run_command(lambda: cli.register_vessel("MV-NOVA", "Nova", 200, 50, "2026-11-01T09:00"))
    run_command(lambda: cli.add_dock("D1", 500, 120))
    run_command(lambda: cli.add_dock("D2", 300, 90))
    run_command(lambda: cli.add_warehouse("W-NORTH", 1000, 1.5))
    run_command(lambda: cli.dock_vessel("MV-ATLAS", "D1", "2026-11-01T10:00"))


class TutorApp(HarbourApp):
    SHOW_SHIP = False
    CSS = (
        HarbourApp.CSS
        + """
    #lesson { margin: 1 2 0 2; padding: 0 1; border: round ansi_default; height: auto; }
    """
    )

    def __init__(self) -> None:
        super().__init__()
        self.lesson_index = 0
        self.before: PortState | None = None

    def compose(self) -> ComposeResult:
        yield Static(id="lesson")
        yield from super().compose()

    def port_state(self) -> PortState:
        port = self.port or read_port()
        tab = self.query_one(TabbedContent).active
        table = self.table(tab)
        return PortState(
            vim_mode=self.vim_mode,
            tab=tab,
            row=table.cursor_row,
            rows=table.row_count,
            ships=self.table("ships").row_count,
            docked=len(port.dockings),
            stored=sum(warehouse.stored_units for warehouse in port.warehouses),
        )

    def after_change(self) -> None:
        now = self.port_state()
        if self.before is None:
            self.before = now
        elif LESSONS[self.lesson_index].done(self.before, now):
            self.lesson_index += 1
            self.before = now
        self.show_lesson()

    def show_lesson(self) -> None:
        text = Text(f"lesson {self.lesson_index + 1} of {len(LESSONS)}\n", style="dim")
        text.append_text(Text.from_markup(LESSONS[self.lesson_index].text))
        self.query_one("#lesson", Static).update(text)


def run_tutor() -> None:
    with tempfile.TemporaryDirectory() as folder, contextlib.chdir(folder):
        seed_practice_port()
        TutorApp().run()
