# pybonsai

A beautifully random bonsai tree generator for the terminal, written in Python using `curses`.

![Screenshot](screenshot.png)

`pybonsai` is a modern Python port of [cbonsai](https://gitlab.com/jallbrit/cbonsai), the original C/ncurses bonsai tree generator by [John Googled (jallbrit)](https://gitlab.com/jallbrit). It faithfully reproduces the same tree generation algorithm, base art, coloring, and CLI interface -- just in Python with no external dependencies.

There are two modes of operation: **static** (display the finished tree) and **live** (watch it grow step-by-step).

## Installation

Requires Python 3.10+ (uses only the standard library).

```bash
# Run directly
python3 -m pybonsai -l

# Or install as a CLI tool
pip install .
pybonsai -l
```

## Usage

```
usage: pybonsai [-h] [-l] [-t TIME] [-i] [-w TIME] [-S] [-m MESSAGE]
                [-T ROW,COL] [-b INT] [-g ROW,COL] [-c LEAF] [-k COLOR]
                [-M INT] [-L INT] [-p] [-s INT] [-W [FILE]] [-C [FILE]] [-v]
                [-V]

Options:
  -l, --live             live mode: show each step of growth
  -t, --time=TIME        in live mode, wait TIME secs between steps [default: 0.03]
  -i, --infinite         infinite mode: keep growing trees
  -w, --wait=TIME        in infinite mode, wait TIME between trees [default: 4.00]
  -S, --screensaver      screensaver mode; equivalent to -li, quit on any keypress
  -m, --message=STR      attach message next to the tree
  -T, --text-origin=ROW,COL
                         display text from stdin at ROW,COL
  -b, --base=INT         ascii-art plant base to use, 0 is none
  -g, --geometry=ROW,COL place the plant base at ROW,COL
  -c, --leaf=LIST        comma-delimited list of leaf strings [default: &]
  -k, --color=LIST       4 comma-delimited color indices (0-255) [default: 2,3,10,11]
  -M, --multiplier=INT   branch multiplier; higher -> more branching [default: 5]
  -L, --life=INT         life; higher -> more growth [default: 32]
  -p, --print            print tree to terminal when finished
  -s, --seed=INT         seed random number generator
  -W, --save=FILE        save progress to file
  -C, --load=FILE        load progress from file
  -v, --verbose          increase output verbosity
  -V, --version          show version
```

## Examples

```bash
# Print a tree and return to the prompt
pybonsai -p

# Watch a tree grow live
pybonsai -l

# Screensaver mode (infinite + live, quit on any key)
pybonsai -S

# Custom leaves and high branching
pybonsai -l -c '**,&&,@@' -M 10 -L 50

# Reproducible tree with a fixed seed
pybonsai -p -s 42

# Attach a message
pybonsai -l -m "hello world"
```

## Credits

This project is a Python port of **cbonsai** by **John Googled (jallbrit)**.

- Original project: https://gitlab.com/jallbrit/cbonsai
- Original license: GPL-3.0

The tree generation algorithm, branch logic, base art, and CLI interface are all derived from the original C implementation. `cbonsai` was itself inspired by [bonsai.sh](https://gitlab.com/jallbrit/bonsai.sh) (a bash version) which was a port of [this JavaScript bonsai generator](https://avelican.github.io/bonsai/) by avelican.

## License

GPL-3.0 -- same as the original cbonsai.
