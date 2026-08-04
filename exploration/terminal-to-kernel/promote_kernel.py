"""Proof-of-concept IPython extension: promote a live terminal session to a Jupyter kernel.

IPython-only implementation: requires traitlets >= 5.17 (``SingletonScope``,
on traitlets ``main`` as of 2026-08) and an installed ipykernel, but **no
patches to ipykernel** — all singleton collisions are avoided by activating a
scoped singleton registry, so the kernel machinery instantiates its own
``IPKernelApp``/``ZMQInteractiveShell`` inside the scope while the terminal's
``TerminalIPythonApp``/``TerminalInteractiveShell`` singletons are never read,
created over, or mutated. On older traitlets, ``%promote`` prints that a newer
traitlets is required and does nothing.

Usage, from a plain ``ipython`` terminal session::

    In [1]: %load_ext promote_kernel   # (this file on sys.path / in extensions dir)
    In [2]: %promote

    ... prints the connection file path and how to attach; the terminal
    stops being interactive and the process becomes a standard kernel ...

``%promote`` is a **hand-off**: the prompt_toolkit REPL is finished for good,
the live namespace/state is handed over to ipykernel, and the kernel event
loop runs on the **main thread**. This is the semantically-correct "move my
session to a kernel": signal-based interrupt works (``interrupt_request`` →
SIGINT → ``default_int_handler`` around handlers, ipykernel/kernelbase.py),
GUI event loops and main-thread-only libraries work, and streams /
``execute_result`` / ``display_data`` all reach iopub. The scope is entered on
the main thread and deliberately never exited: the rest of the process's
main-thread work *is* the kernel loop, so in-scope resolution (e.g.
``InteractiveShell.instance()`` inside ``IPython.display.display``,
IPython/core/display_functions.py:64) yields the kernel's ZMQ shell, while the
untouched terminal singletons simply become unreachable. The old tty keeps
mirroring output via ``OutStream(echo=sys.__stdout__)`` (``quiet=False``); to
get an interactive prompt back on the same session, run
``jupyter console --existing <connection-file>``.

The hand-off blocks inside the magic (embed_kernel-style) rather than
returning through ``TerminalInteractiveShell.mainloop()``, because that path
runs ``_atexit_once()`` which resets the (now shared) user_ns and closes
history (IPython/terminal/interactiveshell.py:1050,
IPython/core/interactiveshell.py:4173-4183).

A background-thread "dual frontend" variant (kernel in a daemon thread, the
terminal staying interactive) was prototyped and **rejected**: notebook code
would execute off the main thread — breaking GUI/matplotlib backends and other
main-thread-only libraries, and inverting interrupt delivery
(``interrupt_request`` SIGINTs the main thread, i.e. the terminal, while the
busy kernel thread is uninterruptible) — and the two unserialized executors
race on shared shell state. See README.md for the analysis.

Attach paths after promotion:

- ``jupyter console --existing kernel-<pid>.json`` works immediately;
- with ``%promote --external-dir DIR`` the connection file is written into
  DIR, so ``jupyter lab --ServerApp.allow_external_kernels=True
  --ServerApp.external_connection_dir=DIR`` lists the session in its kernel
  picker (jupyter_client >= 8.3.1 / jupyter_server >= 2.7.3).
"""

import os
import sys

try:
    from traitlets.config import SingletonScope  # noqa: F401  (traitlets >= 5.17)

    _HAS_SCOPE = True
except ImportError:
    _HAS_SCOPE = False

_state = {"app": None}


def _handoff(shell, connection_file, external_dir):
    """Finish the terminal session; the main thread becomes the kernel loop.

    Blocks forever (this is the point): we are inside run_cell inside
    interact(), and deliberately never return -- returning through
    mainloop() would run _atexit_once(), which resets the user_ns we just
    handed to the kernel. On kernel shutdown_request the process exits.
    """
    from ipykernel.kernelapp import IPKernelApp
    from traitlets.config.configurable import SingletonConfigurable

    # Enter a process-wide-for-all-practical-purposes scope: it is activated
    # on the main thread and never exited, so kernel construction here and
    # every later main-thread resolution (the kernel loop, executions, and
    # io_loop callbacks, which inherit this context) happen in the scoped
    # registry. The terminal's TerminalIPythonApp/TerminalInteractiveShell
    # globals are never touched.
    scope = SingletonConfigurable.scope()
    scope_cm = scope()
    scope_cm.__enter__()
    _state["scope"] = scope

    app = IPKernelApp.instance(
        connection_file=connection_file,
        # OutStream replaces sys.stdout/stderr so notebook clients see
        # streams on iopub; quiet=False makes it echo to the real tty so
        # the terminal user still sees everything.
        quiet=False,
        # Leave OS-level fds 1/2 alone -- fd capture would also swallow
        # prompt_toolkit's rendering (and the tty echo).
        capture_fd_output=False,
    )
    app.initialize([])

    # Adopt the terminal session's state. Setting kernel.user_ns triggers
    # IPythonKernel._user_ns_changed which re-points the ZMQ shell's
    # namespace and re-runs init_user_ns.
    app.kernel.user_module = shell.user_module
    app.kernel.user_ns = shell.user_ns
    app.kernel.shell.execution_count = shell.execution_count
    _state["app"] = app

    # If the kernel loop ever stops (shutdown_request), fall out through
    # interact()/mainloop() cleanly instead of prompting again.
    shell.keep_running = False

    cf = app.abs_connection_file
    print("This terminal session is now a Jupyter kernel; this prompt is no longer interactive.")
    print("Connection file: %s" % cf)
    print()
    print("Attach a console:   jupyter console --existing %s" % cf)
    if external_dir:
        print(
            "Attach a notebook:  jupyter lab"
            " --ServerApp.allow_external_kernels=True"
            " --ServerApp.external_connection_dir=%s" % external_dir
        )
        print("                    then pick this kernel in the kernel selector.")

    # sys.stdout is now the iopub OutStream (echo=tty). init_signal() ran on
    # the main thread, so SIGINT handling is the standard kernel setup and
    # interrupt_request -> SIGINT -> KeyboardInterrupt works. User code
    # initiated by notebook clients executes on this (main) thread.
    app.start()


def promote(line=""):
    """%promote [--external-dir DIR] -- turn this session into a Jupyter kernel.

    Hand-off: the terminal stops being interactive, the process becomes a
    kernel executing on the main thread. Reattach interactively with
    ``jupyter console --existing``.

    Requires traitlets >= 5.17 (SingletonScope).
    """
    from IPython.core.getipython import get_ipython

    if not _HAS_SCOPE:
        import traitlets

        print(
            "%%promote requires traitlets >= 5.17 (SingletonScope); "
            "you have %s." % traitlets.__version__,
            file=sys.stderr,
        )
        print(
            "Until 5.17 is released:  pip install git+https://github.com/ipython/traitlets",
            file=sys.stderr,
        )
        return

    shell = get_ipython()

    if _state["app"] is not None:
        print("Session already promoted; connection file:")
        print("    " + _state["app"].abs_connection_file)
        return

    args = line.split()
    external_dir = None
    if "--external-dir" in args:
        external_dir = os.path.abspath(args[args.index("--external-dir") + 1])
        os.makedirs(external_dir, exist_ok=True)

    if external_dir:
        connection_file = os.path.join(external_dir, "kernel-%i.json" % os.getpid())
    else:
        connection_file = ""  # IPKernelApp default: runtime-dir/kernel-<pid>.json

    _handoff(shell, connection_file, external_dir)  # blocks; never returns


def load_ipython_extension(ip):
    ip.register_magic_function(promote, magic_kind="line", magic_name="promote")
