#!/usr/bin/env python3
"""Entry point for pybonsai."""

from __future__ import annotations

import curses
import locale
import os
import sys

from .config import parse_args
from .tree import run


def main() -> None:
    locale.setlocale(locale.LC_ALL, "")

    if not os.isatty(sys.stdout.fileno()):
        print("error: pybonsai requires a terminal (TTY)", file=sys.stderr)
        sys.exit(1)

    conf = parse_args()

    stdscr = curses.initscr()
    try:
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)
        stdscr.nodelay(True)
        stdscr.keypad(True)
        output = run(stdscr, conf)
    except KeyboardInterrupt:
        output = None
    finally:
        try:
            stdscr.keypad(False)
            curses.nocbreak()
            curses.echo()
            curses.endwin()
        except curses.error:
            pass

    if output:
        sys.stdout.write(output)


if __name__ == "__main__":
    main()
