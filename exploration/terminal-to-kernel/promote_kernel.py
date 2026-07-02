"""Proof-of-concept IPython extension: promote a live terminal session to a Jupyter kernel.

Usage, from a plain ``ipython`` terminal session::

    In [1]: %load_ext promote_kernel   # (this file on sys.path / in extensions dir)
    In [2]: %promote

    ... prints the connection file path and how to attach ...

After ``%promote`` the session keeps working normally at the terminal, and is
*also* reachable as a standard Jupyter kernel over ZMQ:

- ``jupyter console --existing kernel-<pid>.json`` works immediately;
- with ``%promote --external-dir DIR`` the connection file is written into
  DIR, so a server started with
  ``jupyter lab --ServerApp.allow_external_kernels=True --ServerApp.external_connection_dir=DIR``
  lists the session in its kernel picker and any notebook can attach to it
  (jupyter_client >= 8.3.1 / jupyter_server >= 2.7.3).

Architecture (see README.md in this directory): the kernel machinery runs in a
daemon background thread (sockets, heartbeat, iopub, control, shell dispatch);
the terminal REPL keeps the main thread. The kernel's ZMQInteractiveShell is a
*separate shell object* that shares user_ns/user_module with the terminal
shell, so state is common but execution is not serialized between the two
frontends — this is a PoC, not a finished design.

Known PoC limitations:
- terminal and notebook executions may interleave (no locking);
- ``input()`` requested by notebook code is answered by the notebook, not the tty;
- Ctrl-C at the terminal does not interrupt notebook-initiated execution;
- ``get_ipython()`` inside kernel executions returns the kernel's shell,
  not the terminal shell (they share a namespace, not identity);
- history written by notebook executions lands in a second history session.
"""

import os
import sys
import threading

_state = {"app": None, "thread": None, "error": None, "ready": threading.Event()}


def _start_kernel_thread(shell, connection_file):
    """Run IPKernelApp forever in this (background) thread, sharing *shell*'s state."""
    try:
        from ipykernel.kernelapp import IPKernelApp
        from IPython.core.interactiveshell import InteractiveShell
        from IPython.core.application import BaseIPythonApplication

        # Both the Application and the InteractiveShell singleton slots are
        # already claimed by the terminal session (TerminalIPythonApp /
        # TerminalInteractiveShell). ipykernel wants to register its own
        # siblings (IPKernelApp / ZMQInteractiveShell) and traitlets raises
        # MultipleInstanceError otherwise, so release the slots first. The
        # terminal keeps using its existing objects; this only affects who
        # answers ``.instance()`` from now on.
        BaseIPythonApplication.clear_instance()
        InteractiveShell.clear_instance()

        app = IPKernelApp.instance(
            connection_file=connection_file,
            # OutStream replaces sys.stdout/stderr so notebook clients see
            # streams on iopub; quiet=False makes it echo to the real tty so
            # the terminal user still sees everything.
            quiet=False,
            # Leave OS-level fds 1/2 alone -- fd capture would also swallow
            # prompt_toolkit's rendering.
            capture_fd_output=False,
        )
        # init_signal() fails harmlessly off the main thread (it logs an
        # error and continues); everything else in initialize() is
        # thread-agnostic in ipykernel 7.
        app.initialize([])

        # Adopt the terminal session's state. Setting kernel.user_ns
        # triggers IPythonKernel._user_ns_changed which re-points the ZMQ
        # shell's namespace and re-runs init_user_ns.
        app.kernel.user_module = shell.user_module
        app.kernel.user_ns = shell.user_ns
        app.kernel.shell.execution_count = shell.execution_count

        # Creating the ZMQ shell made it the InteractiveShell singleton, so
        # the module-level get_ipython() now returns it -- which breaks the
        # terminal frontend: prompt_toolkit key-binding filters look up
        # terminal-only traits through get_ipython() on every keypress
        # (IPython/terminal/shortcuts/filters.py, e.g. shell.auto_match) and
        # raise AttributeError on ZMQInteractiveShell. Point the singleton
        # back at the terminal shell. Trade-off: IPython.display.display()
        # from notebook clients resolves the terminal display publisher and
        # won't reach the notebook (execute_result display still works --
        # the displayhook is per-shell, installed around each run_cell). A
        # real implementation would graft the ZMQ publishers onto the one
        # shell object instead of having two shells.
        InteractiveShell._instance = shell

        # init_io() installed iopub OutStreams as sys.stdout/stderr, but the
        # terminal REPL wraps every prompt in prompt_toolkit's
        # patch_stdout(raw=True) (IPython/terminal/interactiveshell.py:949),
        # which restores the pre-prompt stdout when the prompt exits -- so
        # the OutStreams get evicted one prompt after promotion and
        # notebook-side print() would silently stop reaching iopub. Instead
        # of owning sys.stdout globally, swap the ZMQ streams in only for
        # the duration of each kernel-side execution.
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
    """%promote [--external-dir DIR] -- expose this session as a Jupyter kernel."""
    from IPython.core.getipython import get_ipython

    shell = get_ipython()

    if _state["app"] is not None:
        print("Session already promoted; connection file:")
        print("    " + _state["app"].abs_connection_file)
        return

    external_dir = None
    args = line.split()
    if "--external-dir" in args:
        external_dir = args[args.index("--external-dir") + 1]
        os.makedirs(external_dir, exist_ok=True)

    if external_dir:
        connection_file = os.path.join(
            os.path.abspath(external_dir), "kernel-%i.json" % os.getpid()
        )
    else:
        connection_file = ""  # IPKernelApp default: runtime-dir/kernel-<pid>.json

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

    app = _state["app"]
    cf = app.abs_connection_file
    print("This terminal session is now also a Jupyter kernel.")
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


def load_ipython_extension(ip):
    ip.register_magic_function(promote, magic_kind="line", magic_name="promote")
