# Promoting a live terminal IPython session to a Jupyter kernel

**Goal.** From a plain `ipython` terminal session, mid-session: turn the process into a
standard Jupyter kernel — keeping `user_ns`, `user_module`, execution count — with a
normal connection file (ip, shell/iopub/stdin/control/hb ports, key, transport,
signature scheme), so consoles and notebooks can attach to it.

**Status: working, IPython-side only.** The proof of concept in this directory
([`promote_kernel.py`](promote_kernel.py)) needs **no changes to ipykernel,
jupyter_client, or jupyter_server** — only an importable ipykernel and
**traitlets ≥ 5.17** (`SingletonScope`, on traitlets `main` as of 2026-08; on older
traitlets `%promote` prints the requirement and does nothing). Everything is exercised
end-to-end by [`test_promote_e2e.py`](test_promote_e2e.py), which drives a real
`ipython` under pexpect and attaches a `jupyter_client` as a stand-in notebook.

```
In [1]: %load_ext promote_kernel
In [2]: %promote --external-dir /tmp/ext-kernels
This terminal session is now a Jupyter kernel; this prompt is no longer interactive.
Connection file: /tmp/ext-kernels/kernel-12345.json

Attach a console:   jupyter console --existing /tmp/ext-kernels/kernel-12345.json
Attach a notebook:  jupyter lab --ServerApp.allow_external_kernels=True --ServerApp.external_connection_dir=/tmp/ext-kernels
```

## How hand-off works (default `%promote`)

The terminal REPL is finished for good and the **main thread becomes the kernel's
event loop** — main-thread execution is the design requirement: signal-based
interrupt and many libraries need it.

1. **A `SingletonScope` is entered on the main thread and never exited.** All kernel
   construction (`IPKernelApp.instance()`, its `ZMQInteractiveShell`) and every later
   main-thread resolution — the kernel loop, executions, io_loop callbacks (which
   inherit the contextvar) — happen in the scoped registry. The terminal's
   `TerminalIPythonApp`/`TerminalInteractiveShell` singletons are never read, created
   over, or mutated; without the scope, both instantiations raise
   `MultipleInstanceError` (verified), which previously forced `clear_instance()`
   surgery or ipykernel patches. In-scope resolution also routes
   `IPython.display.display()` (`InteractiveShell.instance()`,
   `core/display_functions.py:64`) to the ZMQ display publisher, so rich display
   reaches the notebook.
2. **`IPKernelApp` is initialized normally** (`quiet=False`, `capture_fd_output=False`):
   sockets, heartbeat, connection file, IO. `quiet=False` makes the iopub `OutStream`
   echo to `sys.__stdout__`, so the old tty keeps mirroring kernel output.
3. **Session state is adopted**: `kernel.user_module`, then `kernel.user_ns` (the
   trait observer re-runs `init_user_ns` on the kernel shell), then
   `shell.execution_count`. Namespace identity is shared, not copied.
4. **The magic blocks in `app.start()` and never returns.** Returning through
   `TerminalInteractiveShell.mainloop()` would run `_atexit_once()`
   (`terminal/interactiveshell.py:1050` → `core/interactiveshell.py:4173-4183`), which
   calls `shell.reset()` — wiping the *shared* `user_ns` just handed over.
   `shell.keep_running` is set to `False`, so if the kernel loop stops
   (`shutdown_request`) the process falls out through `interact()` and exits cleanly —
   at which point `_atexit_once()` is the correct teardown.

Because the kernel owns the main thread, `interrupt_request` on the control channel →
`os.kill(pid, SIGINT)` (`ipykernel/kernelbase.py:1040-1074`) with
`default_int_handler` installed around handlers (`kernelbase.py:496-503`) →
`KeyboardInterrupt` lands in busy user code. `input()` from notebook-initiated code is
answered over the stdin channel by the notebook, not the tty.

## `%promote --share` (experimental dual-frontend)

The kernel machinery runs in a daemon background thread instead, and the terminal
stays interactive; both frontends share `user_ns`. The scope is activated *inside* the
kernel thread (the pattern the `SingletonScope` docs recommend; correct on both GIL
and free-threaded builds), so `get_ipython()` resolves per-thread — terminal shell on
the main thread (the prompt_toolkit key-binding filters that read terminal-only traits
through `get_ipython()` on every keypress, `terminal/shortcuts/filters.py:84`, keep
working), ZMQ shell on the kernel thread (rich `display()` reaches the notebook).

Two share-mode-specific mitigations/caveats, both inherent to keeping the REPL alive:

- every prompt is wrapped in prompt_toolkit's `patch_stdout(raw=True)`
  (`terminal/interactiveshell.py:954`), which restores the pre-prompt `sys.stdout` on
  exit and would silently evict the kernel's iopub `OutStream` one prompt after
  promotion — so the ZMQ streams are swapped in only around each kernel-side
  execution via the kernel shell's `pre_execute`/`post_execute` events;
- notebook-initiated code executes **off** the main thread (signal-based interrupt and
  main-thread-only libraries degrade), and the two frontends' executions are not
  serialized (races on `execution_count`, history, display state are possible).

## Connection info and attaching

All plumbing is stock:

- `IPKernelApp` writes the standard connection file (`kernel-<pid>.json`, all 9 fields
  plus `kernel_name`) via `jupyter_client.connect.write_connection_file`.
- `jupyter console --existing <file>` / qtconsole attach with nothing else.
- Notebooks: jupyter_server ≥ 2.7.3 with
  `--ServerApp.allow_external_kernels=True --ServerApp.external_connection_dir=DIR`
  auto-discovers connection files in DIR (jupyter_client ≥ 8.3.1,
  `MultiKernelManager.external_connection_dir`, `KernelManager(owns_kernel=False)`);
  the promoted session appears in JupyterLab's kernel picker. UI "shutdown" of an
  external kernel is a detach no-op; restart/interrupt buttons raise by design
  (interrupt still works over the control channel, as the e2e test shows).
  `%promote --external-dir DIR` writes the connection file straight into such a
  directory. Spyder can also attach by connection file; VS Code cannot
  (microsoft/vscode-jupyter#13849).

Security note: the connection file's HMAC key is full execute rights for any same-user
process that can read it; the external-connection dir should be treated accordingly.

## Verified end-to-end (`test_promote_e2e.py`)

Hand-off: client sees the terminal namespace; executions run on **`MainThread`**;
`signal.signal(...)` works from client code; `print()` → iopub `stream`;
`display()` → iopub `display_data`; `interrupt_request` turns `time.sleep(120)` into a
`KeyboardInterrupt` error reply; `shutdown_request` exits the process cleanly.

Share: terminal stays interactive; bidirectional namespace visibility; streams,
`execute_result`, and `display_data` on iopub.

Refusal: on traitlets < 5.17, `%promote` prints the requirement (and an install hint)
and the session continues unharmed.

## What a real IPython implementation would add

The PoC is an extension; productizing it in IPython means:

- a real exit path instead of blocking inside the magic: `interact()` returns a
  "promote" disposition and `mainloop()`/`TerminalIPythonApp.start()` runs the kernel
  loop instead of `_atexit_once()`;
- a `traitlets >= 5.17` requirement (or the same conditional refusal), and an
  ipykernel presence check with a clear message;
- decisions on the open questions below.

Open questions:

1. **tty input role after hand-off** — should the old terminal answer `input()` when no
   frontend does, or map tty Ctrl-C to a control-channel self-interrupt? (Currently:
   neither; the tty is display-only.)
2. **History** — the kernel shell opens a second `HistoryManager` session on the same
   sqlite file; notebook inputs land in a new session. Handing over the live manager is
   blocked on sqlite thread affinity.
3. **`get_ipython()` in user code** — it resolves through the shared `user_ns`, where
   the kernel shell's `init_user_ns` wrote its own binding; terminal-side user code
   calling it in `--share` mode gets the ZMQ shell. Harmless for hand-off, worth a
   decision for share.
4. **Un-promote** — hand-off is a one-way door. A reversible version is a bigger
   design (the terminal as a first-class ZMQ frontend / subshell owner).

## Optional ipykernel polish

None of it is required anymore, but [`ipykernel-changes.md`](ipykernel-changes.md)
specs quality-of-life changes that would still help embedders (honoring an injected
`shell`, an `embed_instance()` for released-traitlets environments, a factored
`initialize()`, a supported `adopt_session_state()`, documented
`embed_kernel(connection_file=...)`, quieter off-main-thread `init_signal`).

## Prior art

- `ipykernel.embed.embed_kernel` — the promotion skeleton (blocking,
  singleton-once-per-process); wishlist issues ipython/ipython#8097, #4032.
- albertz/background-zmq-ipython — background-thread kernel sharing a live namespace.
- Repeated requests for exactly this feature: ipython/ipython#4066, jupyter/help#298,
  jupyter_console#165, JetBrains PY-31502.
- External-kernel attach: jupyter/jupyter_client#961, jupyter-server/jupyter_server#1305.
- The 2011 two-process `ipython console` model (terminal as ZMQ frontend from the
  start) — architecturally trivial promotion, but terminal UX regressions kept plain
  IPython single-process.

## Running the PoC

```bash
# terminal 1 — a plain session, then promote it
cd exploration/terminal-to-kernel
PYTHONPATH=. ipython
In [1]: %load_ext promote_kernel
In [2]: %promote --external-dir /tmp/ext-kernels        # hand-off (default)
#  ... or keep the terminal interactive too (experimental):
In [2]: %promote --share --external-dir /tmp/ext-kernels

# terminal 2 — console attach
jupyter console --existing /tmp/ext-kernels/kernel-<pid>.json

# or notebook attach
jupyter lab --ServerApp.allow_external_kernels=True \
            --ServerApp.external_connection_dir=/tmp/ext-kernels

# automated end-to-end check (needs pexpect):
python test_promote_e2e.py

# requirement: traitlets >= 5.17 (SingletonScope) — until released:
pip install git+https://github.com/ipython/traitlets
```
