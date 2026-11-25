"""Configuration and argument parsing for pybonsai."""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass, field

from . import __version__


@dataclass
class Config:
    live: bool = False
    infinite: bool = False
    screensaver: bool = False
    print_tree: bool = False
    verbosity: int = 0
    life_start: int = 32
    multiplier: int = 5
    base_type: int = 1
    base_width: int = 0
    base_height: int = 0
    base_origin_x: int = -1
    base_origin_y: int = -1
    automatic_base_position: bool = True
    growth_height: int = 0
    text_origin_x: int = -1
    text_origin_y: int = -1
    seed: int = 0
    save: bool = False
    load: bool = False
    write_to_file: bool = False
    target_branch_count: int = 0

    time_wait: float = 4.0
    time_step: float = 0.03

    message: str | None = None
    text: str | None = None
    leaves: list[str] = field(default_factory=lambda: ["&"])
    colors: list[int] = field(default_factory=lambda: [2, 3, 10, 11])
    save_file: str = ""
    load_file: str = ""
    write_file: str = ""


def _default_cache_path() -> str:
    xdg = os.environ.get("XDG_CACHE_HOME", "")
    if xdg:
        return os.path.join(xdg, "cbonsai")
    home = os.environ.get("HOME", "")
    if home:
        return os.path.join(home, ".cache", "cbonsai")
    return "cbonsai"


def _parse_rowcol(value: str) -> tuple[int, int]:
    parts = value.split(",", 1)
    if len(parts) != 2:
        raise argparse.ArgumentTypeError(f"expected ROW,COL: '{value}'")
    try:
        row, col = int(parts[0]), int(parts[1])
    except ValueError:
        raise argparse.ArgumentTypeError(f"expected ROW,COL: '{value}'")
    if row < 0 or col < 0:
        raise argparse.ArgumentTypeError(f"values must be non-negative: '{value}'")
    return row, col


def parse_args(argv: list[str] | None = None) -> Config:
    parser = argparse.ArgumentParser(
        prog="pybonsai",
        description="pybonsai is a beautifully random bonsai tree generator.",
    )
    parser.add_argument("-l", "--live", action="store_true",
                        help="live mode: show each step of growth")
    parser.add_argument("-t", "--time", type=float, default=0.03, metavar="TIME",
                        help="in live mode, wait TIME secs between steps [default: 0.03]")
    parser.add_argument("-i", "--infinite", action="store_true",
                        help="infinite mode: keep growing trees")
    parser.add_argument("-w", "--wait", type=float, default=4.0, metavar="TIME",
                        help="in infinite mode, wait TIME between trees [default: 4.00]")
    parser.add_argument("-S", "--screensaver", action="store_true",
                        help="screensaver mode; equivalent to -li, quit on any keypress")
    parser.add_argument("-m", "--message", type=str, default=None,
                        help="attach message next to the tree")
    parser.add_argument("-T", "--text-origin", type=_parse_rowcol, default=None,
                        metavar="ROW,COL",
                        help="display text from stdin at ROW,COL")
    parser.add_argument("-b", "--base", type=int, default=1, metavar="INT",
                        help="ascii-art plant base to use, 0 is none")
    parser.add_argument("-g", "--geometry", type=_parse_rowcol, default=None,
                        metavar="ROW,COL",
                        help="place the plant base at ROW,COL")
    parser.add_argument("-c", "--leaf", type=str, default="&",
                        help="comma-delimited list of leaf strings [default: &]")
    parser.add_argument("-k", "--color", type=str, default="2,3,10,11",
                        help="4 comma-delimited color indices (0-255) [default: 2,3,10,11]")
    parser.add_argument("-M", "--multiplier", type=int, default=5, metavar="INT",
                        help="branch multiplier; higher -> more branching [default: 5]")
    parser.add_argument("-L", "--life", type=int, default=32, metavar="INT",
                        help="life; higher -> more growth [default: 32]")
    parser.add_argument("-p", "--print", action="store_true", dest="print_tree",
                        help="print tree to terminal when finished")
    parser.add_argument("-s", "--seed", type=int, default=0, metavar="INT",
                        help="seed random number generator")
    parser.add_argument("-W", "--write", type=str, default=None,
                        metavar="FILE",
                        help="write ascii tree to file")
    parser.add_argument("-C", "--load", type=str, nargs="?", const="", default=None,
                        metavar="FILE",
                        help="load progress from file")
    parser.add_argument("-v", "--verbose", action="count", default=0)
    parser.add_argument("-V", "--version", action="version",
                        version=f"pybonsai {__version__}")

    args = parser.parse_args(argv)

    conf = Config()
    conf.live = args.live
    conf.time_step = args.time
    conf.infinite = args.infinite
    conf.time_wait = args.wait
    conf.print_tree = args.print_tree
    conf.verbosity = args.verbose
    conf.lifeStart = args.life  # keep for compat
    conf.life_start = args.life
    conf.multiplier = args.multiplier
    conf.base_type = args.base
    conf.seed = args.seed
    conf.message = args.message

    # Leaves
    conf.leaves = [s for s in args.leaf.split(",") if s]
    if not conf.leaves:
        conf.leaves = ["&"]

    # Colors
    color_tokens = args.color.split(",")
    if len(color_tokens) != 4:
        parser.error("exactly 4 color indices required")
    try:
        conf.colors = [int(c) for c in color_tokens]
    except ValueError:
        parser.error(f"invalid color indices: '{args.color}'")

    # Geometry
    if args.geometry is not None:
        conf.base_origin_y, conf.base_origin_x = args.geometry
        conf.automatic_base_position = False

    # Text origin
    if args.text_origin is not None:
        conf.text_origin_y, conf.text_origin_x = args.text_origin
        conf.text = sys.stdin.read()

    # Infinite mode implies live mode
    if conf.infinite:
        conf.live = True

    # Screensaver
    if args.screensaver:
        conf.live = True
        conf.infinite = True
        conf.screensaver = True
        conf.save = True
        conf.load = True

    # Save/load (state persistence for screensaver)
    default_path = _default_cache_path()
    conf.save_file = default_path
    conf.load_file = default_path

    if args.load is not None:
        conf.load = True
        conf.load_file = args.load if args.load else default_path

    # Write ASCII tree to file
    if args.write is not None:
        conf.write_to_file = True
        conf.write_file = args.write

    return conf
