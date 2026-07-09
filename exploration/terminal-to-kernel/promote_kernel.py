"""Proof-of-concept IPython extension: promote a live terminal session to a Jupyter kernel.

Usage, from a plain ``ipython`` terminal session::

    In [1]: %load_ext promote_kernel   # (this file on sys.path / in extensions dir)
    In [2]: %promote

    ... prints the connection file path and how to attach; the terminal
    stops being interactive and the process becomes a standard kernel ...

Two modes:

``%promote`` (default) — **hand-off**: the prompt_toolkit REPL is finished for
good, the live namespace/state is handed over to ipykernel, and the kernel
event loop runs on the **main thread**. This is the semantically-correct
"move my session to a kernel": signal-based interrupt works
(``interrupt_request`` → SIGINT → ``default_int_handler`` around handlers,
ipykernel/kernelbase.py), GUI event loops and main-thread-only libraries
work, ``get_ipython()`` globally resolves to the kernel shell, and
``IPython.display.display()`` publishes real display_data. The old tty keeps
mirroring output via ``OutStream(echo=sys.__stdout__)`` (``quiet=False``).
The hand-off blocks inside the magic (embed_kernel-style) rather than
returning through ``TerminalInteractiveShell.mainloop()``, because that path
runs ``_atexit_once()`` which resets the (now shared) user_ns and closes
history (IPython/terminal/interactiveshell.py:1045,
IPython/core/interactiveshell.py:4091-4101).

``%promote --share`` — **experimental dual-frontend**: the kernel machinery
runs in a daemon background thread and the terminal REPL stays interactive;
both frontends share user_ns/user_module. Execution of notebook-initiated
code happens off the main thread (signal-based interrupt and some libraries
degrade), and the two frontends are not serialized. Singleton handling in
this mode:

- with the ``SingletonScope`` traitlets extension
  (https://github.com/Carreau/traitlets/tree/multiton) the kernel thread
  activates a scoped singleton registry: IPKernelApp/ZMQInteractiveShell are
  created inside the scope, the process-global singletons are never touched,
  and ``get_ipython()``/``InteractiveShell.instance()`` resolve per-thread —
  terminal shell on the main thread (keybinding filters keep working), ZMQ
  shell on the kernel thread (rich ``display()`` reaches the notebook);
- with stock traitlets, fall back to clearing the singleton slots and
  re-pointing ``InteractiveShell._instance`` at the terminal shell (without
  this, prompt_toolkit key-binding filters that read terminal-only traits
  through get_ipython() on every keypress —
  IPython/terminal/shortcuts/filters.py — crash the prompt loop). Trade-off:
  ``display()`` from notebook clients does not reach the notebook.

Attach paths after promotion (either mode):

- ``jupyter console --existing kernel-<pid>.json`` works immediately;
- with ``%promote --external-dir DIR`` the connection file is written into
  DIR, so ``jupyter lab --ServerApp.allow_external_kernels=True
  --ServerApp.external_connection_dir=DIR`` lists the session in its kernel
  picker (jupyter_client >= 8.3.1 / jupyter_server >= 2.7.3).
"""

import contextlib
import os
import sys
import threading

try:
    from traitlets.config import SingletonScope  # noqa: F401  (multiton branch)

    _HAS_SCOPE = True
except ImportError:
    _HAS_SCOPE = False

_state = {"app": None, "thread": None, "error": None, "ready": threading.Event()}


def _make_kernel_app(shell, connection_file):
    """Create + initialize IPKernelApp and adopt *shell*'s session state.

    Must run with the singleton slots resolved by the caller (cleared
    globals for hand-off, or inside a SingletonScope for --share).
    """
    from ipykernel.kernelapp import IPKernelApp

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
    return app


def _print_connect_info(app, external_dir, extra=""):
    cf = app.abs_connection_file
    print("This terminal session is now a Jupyter kernel%s." % extra)
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


def _handoff(shell, connection_file, external_dir):
    """Finish the terminal session; the main thread becomes the kernel loop.

    Blocks forever (this is the point): we are inside run_cell inside
    interact(), and deliberately never return -- returning through
    mainloop() would run _atexit_once(), which resets the user_ns we just
    handed to the kernel. On kernel shutdown_request the process exits.
    """
    from IPython.core.interactiveshell import InteractiveShell
    from IPython.core.application import BaseIPythonApplication

    # The terminal session is over: hand the singleton slots to the kernel
    # so get_ipython()/InteractiveShell.instance() resolve to the kernel
    # shell everywhere from now on. (No scope needed here even with the
    # multiton branch -- a global hand-over is the semantically-correct
    # global state.)
    BaseIPythonApplication.clear_instance()
    InteractiveShell.clear_instance()

    app = _make_kernel_app(shell, connection_file)
    _state["app"] = app

    # If the kernel loop ever stops (shutdown_request), fall out through
    # interact()/mainloop() cleanly instead of prompting again.
    shell.keep_running = False

    _print_connect_info(
        app, external_dir, extra="; this prompt is no longer interactive"
    )
    # sys.stdout is now the iopub OutStream (echo=tty). init_signal() ran on
    # the main thread, so SIGINT handling is the standard kernel setup and
    # interrupt_request -> SIGINT -> KeyboardInterrupt works. User code
    # initiated by notebook clients executes on this (main) thread.
    app.start()


def _start_kernel_thread(shell, connection_file):
    """--share mode: run IPKernelApp forever in this background thread."""
    try:
        from IPython.core.interactiveshell import InteractiveShell
        from IPython.core.application import BaseIPythonApplication
        from traitlets.config.configurable import SingletonConfigurable

        if _HAS_SCOPE:
            # Give this thread its own singleton registry. IPKernelApp and
            # ZMQInteractiveShell are created inside the scope; the global
            # TerminalIPythonApp / TerminalInteractiveShell singletons are
            # never read or mutated, so .instance() keeps resolving to the
            # terminal objects on the main thread and to the kernel objects
            # on this thread (contextvars propagate into the io_loop
            # callbacks registered here).
            singleton_ctx = SingletonConfigurable.scope()()
        else:
            # Stock traitlets: both the Application and the InteractiveShell
            # singleton slots are already claimed by the terminal session,
            # and ipykernel registering its siblings raises
            # MultipleInstanceError -- release the slots first.
            BaseIPythonApplication.clear_instance()
            InteractiveShell.clear_instance()
            singleton_ctx = contextlib.nullcontext()

        with singleton_ctx:
            app = _make_kernel_app(shell, connection_file)

            if not _HAS_SCOPE:
                # Creating the ZMQ shell made it the InteractiveShell
                # singleton, so the module-level get_ipython() now returns
                # it -- which breaks the terminal frontend: prompt_toolkit
                # key-binding filters look up terminal-only traits through
                # get_ipython() on every keypress
                # (IPython/terminal/shortcuts/filters.py, e.g.
                # shell.auto_match) and raise AttributeError on
                # ZMQInteractiveShell. Point the singleton back at the
                # terminal shell. Trade-off: IPython.display.display() from
                # notebook clients resolves the terminal display publisher
                # and won't reach the notebook (execute_result display
                # still works -- the displayhook is per-shell, installed
                # around each run_cell).
                InteractiveShell._instance = shell

            # init_io() installed iopub OutStreams as sys.stdout/stderr, but
            # the terminal REPL wraps every prompt in prompt_toolkit's
            # patch_stdout(raw=True)
            # (IPython/terminal/interactiveshell.py:949), which restores the
            # pre-prompt stdout when the prompt exits -- so the OutStreams
            # get evicted one prompt after promotion and notebook-side
            # print() would silently stop reaching iopub. Instead of owning
            # sys.stdout globally, swap the ZMQ streams in only for the
            # duration of each kernel-side execution.
            zmq_stdout, zmq_stderr = sys.stdout, sys.stderr
            saved = []

            def _pre_execute():
                saved.append((sys.stdout, sys.stderr))
                sys.stdout, sys.stderr = zmq_stdout, zmq_stderr

            def _post_execute():
                if saved:
                    sys.stdout, sys.stderr = saved.pop()

            app.kernel.shell.events.register("pre_execute", _pre_execute)
            app.kernel.shell.events.register("post_execute", _post_execute)

            _state["app"] = app
            _state["ready"].set()
            app.start()  # blocks this thread forever servicing the kernel
    except BaseException:
        import traceback

        _state["error"] = traceback.format_exc()
        _state["ready"].set()


def promote(line=""):
    """%promote [--share] [--external-dir DIR] -- turn this session into a Jupyter kernel.

    Default: hand-off -- the terminal stops being interactive, the process
    becomes a kernel executing on the main thread. With --share, the kernel
    runs in a background thread and the terminal stays interactive
    (experimental; see module docstring for caveats).
    """
    from IPython.core.getipython import get_ipython

    shell = get_ipython()

    if _state["app"] is not None:
        print("Session already promoted; connection file:")
        print("    " + _state["app"].abs_connection_file)
        return

    args = line.split()
    share = "--share" in args
    external_dir = None
    if "--external-dir" in args:
        external_dir = os.path.abspath(args[args.index("--external-dir") + 1])
        os.makedirs(external_dir, exist_ok=True)

    if external_dir:
        connection_file = os.path.join(external_dir, "kernel-%i.json" % os.getpid())
    else:
        connection_file = ""  # IPKernelApp default: runtime-dir/kernel-<pid>.json

    if not share:
        _handoff(shell, connection_file, external_dir)  # blocks; never returns
        return

    t = threading.Thread(
        target=_start_kernel_thread,
        args=(shell, connection_file),
        name="jupyter-kernel",
        daemon=True,
    )
    _state["thread"] = t
    t.start()
    _state["ready"].wait(timeout=30)

    if _state["error"]:
        print("Promotion failed:", file=sys.stderr)
        print(_state["error"], file=sys.stderr)
        return

    mode = (
        "scoped singletons (traitlets multiton)"
        if _HAS_SCOPE
        else "singleton swap (stock traitlets)"
    )
    _print_connect_info(
        _state["app"], external_dir, extra=" [shared mode: %s]" % mode
    )


def load_ipython_extension(ip):
    ip.register_magic_function(promote, magic_kind="line", magic_name="promote")
