# Exploration: promoting a live terminal IPython session to a Jupyter kernel

**Question.** A user starts a plain `ipython` terminal session. Mid-session they want to
"move" it to a kernel — keep the namespace/history, obtain a standard connection file
(ip, shell/iopub/stdin/control/hb ports, key, transport, signature scheme) — and connect
to it from a notebook.

**Method.** Multi-agent exploration (5 parallel deep-dives over IPython dev checkout,
ipykernel 7.3.0, jupyter_client 8.9.1, plus prior-art/web research, then synthesis),
cross-checked with live in-process experiments. A working proof of concept is in this
directory ([`promote_kernel.py`](promote_kernel.py)) with an end-to-end test
([`test_promote_e2e.py`](test_promote_e2e.py)) that drives a real `ipython` under pexpect,
promotes it, attaches a `jupyter_client`, and verifies shared state and iopub output.

---

## TL;DR

Feasible, and much closer than expected. Two discoveries do most of the work:

1. **The notebook-attach half already shipped.** jupyter_client ≥ 8.3.1 has
   `MultiKernelManager.external_connection_dir` + `KernelManager(owns_kernel=False)`
   (jupyter_client PR #961), and jupyter_server ≥ 2.7.3 exposes it as
   `--ServerApp.allow_external_kernels=True --ServerApp.external_connection_dir=DIR`
   (jupyter_server PR #1305). Any connection file dropped in that directory shows up in
   JupyterLab's kernel picker; "shutdown" from the UI is a detach no-op (the terminal
   process survives), though restart/interrupt raise `RuntimeError` by design.
   Verified working headlessly against `AsyncMultiKernelManager` in this exploration.

2. **ipykernel 7's machinery tolerates being started in a background thread of an
   existing process.** Sockets, heartbeat, iopub, control, and shell dispatch come up
   fine off the main thread (`init_signal` failure is caught and tolerated,
   `ipykernel/kernelapp.py:600-609`), the connection file is written normally, and a
   client can execute against a namespace shared with the main thread.

So a `%promote` magic that starts the kernel machinery in a daemon thread, shares
`user_ns`/`user_module` with the live terminal shell, and writes its connection file into
the external-connection dir gives a *working* terminal+notebook dual-frontend session
today — the PoC here does exactly that. The remaining hard problems are about making it
*correct* rather than possible: shell identity (one shell object vs. two sharing a
namespace), execution serialization between the two frontends, stdout ownership, and
interrupt semantics.

---

## What already exists (reuse as-is)

**Connection info creation** is fully solved:

- `IPKernelApp.init_connection_file` defaults to `kernel-<pid>.json` under the Jupyter
  runtime dir and registers atexit cleanup (`ipykernel/kernelapp.py:331-348`).
- `init_sockets`/`init_iopub` bind shell/stdin/control/iopub (random ports), heartbeat
  runs in its own thread (`kernelapp.py:352+`, `heartbeat.py:27`).
- `jupyter_client.connect.write_connection_file` emits exactly the JSON asked for —
  ip, transport, five ports, auto-generated HMAC key, `hmac-sha256`
  (`jupyter_client/connect.py:55-186`); `ConnectionFileMixin.write_connection_file`
  wires it in (`connect.py:532-558`).
- `%connect_info` (`ipykernel/zmqshell.py:405`) already prints the JSON, the file path,
  and the `jupyter console --existing` hint — the right UX to reuse after promotion.

**Attach paths**, from zero-effort to nicest:

- `jupyter console --existing kernel-<pid>.json` / qtconsole: works today
  (`jupyter_client/connect.py:560-602, 713-731`).
- `jupyter lab --ServerApp.allow_external_kernels=True --ServerApp.external_connection_dir=DIR`:
  auto-discovers connection files (they must contain `kernel_name` and `key` — every
  file written by `write_connection_file` does); kernel appears in the Lab picker.
  External kernels are second-class: shutdown = detach (good for us), restart/interrupt
  raise (`jupyter_client/multikernelmanager.py`, `KernelManager.owns_kernel`).
- A custom **kernel provisioner** (entry-point group `jupyter_client.kernel_provisioners`,
  `jupyter_client/provisioning/factory.py:32`; `LocalProvisioner` as template) whose
  `launch_kernel()` returns the live kernel's connection info instead of spawning —
  the pattern pyxll-jupyter's `ExistingProvisioner` and `extipy` use in production.
  Caveat: with `owns_kernel=True`, UI shutdown sends a real `shutdown_request`, so the
  kill policy needs thought; the `external_connection_dir` route avoids this entirely.

Note VS Code cannot attach to a raw local connection file (open FR
microsoft/vscode-jupyter#13849); Spyder can.

---

## Candidate architectures

### A. Background-thread kernel adopting the live session (what the PoC does)

`%promote` starts `IPKernelApp` in a daemon thread; the terminal REPL keeps the main
thread; both frontends stay live, sharing `user_ns`/`user_module`.

- **Works now** (see PoC + test), including `execute_result` and `stream` on iopub, and
  bidirectional variable visibility.
- **Unsolved correctness issues:** the two frontends execute concurrently with no
  serialization (races on `execution_count`, history, display state); user code
  initiated from the notebook runs off the main thread, so SIGINT-based interrupt,
  GUI event loops, and some top-level-await patterns degrade; two shell objects share a
  namespace but not identity (see obstacles below).
- Good shape for an *extension/prototype*; as a product feature the concurrency
  semantics are a permanent support burden unless the terminal goes read-only or
  submissions are funneled through one queue (see D).

### B. Suspend-and-hand-off (`%promote` exits the REPL, process becomes a kernel)

Exit `interact()` (via `keep_running`/`ask_exit`, `IPython/terminal/interactiveshell.py:997-1001`
— but through a new exit path that skips `mainloop()`'s `_atexit_once()`, which wipes
`user_ns` and closes history), then run essentially `ipykernel.embed.embed_kernel`
(`ipykernel/embed.py:17-57`) on the main thread, transplanting shell state. The user
re-attaches interactively with `jupyter console --existing` — same tty, now a ZMQ
frontend. Clean threading story (kernel owns the main thread; interrupts and GUI loops
work), one-way door in v1. The synthesis agent recommended this as the shippable v1;
the PoC results suggest A is more attractive than expected, but B remains the correct
semantics for "move" rather than "share".

### C. Kernel-first (`ipython --promotable` = kernel + local ZMQ frontend from the start)

The original 2011 two-process `ipython console` model (ipython PR #433, later
jupyter_console). Architecturally trivial — promotion is just printing `%connect_info` —
but regresses the terminal UX (jupyter_console's completion/debugger/prompt integration
lags `TerminalInteractiveShell`, and completion/input round-trips block while the kernel
is busy: the reason terminal IPython deliberately stayed in-process). Doesn't answer
"I *already have* a session". Good opt-in mode someday, not the feature.

### D. Loop-unified dual frontend (the good end state)

Bring up the kernel as in A/B, but run the prompt_toolkit application inside the same
event loop that services ZMQ (tornado IOLoop is asyncio-backed; `Kernel.start` just
registers stream callbacks, `kernelbase.py:546-572`), and funnel terminal submissions
through the kernel's own execution queue so the terminal becomes "just another
frontend" — possibly owning a dedicated **subshell** (JEP 91 machinery already in
ipykernel 7: `shellchannel.py`, `subshell_manager.py`). Terminal prompt redraw around
async iopub output uses the `patch_stdout` machinery IPython already employs. This
resolves every correctness issue in A (single executor, single shell object, serialized
history/execution_count) at the cost of a real refactor of
`interact()`/`mainloop()` loop ownership (`terminal/interactiveshell.py:1005-1046`).
Estimated 1-2 months; best done after an A/B-grade prototype ships behind a flag.

*(Rejected: `ipykernel.inprocess` — no real ZMQ sockets, solves the inverse problem.)*

---

## Empirically verified obstacles (with fixes used in the PoC)

All verified by experiment in this exploration, not just code reading:

1. **Two singleton collisions.** `IPythonKernel.__init__` calls
   `self.shell_class.instance(...)` (`ipykernel/ipkernel.py:140`) → traitlets
   `MultipleInstanceError: An incompatible sibling of 'ZMQInteractiveShell' is already
   instantiated as singleton: TerminalInteractiveShell`. Same story for
   `IPKernelApp.instance()` vs `TerminalIPythonApp`. PoC clears both slots
   (`BaseIPythonApplication.clear_instance()`, `InteractiveShell.clear_instance()`);
   the real fix is letting `IPythonKernel` accept an injected, pre-existing shell —
   a small upstream ipykernel change.

2. **`get_ipython()` re-points to the ZMQ shell and breaks the terminal.** After the
   swap, prompt_toolkit key-binding filters resolve terminal-only traits through
   `get_ipython()` on *every keypress* (`IPython/terminal/shortcuts/filters.py:85`,
   `shell.auto_match`) → `AttributeError` → unhandled exception in the prompt loop →
   "Press ENTER to continue..." wedge. PoC restores
   `InteractiveShell._instance = <terminal shell>`; trade-off: `IPython.display.display()`
   from notebook code then resolves the terminal display publisher and doesn't reach the
   notebook (`execute_result` is unaffected — displayhooks are per-shell, installed
   around each `run_cell`). This is the strongest argument for **one shell object**, not
   two shells sharing a namespace.

3. **`patch_stdout` evicts the kernel's OutStream.** `prompt_for_code` wraps every
   prompt in prompt_toolkit's `patch_stdout(raw=True)`
   (`IPython/terminal/interactiveshell.py:949`), which restores the pre-prompt
   `sys.stdout` on exit — so the iopub `OutStream` installed by `init_io`
   (`kernelapp.py:530-546`) is silently removed one prompt after promotion and
   notebook `print()` stops reaching iopub. PoC swaps the ZMQ streams in only around
   kernel-side executions via the kernel shell's `pre_execute`/`post_execute` events.
   A real implementation needs a deliberate stdout policy (tee object, or D's unified
   loop with `patch_stdout` managing both).

4. **stdout duality is a policy choice with existing knobs.** `OutStream(echo=...)` via
   `IPKernelApp.quiet=False` (`kernelapp.py:181, 537-546`) tees kernel output to the real
   tty, so the terminal user sees notebook activity. Raw echo writes from another thread
   garble the prompt cosmetically until routed through `patch_stdout`.

5. **stdin/interrupt semantics flip.** After promotion, `input()` from notebook-initiated
   code is answered by the notebook's stdin channel, not the tty
   (`kernelbase.py:1368-1445`); kernel interrupt arrives via the control channel, and in
   architecture A a busy kernel thread cannot be interrupted by tty Ctrl-C at all
   (a real implementation on the main thread — B/D — fixes this).

6. **History.** The kernel's shell opens a second `HistoryManager` session on the same
   sqlite file; notebook-side inputs land in a separate session. Handing over the live
   `HistoryManager` object is complicated by sqlite thread affinity
   (`IPython/core/history.py`).

7. **`_atexit_once()` trap for architecture B.** A hand-off that exits `mainloop()`
   normally would wipe `user_ns` and close history before the kernel starts; B needs an
   exit path that skips it.

## What a real implementation would change

- **ipykernel:** allow injecting an existing shell (or a shell *object*) into
  `IPythonKernel` instead of `shell_class.instance(...)` (`ipkernel.py:140`); factor
  `IPKernelApp.initialize()` so IO/signal/singleton steps are individually optional.
  (`embed_kernel`'s `IPKernelApp.initialized()` guard, `embed.py:33-36`, already makes
  promotion idempotent for free.)
- **IPython:** a `%promote` magic (or `ipython --promotable`); a "kernel-capable" seam on
  `InteractiveShell` where DisplayPublisher/DisplayHook/streams can be swapped or teed
  at runtime (they are already trait-selected classes — the exact seam ipykernel
  overrides); an `interact()` exit path without `_atexit_once()`; longer-term, the D
  refactor putting the prompt and ZMQ on one loop with the terminal as a subshell owner.
- **Nothing needed** in jupyter_client/jupyter_server for a first release —
  `external_connection_dir` covers discovery; a provisioner + Lab UX polish can come later.

## Prior art

- `ipykernel.embed.embed_kernel` (`embed.py:17-57`) — the promotion skeleton; blocking,
  singleton-once-per-process; wishlist issues ipython#8097, ipython#4032 (both open).
- albertz/background-zmq-ipython — production PoC of a background-thread kernel sharing
  a live namespace (subclasses ZMQInteractiveShell/IPythonKernel, no-ops signal hooks,
  own IOLoop thread, thread-routed stdout).
- The feature has been requested repeatedly: ipython#4066, jupyter/help#298,
  jupyter_console#165, JetBrains PY-31502.
- jupyter_client PR #961 / jupyter_server PR #1305 (external kernels), pyxll-jupyter
  `ExistingProvisioner`, `extipy` (provisioner-based attach).
- The old GUI-embedder pattern (`kernel.do_one_iteration()` pumped from a host loop) is
  dead in ipykernel 7 — `Kernel` no longer defines `do_one_iteration`; integration goes
  through the ShellChannelThread/subshell machinery.

## Open questions

1. One-way (B: terminal goes passive) vs dual-frontend (A now / D eventually)? The PoC
   shows dual-frontend is viable; is unserialized concurrent execution acceptable behind
   an "experimental" flag, or must promotion wait for the D-style single queue?
2. Where does shell injection land — ipykernel change, or an IPython-shipped
   `PromotedKernel(IPythonKernel)` subclass?
3. One shell object (graft ZMQ publishers onto `TerminalInteractiveShell`) vs two shells
   sharing state? Obstacle 2 argues strongly for one object; that means
   `TerminalInteractiveShell` growing runtime-swappable display plumbing.
4. Should the tty keep any input role after promotion (answer `input()` when no frontend
   does; map tty Ctrl-C to a control-channel self-interrupt)?
5. History: second session on the same sqlite file, or hand over the live manager?

## Running the PoC

```bash
# terminal 1 — a plain session, then promote it
cd exploration/terminal-to-kernel
PYTHONPATH=. ipython
In [1]: %load_ext promote_kernel
In [2]: %promote --external-dir /tmp/ext-kernels

# terminal 2 — console attach (works with nothing else)
jupyter console --existing /tmp/ext-kernels/kernel-<pid>.json

# or notebook attach
jupyter lab --ServerApp.allow_external_kernels=True \
            --ServerApp.external_connection_dir=/tmp/ext-kernels
# → the session appears in the kernel picker; open a notebook on it.

# automated end-to-end check (needs pexpect):
python test_promote_e2e.py
```
