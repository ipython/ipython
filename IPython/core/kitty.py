# Implements https://sw.kovidgoyal.net/kitty/graphics-protocol/

from base64 import b64encode, b64decode
from collections.abc import Iterator
import os
import sys
import warnings

#: Set ``IPYTHON_KITTY_GRAPHICS`` to ``1``/``true`` or ``0``/``false`` to state
#: outright whether the terminal speaks the kitty graphics protocol. Unset (or
#: empty) autodetects. Forcing it also skips the detection itself, which walks
#: the process tree and is the reason IPython imports psutil at startup.
_FORCE_ENVVAR = "IPYTHON_KITTY_GRAPHICS"


def _forced_kitty_graphics() -> bool | None:
    """Whether the user has stated support explicitly; None to autodetect."""
    value = os.environ.get(_FORCE_ENVVAR)
    if value is None or value == "":
        return None
    if value.lower() in {"1", "true"}:
        return True
    if value.lower() in {"0", "false"}:
        return False
    warnings.warn(
        f"Ignoring {_FORCE_ENVVAR}={value!r}: expected one of"
        " '0', '1', 'false', 'true' or '' (autodetect).",
        UserWarning,
        stacklevel=2,
    )
    return None


def _read_proc_stat(pid: int) -> bytes:
    """Return the raw contents of ``/proc/<pid>/stat``."""
    with open(f"/proc/{pid}/stat", "rb") as stat_file:
        return stat_file.read()


def _proc_ancestor_names() -> Iterator[str]:
    """Yield ancestor process names, nearest first, by reading ``/proc``.

    Stops early -- yielding nothing further -- if an ancestor's ``stat`` file
    cannot be read, which is what happens when ``/proc`` is mounted with
    ``hidepid`` and the ancestor belongs to another user. That is the same
    outcome as the `psutil.AccessDenied` the psutil walk below has to handle.

    The kernel truncates the name in ``stat`` to 15 characters, where psutil
    would fall back to ``cmdline`` to recover the full one. Every terminal
    this is matched against is well under that, so a truncated name can only
    ever fail to match -- and only for a process that was never a match.
    """
    pid = os.getppid()
    while pid > 0:
        try:
            stat = _read_proc_stat(pid)
        except OSError:
            return
        # `stat` is ``pid (comm) state ppid ...``, and `comm` may itself
        # contain spaces and parentheses, so the closing parenthesis to split
        # on is the *last* one.
        head, _, rest = stat.rpartition(b")")
        yield head.partition(b"(")[2].decode("utf-8", "replace")
        fields = rest.split()
        try:
            # The ppid, after the one-letter state; 0 once we reach pid 1.
            pid = int(fields[1])
        except (IndexError, ValueError):
            return


def _psutil_ancestor_names() -> Iterator[str]:
    """Yield ancestor process names, nearest first, using psutil."""
    import psutil

    try:
        process = psutil.Process()
        while process := process.parent():
            yield process.name()
    except (psutil.Error, OSError):
        # Walking the process tree can fail when /proc is mounted with
        # ``hidepid`` on shared multi-user systems (common on HPC clusters):
        # ancestor processes owned by other users are inaccessible and psutil
        # raises AccessDenied. Treat as "unsupported" rather than letting it
        # abort the import of IPython.
        return


def _ancestor_process_names() -> Iterator[str]:
    """Yield the names of this process' ancestors, nearest first.

    On Linux this reads ``/proc`` directly: importing psutil costs upwards of
    10ms, which is a real slice of IPython's startup, and this runs on every
    interactive start. ``/proc/<pid>/stat`` holds both the name psutil would
    report and the parent pid, so one read per ancestor is enough.

    Everywhere else -- macOS, or a Linux without ``/proc`` -- fall back to
    psutil, which IPython depends on anyway.
    """
    if sys.platform == "linux" and os.path.isdir("/proc/self"):
        yield from _proc_ancestor_names()
    else:
        yield from _psutil_ancestor_names()


def _supports_kitty_graphics() -> bool:
    forced = _forced_kitty_graphics()
    if forced is not None:
        return forced

    if sys.platform not in ("darwin", "linux"):
        return False

    isatty = getattr(sys.stdout, "isatty", None)
    if not callable(isatty) or not isatty():
        return False
    # Hardcoding process names instead of using
    # https://sw.kovidgoyal.net/kitty/graphics-protocol/#querying-support-and-available-transmission-mediums
    # to avoid startup slowdown
    supported_terminals = {
        "ghostty",
        "iTerm2",
        "kitty",
        "konsole",
        "warp",
        "wayst",
        "wezterm-gui",
        "yakuake",
    }
    return any(name in supported_terminals for name in _ancestor_process_names())


supports_kitty_graphics = _supports_kitty_graphics()


def png_to_kitty_ansi(png: bytes) -> str:
    if not png.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError
    # This simplicity resembles
    # https://sw.kovidgoyal.net/kitty/graphics-protocol/#a-minimal-example
    # but if we need tmux support, we can switch to Unicode like
    # https://github.com/hzeller/timg/blob/main/src/kitty-canvas.cc
    result = ["\033_Ga=T,f=100,", "m=1;"]
    encoded = b64encode(png)
    for i in range(0, len(encoded), 4096):
        result.append(encoded[i : i + 4096].decode("ascii"))
        result.append("\033\\")
        result.append("\033_G")
        result.append("m=1;")
    del result[-2:]
    result[-3] = "m=0;"
    return "".join(result)


def kitty_png_render(png: bytes | str, _md_dict: object) -> None:
    if isinstance(png, str):
        png = png_to_kitty_ansi(b64decode(png))
    else:
        png = png_to_kitty_ansi(png)
    print(png)


display_formatter_default_active_types = [
    "text/plain",
    *(["image/png"] if supports_kitty_graphics else []),
]

terminal_default_mime_renderers = {
    "image/png": kitty_png_render,
}
