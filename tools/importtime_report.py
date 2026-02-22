#!/usr/bin/env python
"""
Parse the output of `python -X importtime` and display it with percentages.

Usage (pipe):
    python -X importtime -m IPython -c exit 2>&1 | python tools/importtime_report.py

Usage (let the script run the command):
    python tools/importtime_report.py
    python tools/importtime_report.py -- -m IPython -c exit --no-banner

Options:
    --top N         Show only the top N lines by self time (default: all)
    --flat          Flat sorted list instead of tree
    --min-self MS   Hide entries whose self time is below MS milliseconds
"""

import re
import subprocess
import sys
from dataclasses import dataclass

# ── ANSI colours ────────────────────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RED    = "\033[31m"
YELLOW = "\033[33m"
CYAN   = "\033[36m"
GREEN  = "\033[32m"
WHITE  = "\033[37m"

def _colour(text: str, *codes: str) -> str:
    return "".join(codes) + text + RESET


# ── Data model ───────────────────────────────────────────────────────────────
@dataclass
class Entry:
    self_us: int
    cum_us:  int
    raw_name: str          # e.g. "    some.module"  (leading spaces = depth)
    name: str              # stripped
    depth: int             # nesting level (spaces / 2)


PATTERN = re.compile(r"import time:\s+(\d+) \|\s+(\d+) \| (.+)")


def parse(lines: list[str]) -> list[Entry]:
    entries = []
    for line in lines:
        m = PATTERN.match(line)
        if not m:
            continue
        self_us = int(m.group(1))
        cum_us  = int(m.group(2))
        raw     = m.group(3)          # leading spaces preserved
        stripped = raw.lstrip(" ")
        depth   = (len(raw) - len(stripped)) // 2
        entries.append(Entry(self_us, cum_us, raw, stripped, depth))
    return entries


# ── Formatting helpers ────────────────────────────────────────────────────────
def _bar(pct: float, width: int = 12) -> str:
    filled = round(pct / 100 * width)
    bar = "█" * filled + "░" * (width - filled)
    if pct >= 10:
        colour = RED
    elif pct >= 3:
        colour = YELLOW
    else:
        colour = GREEN
    return _colour(bar, colour)


def _fmt_ms(us: int) -> str:
    return f"{us / 1000:7.2f}"


def _pct_str(pct: float) -> str:
    s = f"{pct:5.1f}%"
    if pct >= 10:
        return _colour(s, BOLD, RED)
    elif pct >= 3:
        return _colour(s, YELLOW)
    return _colour(s, DIM)


# ── Report modes ─────────────────────────────────────────────────────────────
HEADER = (
    f"{'self ms':>7}  {'self%':>6}  {'cum ms':>7}  {'cum%':>6}  {'':12}  module"
)
RULE = "─" * 80


def _print_header(total_self_us: int, total_cum_us: int, cmd: str) -> None:
    print(_colour(f"\n  Command : {cmd}", BOLD))
    print(_colour(f"  Total self-time : {total_self_us/1000:.1f} ms", BOLD))
    print(_colour(f"  Total cum  (top): {total_cum_us/1000:.1f} ms\n", BOLD))
    print(_colour(HEADER, BOLD, CYAN))
    print(_colour(RULE, DIM))


def print_tree(entries: list[Entry], total_self: int, total_cum: int,
               min_self_us: int = 0) -> None:
    for e in entries:
        if e.self_us < min_self_us:
            continue
        self_pct = e.self_us / total_self * 100 if total_self else 0
        cum_pct  = e.cum_us  / total_cum  * 100 if total_cum  else 0
        indent   = "  " * e.depth + e.name
        print(
            f"{_fmt_ms(e.self_us)}  {_pct_str(self_pct)}  "
            f"{_fmt_ms(e.cum_us)}  {_pct_str(cum_pct)}  "
            f"{_bar(self_pct)}  {indent}"
        )


def print_flat(entries: list[Entry], total_self: int, total_cum: int,
               top: int | None, min_self_us: int = 0) -> None:
    # Deduplicate: keep highest cumulative per name
    seen: dict[str, Entry] = {}
    for e in entries:
        if e.name not in seen or e.cum_us > seen[e.name].cum_us:
            seen[e.name] = e

    ranked = sorted(seen.values(), key=lambda e: -e.self_us)
    if min_self_us:
        ranked = [e for e in ranked if e.self_us >= min_self_us]
    if top:
        ranked = ranked[:top]

    for e in ranked:
        self_pct = e.self_us / total_self * 100 if total_self else 0
        cum_pct  = e.cum_us  / total_cum  * 100 if total_cum  else 0
        print(
            f"{_fmt_ms(e.self_us)}  {_pct_str(self_pct)}  "
            f"{_fmt_ms(e.cum_us)}  {_pct_str(cum_pct)}  "
            f"{_bar(self_pct)}  {e.name}"
        )


# ── CLI ───────────────────────────────────────────────────────────────────────
def main() -> None:
    args = sys.argv[1:]

    # Parse our own flags
    flat     = "--flat"  in args;  args = [a for a in args if a != "--flat"]
    top      = None
    min_self = 0.0
    rest     = []
    i = 0
    while i < len(args):
        if args[i] == "--top" and i + 1 < len(args):
            top = int(args[i + 1]); i += 2
        elif args[i] == "--min-self" and i + 1 < len(args):
            min_self = float(args[i + 1]); i += 2
        elif args[i] == "--":
            rest = args[i + 1:]; i = len(args)
        else:
            rest.append(args[i]); i += 1

    min_self_us = int(min_self * 1000)

    # Decide whether to read from stdin or run the command
    if not sys.stdin.isatty():
        raw = sys.stdin.read()
        cmd_label = "(stdin)"
    else:
        target = rest if rest else ["-m", "IPython", "-c", "exit"]
        cmd = [sys.executable, "-X", "importtime"] + target
        cmd_label = " ".join(cmd)
        print(_colour(f"Running: {cmd_label}", DIM), file=sys.stderr)
        result = subprocess.run(cmd, capture_output=True, text=True)
        # importtime writes to stderr
        raw = result.stderr

    lines   = raw.splitlines()
    entries = parse(lines)

    if not entries:
        print("No 'import time:' lines found.", file=sys.stderr)
        sys.exit(1)

    total_self = sum(e.self_us for e in entries)
    # Top-level cumulative = the last entry with depth 0, or the maximum
    top_level = [e for e in entries if e.depth == 0]
    total_cum  = max((e.cum_us for e in top_level), default=0) or max(e.cum_us for e in entries)

    _print_header(total_self, total_cum, cmd_label)

    if flat:
        print_flat(entries, total_self, total_cum, top, min_self_us)
    else:
        if top:
            # In tree mode, --top filters by self time but keeps tree order
            threshold = sorted(e.self_us for e in entries)[-top] if top < len(entries) else 0
            min_self_us = max(min_self_us, threshold)
        print_tree(entries, total_self, total_cum, min_self_us)

    print(_colour(RULE, DIM))


if __name__ == "__main__":
    main()
