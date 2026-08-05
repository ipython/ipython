#!/usr/bin/env python3
"""Measure the memory footprint of importing and starting IPython.

``tools/importtime_average.py`` answers "what is slow to import?". This script
answers the companion question, "what is *expensive to keep around*?" -- which
is not the same thing. A module can be slow to import but cheap in memory (a
regex-heavy module that compiles once and keeps little), or fast to import but
expensive (a table module that unmarshals a few MB of constants in one go). A
cache built during ``InteractiveShell`` construction costs memory without
showing up in ``-X importtime`` at all.

Every measurement runs in a **fresh subprocess**, because imports are sticky:
once ``prompt_toolkit`` is in ``sys.modules``, asking what ``wcwidth`` costs
gives you nothing. Isolation is the whole point, so the numbers below are
*independent* costs and generally overlap each other -- ``jupyter_client`` and
``IPython`` both pay for ``traitlets``, and summing the rows will overcount.

Two metrics are reported per scenario:

``rss``
    Peak resident set size (``resource.getrusage``), minus the same measurement
    for a bare interpreter. This is what the operating system actually charges
    you, including the unmarshalled ``.pyc`` code objects that dominate startup.
``modules``
    Number of entries added to ``sys.modules``. A good proxy for import-graph
    breadth, and much less noisy than RSS.

Usage
-----
Measure the standard scenarios (baseline, ``import IPython``, terminal shell,
kernel shell) and the usual heavy dependencies::

    python tools/memory_snapshot.py

Measure specific modules, isolated from each other::

    python tools/memory_snapshot.py -m prompt_toolkit -m jupyter_client

Measure an arbitrary statement, repeated for stability::

    python tools/memory_snapshot.py -n 5 -c "import IPython.core.completer"

Attribute allocations to source lines with ``tracemalloc`` instead of RSS
(slower, and it perturbs the very thing it measures -- but it tells you *which
line* allocated, which RSS cannot)::

    python tools/memory_snapshot.py --tracemalloc -c "import IPython"

Note that ``--tracemalloc`` inflates RSS substantially (it stores a traceback
per allocation), so never compare its ``rss`` column against a plain run.
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import textwrap

# Scenarios measured by default. Each is (label, statement); the statement is
# executed in a fresh interpreter and must be importable from a checkout.
DEFAULT_SCENARIOS: list[tuple[str, str]] = [
    ("import IPython", "import IPython"),
    (
        "terminal shell",
        "from IPython.terminal.interactiveshell import TerminalInteractiveShell;"
        " TerminalInteractiveShell.instance().run_cell('pass')",
    ),
    (
        "kernel shell",
        "from ipykernel.zmqshell import ZMQInteractiveShell;"
        " ZMQInteractiveShell.instance()",
    ),
]

# Third-party dependencies worth tracking individually. These are measured in
# isolation, so the costs overlap (most of them pull in traitlets).
DEFAULT_MODULES: list[str] = [
    "prompt_toolkit",
    "jupyter_client",
    "jedi",
    "wcwidth",
    "traitlets",
    "pygments",
    "zmq",
    "tornado",
    "asyncio",
]

# Child program. Prints one JSON object on stdout so the parent never has to
# parse human-oriented text. Kept as a template rather than a file so the tool
# stays a single self-contained script.
_CHILD = """
import json, resource, sys, tracemalloc

TRACE = {trace!r}
if TRACE:
    tracemalloc.start(10)

before_modules = len(sys.modules)
before_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

{statement}

after_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
after_modules = len(sys.modules)

result = {{
    "rss_delta": after_rss - before_rss,
    "rss_total": after_rss,
    "modules_delta": after_modules - before_modules,
    "modules_total": after_modules,
}}

if TRACE:
    stats = tracemalloc.take_snapshot().statistics("lineno")
    result["traced"] = tracemalloc.get_traced_memory()[1]
    result["top"] = [
        {{"size": s.size, "count": s.count, "where": str(s.traceback[0])}}
        for s in stats[:{top}]
    ]

sys.stdout.write(json.dumps(result))
"""


def rss_scale() -> tuple[float, str]:
    """Return (divisor to MiB, note) for ``ru_maxrss`` on this platform.

    ``ru_maxrss`` is kilobytes on Linux but *bytes* on macOS -- a factor of 1024
    that silently makes every number wrong if ignored.
    """
    if sys.platform == "darwin":
        return 1024 * 1024, "bytes"
    return 1024, "KiB"


def measure(
    statement: str, *, repeat: int, trace: bool, top: int, timeout: float
) -> dict | None:
    """Run ``statement`` in ``repeat`` fresh interpreters; return merged results.

    Returns ``None`` if the statement fails (typically an optional dependency
    that is not installed), so callers can skip it rather than abort the run.
    """
    program = _CHILD.format(
        statement=textwrap.dedent(statement).strip(), trace=trace, top=top
    )
    samples: list[dict] = []
    for _ in range(repeat):
        proc = subprocess.run(
            [sys.executable, "-c", program],
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
        if proc.returncode != 0:
            return None
        try:
            samples.append(json.loads(proc.stdout))
        except json.JSONDecodeError:
            # The statement printed to stdout and corrupted our channel.
            return None

    if not samples:
        return None

    # Median rather than mean: RSS occasionally spikes from unrelated system
    # activity, and a single outlier should not move the reported number.
    merged = {
        key: statistics.median(s[key] for s in samples)
        for key in ("rss_delta", "rss_total", "modules_delta", "modules_total")
    }
    merged["samples"] = len(samples)
    if trace:
        # Traceback attribution is deterministic enough that the first run is
        # representative; averaging per-line stats across runs is not meaningful.
        merged["traced"] = samples[0].get("traced", 0)
        merged["top"] = samples[0].get("top", [])
    return merged


def format_row(label: str, result: dict | None, divisor: float, baseline: float) -> str:
    if result is None:
        return f"  {label:<32} {'unavailable':>12}"
    mib = (result["rss_delta"] - baseline) / divisor
    return f"  {label:<32} {mib:>9.1f} MiB  {int(result['modules_delta']):>5d} modules"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Measure IPython's startup memory footprint.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "-c",
        "--statement",
        action="append",
        default=[],
        metavar="STMT",
        help="measure an arbitrary statement (repeatable). Replaces the "
        "default scenarios.",
    )
    parser.add_argument(
        "-m",
        "--module",
        action="append",
        default=[],
        metavar="MOD",
        help="measure 'import MOD' in isolation (repeatable). Replaces the "
        "default dependency list.",
    )
    parser.add_argument(
        "-n",
        "--repeat",
        type=int,
        default=3,
        metavar="N",
        help="run each measurement N times and report the median (default 3).",
    )
    parser.add_argument(
        "--tracemalloc",
        action="store_true",
        help="attribute allocations to source lines instead of only reporting "
        "RSS. Inflates RSS; do not compare against a plain run.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=15,
        metavar="N",
        help="with --tracemalloc, show the N largest allocation sites (default 15).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=120.0,
        metavar="SECONDS",
        help="per-subprocess timeout (default 120).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit raw JSON instead of a human-readable table.",
    )
    args = parser.parse_args(argv)

    if args.repeat < 1:
        parser.error("--repeat must be >= 1")

    divisor, unit = rss_scale()

    scenarios: list[tuple[str, str]] = []
    if args.statement:
        scenarios.extend((stmt, stmt) for stmt in args.statement)
    if args.module:
        scenarios.extend((mod, f"import {mod}") for mod in args.module)
    if not scenarios:
        scenarios = list(DEFAULT_SCENARIOS)
        scenarios.extend((mod, f"import {mod}") for mod in DEFAULT_MODULES)

    def run(statement: str) -> dict | None:
        return measure(
            statement,
            repeat=args.repeat,
            trace=args.tracemalloc,
            top=args.top,
            timeout=args.timeout,
        )

    # A bare interpreter still charges for site.py and friends; subtracting it
    # keeps the reported numbers attributable to the thing being measured.
    print("measuring baseline ...", file=sys.stderr, flush=True)
    baseline_result = run("pass")
    baseline = baseline_result["rss_delta"] if baseline_result else 0.0

    results: dict[str, dict | None] = {}
    for label, statement in scenarios:
        print(f"measuring {label} ...", file=sys.stderr, flush=True)
        results[label] = run(statement)

    if args.json:
        payload = {
            "unit": unit,
            "repeat": args.repeat,
            "baseline_rss": baseline,
            "results": results,
        }
        print(json.dumps(payload, indent=2))
        return 0

    interpreter = (
        (baseline_result["rss_total"] / divisor) if baseline_result else float("nan")
    )
    print(f"\nbare interpreter: {interpreter:.1f} MiB (subtracted below)")
    print(f"median of {args.repeat} run(s), each in a fresh subprocess\n")
    for label, result in results.items():
        print(format_row(label, result, divisor, baseline))

    if args.tracemalloc:
        for label, result in results.items():
            if not result or not result.get("top"):
                continue
            print(f"\n  === {label}: largest allocation sites ===")
            for entry in result["top"]:
                print(
                    f"  {entry['size'] / 1024:>9.1f} KiB "
                    f"{entry['count']:>7d} objs  {entry['where']}"
                )

    print(
        "\nnote: measurements are independent, so they overlap and must not be summed.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
