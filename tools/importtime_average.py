#!/usr/bin/env python3
"""Average several ``python -X importtime`` runs into a single report.

``python -X importtime`` prints, to *stderr*, one line per imported module::

    import time: self [us] | cumulative | imported package
    import time:       146 |        146 |   _io
    import time:       846 |       1223 | _frozen_importlib_external

The ``self``/``cumulative`` columns are microseconds and the indentation of the
module name encodes the import tree. A single run is noisy; this script reads
several runs and emits one report with the per-module timings averaged, in the
same format so downstream tooling (e.g. ``tuna``) can still read it.

Usage
-----
Average existing logs (each file may itself contain several runs, split on the
``self [us]`` header line -- so ``2>>log`` appended repeatedly works too)::

    python tools/importtime_average.py run1.log run2.log run3.log

Run a command N times and average (everything after ``--`` is the command; it
must emit importtime output, i.e. include ``-X importtime``)::

    python tools/importtime_average.py -n 10 -- python -X importtime -c "import IPython"

Read a single run from stdin::

    python -X importtime -c "import IPython" 2>&1 | python tools/importtime_average.py -

Options let you sort by ``self`` or ``cumulative`` time instead of preserving
the import tree, and annotate each line with how many runs it appeared in.
"""

from __future__ import annotations

import argparse
import re
import statistics
import subprocess
import sys
import time
from dataclasses import dataclass, field


def progress(msg: str, *, done: bool = False) -> None:
    """Write a progress line to stderr (in-place when stderr is a TTY)."""
    if _QUIET:
        return
    if sys.stderr.isatty():
        # \r + clear-to-end-of-line keeps updates on a single line.
        end = "\n" if done else ""
        print(f"\r\033[K{msg}", end=end, file=sys.stderr, flush=True)
    else:
        print(msg, file=sys.stderr, flush=True)


_QUIET = False

# A data line: "import time:  <self> | <cumulative> | <indented module>"
# The header line has "self [us]" instead of a number and is used as a run
# boundary. We keep the raw module column (with indentation) to reproduce the
# tree, and strip it for the per-module key.
_LINE = re.compile(r"^import time:\s*(\d+)\s*\|\s*(\d+)\s*\|(.*)$")
_HEADER = re.compile(r"^import time:\s*self \[us\]")


@dataclass
class Module:
    """Accumulated samples for one module across runs."""

    display: str  # raw module column incl. indentation, from first sighting
    self_us: list[int] = field(default_factory=list)
    cumulative_us: list[int] = field(default_factory=list)

    @property
    def mean_self(self) -> float:
        return statistics.fmean(self.self_us)

    @property
    def mean_cumulative(self) -> float:
        return statistics.fmean(self.cumulative_us)


def parse_runs(text: str) -> list[dict[str, tuple[int, int, str]]]:
    """Split ``text`` into runs and parse each into {key: (self, cum, display)}.

    A new run starts at every importtime header line; text before the first
    header (or with no header at all) is treated as a single run.
    """
    runs: list[dict[str, tuple[int, int, str]]] = []
    current: dict[str, tuple[int, int, str]] | None = None

    def start() -> dict[str, tuple[int, int, str]]:
        d: dict[str, tuple[int, int, str]] = {}
        runs.append(d)
        return d

    for line in text.splitlines():
        if _HEADER.match(line):
            current = start()
            continue
        m = _LINE.match(line)
        if not m:
            continue
        if current is None:
            current = start()
        self_us, cum_us, display = int(m.group(1)), int(m.group(2)), m.group(3)
        key = display.strip()
        # A module is normally reported once per run; if a run somehow repeats a
        # name, keep the first (importtime prints in post-order of first import).
        current.setdefault(key, (self_us, cum_us, display))

    return [r for r in runs if r]


def collect(texts: list[str]) -> tuple[list[Module], int, int]:
    """Merge run texts into averaged modules.

    Returns (modules, n_runs, reference_index) where reference_index points at
    the run with the most modules -- used to order/indent the tree output.
    """
    runs: list[dict[str, tuple[int, int, str]]] = []
    for text in texts:
        runs.extend(parse_runs(text))
    if not runs:
        raise SystemExit("no importtime data found in input")

    modules: dict[str, Module] = {}
    for run in runs:
        for key, (self_us, cum_us, display) in run.items():
            mod = modules.get(key)
            if mod is None:
                mod = modules[key] = Module(display=display)
            mod.self_us.append(self_us)
            mod.cumulative_us.append(cum_us)

    reference_index = max(range(len(runs)), key=lambda i: len(runs[i]))
    return list(modules.values()), len(runs), reference_index, runs


def order_modules(
    modules: list[Module],
    runs: list[dict[str, tuple[int, int, str]]],
    reference_index: int,
    sort: str,
) -> list[Module]:
    by_key = {m.display.strip(): m for m in modules}
    if sort == "tree":
        ordered: list[Module] = []
        seen: set[str] = set()
        # Follow the most complete run to preserve tree order and indentation.
        for key in runs[reference_index]:
            ordered.append(by_key[key])
            seen.add(key)
        # Append modules that never appeared in the reference run.
        leftover = [m for k, m in by_key.items() if k not in seen]
        leftover.sort(key=lambda m: m.mean_self, reverse=True)
        ordered.extend(leftover)
        return ordered
    key_fn = {
        "self": lambda m: m.mean_self,
        "cumulative": lambda m: m.mean_cumulative,
    }[sort]
    return sorted(modules, key=key_fn, reverse=True)


def format_report(modules: list[Module], n_runs: int, sort: str, annotate: bool) -> str:
    lines = ["import time: self [us] | cumulative | imported package"]
    for mod in modules:
        # For flat sorts the tree indentation is meaningless, so strip it and
        # print the bare name; for "tree" keep the original indented column.
        name = mod.display if sort == "tree" else " " + mod.display.strip()
        line = "import time: %9d | %10d |%s" % (
            round(mod.mean_self),
            round(mod.mean_cumulative),
            name,
        )
        if annotate and len(mod.self_us) != n_runs:
            line += f"    # {len(mod.self_us)}/{n_runs} runs"
        lines.append(line)
    return "\n".join(lines)


def run_command(cmd: list[str], repeat: int) -> list[str]:
    texts: list[str] = []
    durations: list[float] = []
    for i in range(repeat):
        progress(f"running {i + 1}/{repeat} ...")
        started = time.perf_counter()
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        elapsed = time.perf_counter() - started
        durations.append(elapsed)
        # importtime writes to stderr; some programs also print there, but the
        # parser ignores non-matching lines.
        combined = proc.stderr + "\n" + proc.stdout
        if "import time:" not in combined:
            progress("", done=True)
            raise SystemExit(
                f"run {i + 1}: no importtime output from {cmd!r}; "
                "did you include '-X importtime'?"
            )
        texts.append(combined)
        progress(
            f"ran {i + 1}/{repeat} "
            f"(last {elapsed:.2f}s, mean {statistics.fmean(durations):.2f}s)",
            done=(i + 1 == repeat),
        )
    return texts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Average several `python -X importtime` runs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="importtime log files ('-' for stdin). Each file may contain "
        "several runs separated by the importtime header line.",
    )
    parser.add_argument(
        "-n",
        "--repeat",
        type=int,
        metavar="N",
        help="run the command after '--' N times and average those runs.",
    )
    parser.add_argument(
        "--sort",
        choices=("tree", "self", "cumulative"),
        default="tree",
        help="output order: preserve the import tree (default), or sort "
        "descending by mean self/cumulative time (flat list).",
    )
    parser.add_argument(
        "--annotate",
        action="store_true",
        help="append '# k/N runs' to modules that did not appear in every run.",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="print a short summary (run count, module count, total time) to stderr.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="suppress progress reporting on stderr.",
    )
    # Everything after '--' is the command to run.
    if argv is None:
        argv = sys.argv[1:]
    cmd: list[str] = []
    if "--" in argv:
        split = argv.index("--")
        argv, cmd = argv[:split], argv[split + 1 :]
    args = parser.parse_args(argv)

    global _QUIET
    _QUIET = args.quiet

    texts: list[str] = []
    if cmd:
        repeat = args.repeat if args.repeat is not None else 1
        if repeat < 1:
            parser.error("--repeat must be >= 1")
        texts.extend(run_command(cmd, repeat))
    elif args.repeat is not None:
        parser.error("--repeat requires a command after '--'")

    for i, path in enumerate(args.files):
        if path == "-":
            texts.append(sys.stdin.read())
        else:
            progress(f"reading {i + 1}/{len(args.files)}: {path}")
            with open(path, encoding="utf-8", errors="replace") as fh:
                texts.append(fh.read())
    if args.files and args.files != ["-"]:
        progress(f"read {len(args.files)} file(s)", done=True)

    if not texts:
        parser.error("provide log file(s), '-' for stdin, or '-n N -- <command>'")

    progress("averaging ...")
    modules, n_runs, reference_index, runs = collect(texts)
    progress(f"averaged {len(modules)} modules across {n_runs} run(s)", done=True)
    modules = order_modules(modules, runs, reference_index, args.sort)
    report = format_report(modules, n_runs, args.sort, args.annotate)
    print(report)

    if args.stats:
        # Sum of self time is the real cost of the import graph (cumulative
        # double-counts children). Average it across runs by summing per run.
        per_run_totals = [sum(v[0] for v in run.values()) for run in runs]
        print(
            f"\n# runs: {n_runs} | modules: {len(modules)} | "
            f"mean total self time: {statistics.fmean(per_run_totals):.0f} us "
            f"(min {min(per_run_totals)} / max {max(per_run_totals)})",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
