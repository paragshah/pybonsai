"""Core tree generation logic for pybonsai."""

from __future__ import annotations

import curses
import curses.panel
import enum
import random
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import Config


class BranchType(enum.IntEnum):
    TRUNK = 0
    SHOOT_LEFT = 1
    SHOOT_RIGHT = 2
    DYING = 3
    DEAD = 4


class GrowthResult(enum.IntEnum):
    COMPLETE = 0
    RESIZE = 1


class InputResult(enum.IntEnum):
    CONTINUE = 0
    QUIT = 1
    RESIZE = 2


# Color pair IDs matching the C version
PAIR_LEAF_DARK = 1
PAIR_WOOD_DARK = 2
PAIR_LEAF_BRIGHT = 3
PAIR_WOOD_BRIGHT = 4
PAIR_TEXT = 5


@dataclass
class Counters:
    branches: int = 0
    shoots: int = 0
    shoot_counter: int = 0
    growth_steps: int = 0
    replay_until: int = 0


@dataclass
class Windows:
    base_win: curses.window | None = None
    tree_win: curses.window | None = None


def save_to_file(path: str, seed: int, branch_count: int) -> None:
    with open(path, "w") as f:
        f.write(f"{seed} {branch_count}")


def load_from_file(conf: Config) -> None:
    with open(conf.load_file) as f:
        parts = f.read().split()
        if len(parts) >= 2:
            conf.seed = int(parts[0])
            conf.target_branch_count = int(parts[1])


def _check_key(win: curses.window, conf: Config) -> InputResult:
    """Check for input on the given window.

    Use a subwindow (e.g. tree_win) rather than stdscr to avoid the
    implicit wrefresh(stdscr) in getch() which would blank panel content.
    """
    try:
        key = win.getch()
    except curses.error:
        key = -1
    if key == curses.KEY_RESIZE:
        return InputResult.RESIZE
    if (conf.screensaver and key != -1) or key == ord("q"):
        return InputResult.QUIT
    return InputResult.CONTINUE


def _choose_color(win: curses.window, branch_type: BranchType) -> None:
    if branch_type in (BranchType.TRUNK, BranchType.SHOOT_LEFT, BranchType.SHOOT_RIGHT):
        if random.randint(0, 1) == 0:
            win.attron(curses.A_BOLD | curses.color_pair(PAIR_WOOD_BRIGHT))
        else:
            win.attron(curses.color_pair(PAIR_WOOD_DARK))
    elif branch_type == BranchType.DYING:
        if random.randint(0, 9) == 0:
            win.attron(curses.A_BOLD | curses.color_pair(PAIR_LEAF_BRIGHT))
        else:
            win.attron(curses.color_pair(PAIR_LEAF_BRIGHT))
    elif branch_type == BranchType.DEAD:
        if random.randint(0, 2) == 0:
            win.attron(curses.A_BOLD | curses.color_pair(PAIR_LEAF_DARK))
        else:
            win.attron(curses.color_pair(PAIR_LEAF_DARK))


def _set_deltas(branch_type: BranchType, life: int, age: int, multiplier: int) -> tuple[int, int]:
    dx = dy = 0

    if branch_type == BranchType.TRUNK:
        if age <= 2 or life < 4:
            dy = 0
            dx = random.randint(0, 2) - 1
        elif age < multiplier * 3:
            dy = -1 if age % int(multiplier * 0.5) == 0 else 0
            dice = random.randint(0, 9)
            if dice == 0:
                dx = -2
            elif dice <= 3:
                dx = -1
            elif dice <= 5:
                dx = 0
            elif dice <= 8:
                dx = 1
            else:
                dx = 2
        else:
            dice = random.randint(0, 9)
            dy = -1 if dice > 2 else 0
            dx = random.randint(0, 2) - 1

    elif branch_type == BranchType.SHOOT_LEFT:
        dice = random.randint(0, 9)
        if dice <= 1:
            dy = -1
        elif dice <= 7:
            dy = 0
        else:
            dy = 1

        dice = random.randint(0, 9)
        if dice <= 1:
            dx = -2
        elif dice <= 5:
            dx = -1
        elif dice <= 8:
            dx = 0
        else:
            dx = 1

    elif branch_type == BranchType.SHOOT_RIGHT:
        dice = random.randint(0, 9)
        if dice <= 1:
            dy = -1
        elif dice <= 7:
            dy = 0
        else:
            dy = 1

        dice = random.randint(0, 9)
        if dice <= 1:
            dx = 2
        elif dice <= 5:
            dx = 1
        elif dice <= 8:
            dx = 0
        else:
            dx = -1

    elif branch_type == BranchType.DYING:
        dice = random.randint(0, 9)
        if dice <= 1:
            dy = -1
        elif dice <= 8:
            dy = 0
        else:
            dy = 1

        dice = random.randint(0, 14)
        if dice == 0:
            dx = -3
        elif dice <= 2:
            dx = -2
        elif dice <= 5:
            dx = -1
        elif dice <= 8:
            dx = 0
        elif dice <= 11:
            dx = 1
        elif dice <= 13:
            dx = 2
        else:
            dx = 3

    elif branch_type == BranchType.DEAD:
        dice = random.randint(0, 9)
        if dice <= 2:
            dy = -1
        elif dice <= 6:
            dy = 0
        else:
            dy = 1
        dx = random.randint(0, 2) - 1

    return dx, dy


def _choose_string(conf: Config, branch_type: BranchType, life: int, dx: int, dy: int) -> str:
    bt = BranchType.DYING if life < 4 else branch_type

    if bt == BranchType.TRUNK:
        if dy == 0:
            return "/~"
        elif dx < 0:
            return "\\|"
        elif dx == 0:
            return "/|\\"
        else:
            return "|/"

    elif bt == BranchType.SHOOT_LEFT:
        if dy > 0:
            return "\\"
        elif dy == 0:
            return "\\_"
        elif dx < 0:
            return "\\|"
        elif dx == 0:
            return "/|"
        else:
            return "/"

    elif bt == BranchType.SHOOT_RIGHT:
        if dy > 0:
            return "/"
        elif dy == 0:
            return "_/"
        elif dx < 0:
            return "\\|"
        elif dx == 0:
            return "/|"
        else:
            return "/"

    else:  # DYING or DEAD
        return random.choice(conf.leaves)


def _branch(stdscr: curses.window, conf: Config, wins: Windows, counters: Counters,
            y: int, x: int, branch_type: BranchType, life: int) -> GrowthResult:
    counters.branches += 1
    age = 0
    shoot_cooldown = conf.multiplier

    while life > 0:
        result = _check_key(wins.tree_win, conf)
        if result == InputResult.QUIT:
            return GrowthResult.COMPLETE  # caller handles cleanup
        if result == InputResult.RESIZE:
            return GrowthResult.RESIZE

        life -= 1
        age = conf.life_start - life

        dx, dy = _set_deltas(branch_type, life, age, conf.multiplier)

        if dy > 0 and y > (conf.growth_height - 2):
            dy -= 1

        if life < 3:
            if _branch(stdscr, conf, wins, counters, y, x, BranchType.DEAD, life) == GrowthResult.RESIZE:
                return GrowthResult.RESIZE

        elif branch_type == BranchType.TRUNK and life < (conf.multiplier + 2):
            if _branch(stdscr, conf, wins, counters, y, x, BranchType.DYING, life) == GrowthResult.RESIZE:
                return GrowthResult.RESIZE

        elif branch_type in (BranchType.SHOOT_LEFT, BranchType.SHOOT_RIGHT) and life < (conf.multiplier + 2):
            if _branch(stdscr, conf, wins, counters, y, x, BranchType.DYING, life) == GrowthResult.RESIZE:
                return GrowthResult.RESIZE

        elif branch_type == BranchType.TRUNK and (random.randint(0, 2) == 0 or life % conf.multiplier == 0):
            if random.randint(0, 7) == 0 and life > 7:
                shoot_cooldown = conf.multiplier * 2
                if _branch(stdscr, conf, wins, counters, y, x, BranchType.TRUNK,
                           life + random.randint(0, 4) - 2) == GrowthResult.RESIZE:
                    return GrowthResult.RESIZE
            elif shoot_cooldown <= 0:
                shoot_cooldown = conf.multiplier * 2
                shoot_life = life + conf.multiplier
                counters.shoots += 1
                counters.shoot_counter += 1

                shoot_type = BranchType.SHOOT_LEFT if counters.shoot_counter % 2 == 1 else BranchType.SHOOT_RIGHT
                if _branch(stdscr, conf, wins, counters, y, x, shoot_type, shoot_life) == GrowthResult.RESIZE:
                    return GrowthResult.RESIZE

        shoot_cooldown -= 1
        x += dx
        y += dy

        _choose_color(wins.tree_win, branch_type)
        branch_str = _choose_string(conf, branch_type, life, dx, dy)

        try:
            wins.tree_win.addstr(y, x, branch_str)
        except curses.error:
            pass  # out of bounds is fine

        wins.tree_win.attroff(curses.A_BOLD)

        counters.growth_steps += 1
        if (conf.live and counters.growth_steps >= counters.replay_until
                and not (conf.load and counters.branches < conf.target_branch_count)):
            curses.panel.update_panels()
            curses.doupdate()
            time.sleep(conf.time_step)

    return GrowthResult.COMPLETE


def _draw_base(win: curses.window, base_type: int) -> None:
    try:
        if base_type == 1:
            win.attron(curses.A_BOLD | curses.color_pair(PAIR_TEXT))
            win.addstr(":")
            win.attron(curses.color_pair(PAIR_LEAF_BRIGHT))
            win.addstr("___________")
            win.attron(curses.color_pair(PAIR_WOOD_BRIGHT))
            win.addstr("./~~~\\.")
            win.attron(curses.color_pair(PAIR_LEAF_BRIGHT))
            win.addstr("___________")
            win.attron(curses.color_pair(PAIR_TEXT))
            win.addstr(":")

            win.addstr(1, 0, " \\                           / ")
            win.addstr(2, 0, "  \\_________________________/ ")
            win.addstr(3, 0, "  (_)                     (_)")
            win.attroff(curses.A_BOLD)

        elif base_type == 2:
            win.attron(curses.color_pair(PAIR_TEXT))
            win.addstr("(")
            win.attron(curses.color_pair(PAIR_LEAF_BRIGHT))
            win.addstr("---")
            win.attron(curses.color_pair(PAIR_WOOD_BRIGHT))
            win.addstr("./~~~\\.")
            win.attron(curses.color_pair(PAIR_LEAF_BRIGHT))
            win.addstr("---")
            win.attron(curses.color_pair(PAIR_TEXT))
            win.addstr(")")

            win.addstr(1, 0, " (           ) ")
            win.addstr(2, 0, "  (_________)  ")
    except curses.error:
        pass


def _set_base_geometry(conf: Config, rows: int, cols: int) -> None:
    if conf.base_type == 1:
        conf.base_width = 31
        conf.base_height = 4
    elif conf.base_type == 2:
        conf.base_width = 15
        conf.base_height = 3
    else:
        conf.base_width = 0
        conf.base_height = 0

    if conf.automatic_base_position:
        if conf.base_width > cols or conf.base_height > rows:
            conf.base_width = 0
            conf.base_height = 0
        conf.base_origin_y = rows - conf.base_height
        conf.base_origin_x = (cols // 2) - (conf.base_width // 2)


def _wrap_message(message: str, max_width: int) -> list[str]:
    """Word-wrap a message to fit within max_width columns."""
    lines: list[str] = []
    for paragraph in message.split("\n"):
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current = words[0]
        for word in words[1:]:
            if len(current) + 1 + len(word) <= max_width:
                current += " " + word
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines if lines else [""]


def _draw_message_on_win(win: curses.window, message: str) -> None:
    """Draw a bordered message box directly onto the given window."""
    rows, cols = win.getmaxyx()
    if cols < 5 or rows < 3:
        return

    max_width = max(1, (cols - 4) // 4)
    lines = _wrap_message(message, max_width)

    content_width = max(max(len(line) for line in lines), 1)
    content_height = min(len(lines), rows - 2)

    border_w = content_width + 4
    border_h = content_height + 2
    border_y = (rows * 7) // 10 - 1
    border_x = (cols * 7) // 10 - 2

    border_y = max(0, border_y)
    border_x = max(0, border_x)
    if border_y + border_h > rows:
        border_y = rows - border_h
    if border_x + border_w > cols:
        border_x = cols - border_w
    if border_y < 0 or border_x < 0:
        return

    try:
        # Draw border
        win.attron(curses.color_pair(PAIR_TEXT) | curses.A_BOLD)
        win.addstr(border_y, border_x, "+" + "-" * (border_w - 2) + "+")
        for r in range(1, border_h - 1):
            win.addstr(border_y + r, border_x, "|")
            win.addstr(border_y + r, border_x + border_w - 1, "|")
        win.addstr(border_y + border_h - 1, border_x,
                   "+" + "-" * (border_w - 2) + "+")
        win.attroff(curses.A_BOLD)

        # Draw message text
        for i, line in enumerate(lines[:content_height]):
            try:
                win.addstr(border_y + 1 + i, border_x + 2,
                           line[:content_width])
            except curses.error:
                pass
    except curses.error:
        pass


def _init_colors(conf: Config) -> None:
    if not curses.has_colors():
        return
    curses.start_color()
    try:
        curses.use_default_colors()
        bg = -1
    except curses.error:
        bg = curses.COLOR_BLACK

    num_colors = curses.COLORS
    for i in range(4):
        color_id = conf.colors[i]
        if num_colors < 256:
            color_id = color_id % 8
        curses.init_pair(i + 1, color_id, bg)

    if num_colors < 256:
        curses.init_pair(5, 7, bg)
    else:
        curses.init_pair(5, 8, bg)


def _setup_wins(stdscr: curses.window, conf: Config, wins: Windows) -> None:
    rows, cols = stdscr.getmaxyx()
    _set_base_geometry(conf, rows, cols)

    if conf.base_width > 0 and conf.base_height > 0:
        try:
            wins.base_win = curses.newwin(conf.base_height, conf.base_width,
                                          conf.base_origin_y, conf.base_origin_x)
            _draw_base(wins.base_win, conf.base_type)
            wins.base_win.overlay(stdscr)
        except curses.error:
            wins.base_win = None
    stdscr.noutrefresh()

    wins.tree_win = curses.newwin(conf.base_origin_y, cols, 0, 0)
    wins.tree_win.nodelay(True)
    wins.tree_win.keypad(True)
    curses.panel.new_panel(wins.tree_win)

    if conf.text and conf.text_origin_y >= 0 and conf.text_origin_x >= 0:
        try:
            stdscr.addstr(conf.text_origin_y, conf.text_origin_x, conf.text)
            wins.tree_win.addstr(conf.text_origin_y, conf.text_origin_x, conf.text)
        except curses.error:
            pass


def _grow_tree(stdscr: curses.window, conf: Config, wins: Windows,
               counters: Counters, replay_until: int = 0) -> GrowthResult:
    counters.shoots = 0
    counters.branches = 0
    counters.shoot_counter = random.randint(0, 2**31)
    counters.growth_steps = 0
    counters.replay_until = replay_until

    result = _branch(stdscr, conf, wins, counters,
                     conf.base_origin_y - 1,
                     conf.base_origin_x + conf.base_width // 2,
                     BranchType.TRUNK, conf.life_start)
    if result == GrowthResult.RESIZE:
        return result

    curses.panel.update_panels()
    curses.doupdate()
    return GrowthResult.COMPLETE


def _redraw(stdscr: curses.window, conf: Config, wins: Windows, counters: Counters) -> None:
    result = GrowthResult.RESIZE
    replay_until = counters.growth_steps
    while result == GrowthResult.RESIZE:
        random.seed(conf.seed)
        stdscr.erase()
        stdscr.noutrefresh()
        wins.base_win = None
        wins.tree_win = None
        curses.resize_term(*stdscr.getmaxyx())
        _setup_wins(stdscr, conf, wins)
        result = _grow_tree(stdscr, conf, wins, counters, replay_until)
        if result == GrowthResult.RESIZE and counters.growth_steps > replay_until:
            replay_until = counters.growth_steps
    if conf.message and wins.tree_win:
        _draw_message_on_win(wins.tree_win, conf.message)


def _print_tree(stdscr: curses.window, wins: Windows) -> str:
    """Capture the tree as an ANSI-colored string for printing after curses exits."""
    rows, cols = stdscr.getmaxyx()

    # Overlay windows onto stdscr like the C version
    if wins.base_win:
        wins.base_win.overlay(stdscr)
    if wins.tree_win:
        wins.tree_win.overlay(stdscr)

    output_lines: list[str] = []
    for y in range(rows):
        line = ""
        x = 0
        while x < cols:
            try:
                ch = stdscr.inch(y, x)
            except curses.error:
                ch = ord(" ")

            char = chr(ch & curses.A_CHARTEXT)
            attrs = ch & curses.A_ATTRIBUTES
            pair_num = curses.pair_number(ch)
            bold = bool(attrs & curses.A_BOLD)

            if pair_num > 0:
                try:
                    fg, _bg = curses.pair_content(pair_num)
                except curses.error:
                    fg = 0

                ansi = ""
                if bold:
                    ansi += "\033[1m"
                else:
                    ansi += "\033[0m"
                if fg <= 0:
                    ansi += "\033[0m"
                elif fg >= 16:
                    ansi += f"\033[38;5;{fg}m"
                elif fg <= 7:
                    ansi += f"\033[3{fg}m"
                else:
                    ansi += f"\033[9{fg - 8}m"
                line += ansi + char
            else:
                if bold:
                    line += "\033[1m" + char
                else:
                    line += "\033[0m" + char
            x += 1
        output_lines.append(line)

    return "\n".join(output_lines) + "\033[0m\n"


def run(stdscr: curses.window, conf: Config) -> str | None:
    """Main entry point — expects curses already initialized by the caller."""
    _init_colors(conf)

    if conf.load:
        try:
            load_from_file(conf)
        except (OSError, ValueError):
            pass

    if conf.seed == 0:
        conf.seed = int(time.time())
    random.seed(conf.seed)

    printed_output = None

    while True:
        wins = Windows()
        stdscr.erase()
        stdscr.noutrefresh()  # required before panel/doupdate calls will display
        _set_base_geometry(conf, *stdscr.getmaxyx())
        if conf.growth_height == 0:
            conf.growth_height = conf.base_origin_y
        _setup_wins(stdscr, conf, wins)

        counters = Counters()
        result = _grow_tree(stdscr, conf, wins, counters)
        if result == GrowthResult.RESIZE:
            _redraw(stdscr, conf, wins, counters)
        elif conf.message and wins.tree_win:
            _draw_message_on_win(wins.tree_win, conf.message)
            curses.panel.update_panels()
            curses.doupdate()
        if conf.load:
            conf.target_branch_count = 0

        if conf.infinite:
            wins.tree_win.timeout(int(conf.time_wait * 1000))
            while True:
                r = _check_key(wins.tree_win, conf)
                if r == InputResult.QUIT:
                    if conf.save:
                        save_to_file(conf.save_file, conf.seed, counters.branches)
                    return None
                if r == InputResult.RESIZE:
                    _redraw(stdscr, conf, wins, counters)
                    continue
                break
            random.seed(int(time.time()))
            conf.seed = int(time.time())
            stdscr.erase()
            conf.growth_height = 0
            continue
        else:
            break

    if conf.save:
        save_to_file(conf.save_file, conf.seed, counters.branches)

    if conf.write_to_file:
        ascii_output = _print_tree(stdscr, wins)
        with open(conf.write_file, "w") as f:
            f.write(ascii_output)

    if conf.print_tree:
        printed_output = _print_tree(stdscr, wins)
    else:
        wins.tree_win.timeout(100)
        while True:
            try:
                key = wins.tree_win.getch()
            except curses.error:
                key = -1
            if key == curses.KEY_RESIZE:
                _redraw(stdscr, conf, wins, counters)
                continue
            if key != -1:
                break
    return printed_output
