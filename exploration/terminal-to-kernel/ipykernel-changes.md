# ipykernel changes to support promoting an existing interactive session to a kernel

**Status:** implementation-ready proposal.
**Target repo:** `ipython/ipykernel` (line anchors below are against ipykernel **7.3.0**;
re-locate them on current `main` before editing — the structures are stable but lines
drift).
**Audience:** an implementing agent with no other context. Everything needed is in this
document.

## Background and motivating use case

IPython wants a `%promote` feature: a user in a plain *terminal* IPython session turns
that live session into a standard Jupyter kernel — keeping `user_ns`, `user_module`,
execution count — writes a normal connection file, and connects to it from
`jupyter console --existing` or a notebook (via jupyter_server ≥ 2.7.3
`--ServerApp.allow_external_kernels=True --ServerApp.external_connection_dir=DIR`,
which auto-discovers connection files; jupyter_client ≥ 8.3.1, PR jupyter/jupyter_client#961).

The selected architecture is **hand-off**: the terminal REPL is finished for good and
the process's **main thread** becomes the kernel event loop (main-thread execution is a
hard requirement — signal-based `interrupt_request` handling and many libraries need
it). A working proof of concept exists in `ipython`'s exploration branch
(`exploration/terminal-to-kernel/promote_kernel.py` on branch
`claude/ipython-terminal-kernel-migration-km1thx`), but it must reach into private
state to work. The changes below give it supported seams. Each change is independently
useful and mergeable; they are ordered by value.

What the IPython-side promotion code should look like **after** these changes:

```python
# runs inside the terminal process; `shell` is the live TerminalInteractiveShell
from ipykernel.kernelapp import IPKernelApp

app = IPKernelApp.embed_instance(          # Change 2: no singleton collision
    connection_file="/path/to/dir/kernel-1234.json",   # Change 5: honored today, keep tested
    quiet=False,                           # echo iopub streams to the tty
    capture_fd_output=False,
)
app.initialize([])                         # or the finer-grained steps from Change 3
app.kernel.adopt_session_state(            # Change 4
    user_ns=shell.user_ns,
    user_module=shell.user_module,
    execution_count=shell.execution_count,
)
app.start()                                # main thread becomes the kernel loop
```

## Verified behavior of 7.3.0 (empirical, not just code reading)

These were all confirmed by experiment in a live process:

- `IPKernelApp` can be brought up in a process that already runs an interactive
  session; a `jupyter_client` connects, executes against an adopted namespace, and
  receives `execute_result`/`stream`/`display_data` on iopub.
- Two `MultipleInstanceError` collisions block the naive path:
  - `IPythonKernel.__init__` → `self.shell_class.instance(...)`
    (`ipykernel/ipkernel.py:140`) vs an existing `TerminalInteractiveShell` singleton;
  - `IPKernelApp.instance()` vs the host's `TerminalIPythonApp` (both register on
    shared `Application`/`BaseIPythonApplication` ancestors via
    `SingletonConfigurable._walk_mro`).
- `initialize()` in a non-main thread survives `init_signal()` failure by design
  (`kernelapp.py:766-774` catches it) but logs a full ERROR traceback.
- `interrupt_request` → `os.kill(pid, SIGINT)` (`kernelbase.py:1040-1074`) with
  `default_int_handler` installed around handlers (`kernelbase.py:496-503`) delivers
  `KeyboardInterrupt` into busy user code **only when execution owns the main thread**.
- `embed_kernel(**kwargs)` (`ipykernel/embed.py:17-57`) relays kwargs to the
  `IPKernelApp` constructor — but only on the first call, blocks forever in
  `app.start()` (`embed.py:57`), and hits both singleton collisions above when a
  terminal session owns the process.

---

## Change 1 — honor an injected `shell` on `IPythonKernel`

**Problem.** `IPythonKernel.__init__` unconditionally creates its shell:

```python
# ipykernel/ipkernel.py:140 (inside __init__)
self.shell = self.shell_class.instance(
    parent=self,
    profile_dir=self.profile_dir,
    user_module=self.user_module,
    user_ns=self.user_ns,
    kernel=self,
    compiler_class=self.compiler_class,
)
```

`shell` is *already* a trait that admits injection —
`shell = Instance("IPython.core.interactiveshell.InteractiveShellABC", allow_none=True)`
(`ipkernel.py:74`) — but a value passed to the constructor is clobbered, and the
`.instance()` call raises `MultipleInstanceError` when any other `InteractiveShell`
subclass is the registered singleton.

**Change.** Create the shell only when not provided:

```python
if self.shell is None:
    self.shell = self.shell_class.instance(
        parent=self,
        profile_dir=self.profile_dir,
        user_module=self.user_module,
        user_ns=self.user_ns,
        kernel=self,
        compiler_class=self.compiler_class,
    )
else:
    # adopt an injected shell: it must quack like ZMQInteractiveShell for the
    # wiring below (displayhook/display_pub attribute assignment)
    self.shell.kernel = self
```

Keep the post-creation wiring (`ipkernel.py:148-158`: `shell.displayhook.session/
pub_socket/topic`, `shell.display_pub.session/pub_socket`) running for both paths — it
is plain attribute assignment and is exactly what an injected shell needs to start
publishing.

**Constraints / notes.**
- Document that an injected shell is expected to be a `ZMQInteractiveShell` (or
  provide ZMQ-compatible `displayhook`/`display_pub` objects). Injecting a
  `TerminalInteractiveShell` directly is a *future* step that additionally requires
  runtime-swappable display plumbing on the IPython side; do not attempt it here.
- The `user_ns`/`user_module` observers (`ipkernel.py:92-114`) already forward to
  `self.shell` when set — no change needed there.

**Tests.** Construct `IPythonKernel(shell=premade_zmq_shell, ...)` in a process where a
different `InteractiveShell` subclass singleton exists; assert no
`MultipleInstanceError`, the kernel uses the provided object, and displayhook/display_pub
get the iopub socket wired.

## Change 2 — `IPKernelApp.embed_instance()`: construction without singleton collision

**Problem.** `IPKernelApp.instance()` registers on every singleton ancestor
(`SingletonConfigurable._walk_mro`), so in a process whose `Application` slot is owned
by another app (e.g. `TerminalIPythonApp`) it raises `MultipleInstanceError`. Both
`embed_kernel` (`embed.py:33-36`) and any promotion code hit this. Meanwhile parts of
ipykernel rely on `IPKernelApp.initialized()`/`IPKernelApp.instance()` working — e.g.
`ipykernel.connect.get_connection_file` and therefore `%connect_info` — so plain
`IPKernelApp(...)` construction is not enough.

**Change.** Add a classmethod:

```python
@classmethod
def embed_instance(cls, **kwargs):
    """Return the IPKernelApp singleton for embedding into an existing process.

    Unlike ``instance()``, this never raises MultipleInstanceError when another
    Application (e.g. a terminal IPython app) already owns the process-global
    singleton slots: the app registers as ``IPKernelApp._instance`` only, leaving
    ancestor registrations (Application, BaseIPythonApplication) untouched.
    """
    if cls.initialized():
        return cls.instance()
    try:
        return cls.instance(**kwargs)
    except MultipleInstanceError:
        app = cls(**kwargs)
        cls._instance = app
        return app
```

This keeps `IPKernelApp.initialized()` / `.instance()` (and thus `%connect_info`,
`ipykernel.connect`) working, while the host application keeps answering
`Application.instance()`.

**Follow-up (do not implement now, note in the docstring):** if/when traitlets grows
scoped singleton registries (`SingletonScope`, prototyped in
https://github.com/Carreau/traitlets/tree/multiton), this method can be expressed with
a scope instead of the targeted `_instance` write.

**Also:** switch `embed_kernel` (`embed.py:33-38`) to use `embed_instance`.

**Tests.** In a process where `Application` singleton is claimed by another app class:
`embed_instance()` succeeds; `IPKernelApp.initialized()` is True;
`Application.instance()` still returns the host app; second `embed_instance()` call
returns the same app (idempotent).

## Change 3 — factor `initialize()` into transport vs. process-takeover steps

**Problem.** `initialize()` (`kernelapp.py:749-786`) is one linear sequence mixing two
concerns:

- **transport:** `init_connection_file` → `init_poller` → `init_sockets` →
  `init_heartbeat` → `write_connection_file` → `log_connection_info`
- **process takeover:** `init_blackhole` (can redirect the real stdio), `init_io`
  (replaces `sys.stdout/stderr/displayhook`), `init_signal` (SIGINT)
- **kernel/shell:** `init_kernel` → `init_path` → `init_shell` → gui/extensions/code

An embedding caller wants all of the transport, a *selection* of the takeover (e.g. no
fd capture, echoing OutStreams, no blackhole), and the kernel/shell steps with an
injected shell. Today the selection is only reachable through traits
(`quiet`, `outstream_class`, `capture_fd_output`, `no_stdout`/`no_stderr`), and there
is no supported way to run the groups separately.

**Change.** Introduce three methods that `initialize()` calls in order, preserving the
exact current sequence and behavior:

```python
def init_transport(self):
    self.init_connection_file()
    self.init_poller()
    self.init_sockets()
    self.init_heartbeat()
    self.write_connection_file()
    self.log_connection_info()

def init_process(self):
    # NOTE: init_blackhole currently runs before init_connection_file in
    # initialize(); keep the global order identical by calling init_blackhole
    # from initialize() before init_transport() (see below).
    self.init_io()
    try:
        self.init_signal()
    except Exception:
        ...  # existing tolerant logging

def init_kernel_and_shell(self):
    self.init_kernel()
    self.init_path()
    self.init_shell()
    if self.shell:
        self.init_gui_pylab()
        self.init_extensions()
        self.init_code()
```

`initialize()` becomes: `_init_asyncio_patch` → `super().initialize` → subapp check →
`init_pdb` → `init_blackhole` → `init_transport()` → `init_process()` →
`init_kernel_and_shell()` → the existing stdout/stderr flush. **Behavior must be
byte-identical for the normal path** — this is a pure extraction; the test suite must
pass unchanged.

**Tests.** Existing suite green (that *is* the test); plus one new test calling
`init_transport()` alone and asserting a valid connection file + bound sockets exist
while `sys.stdout` is untouched.

## Change 4 — `IPythonKernel.adopt_session_state(...)`

**Problem.** Promotion code currently pokes attributes in the right magic order:

```python
app.kernel.user_module = shell.user_module   # must come first
app.kernel.user_ns = shell.user_ns           # observer re-runs init_user_ns
app.kernel.shell.execution_count = shell.execution_count  # not exposed on kernel
```

plus `shell.set_completer_frame()` which `embed_kernel` does (`embed.py:55`) and ad-hoc
callers forget.

**Change.** One supported method on `IPythonKernel`:

```python
def adopt_session_state(self, *, user_ns=None, user_module=None, execution_count=None):
    """Adopt session state from an existing interactive session.

    Sets user_module before user_ns (the user_ns observer re-initializes the
    namespace against the current module), propagates the execution counter,
    and refreshes the completer frame.
    """
    if user_module is not None:
        self.user_module = user_module
    if user_ns is not None:
        self.user_ns = user_ns
    if execution_count is not None:
        self.shell.execution_count = execution_count
    self.shell.set_completer_frame()
```

**Deliberately out of scope:** history-manager handoff. The adopted shell's own
`HistoryManager` opens a second session on the same sqlite file, which is acceptable;
transplanting the live manager object is blocked on sqlite thread affinity and needs
its own design. Say so in the docstring.

**Tests.** Adopt a namespace dict + module; execute code through the kernel's shell and
assert it reads/writes the adopted dict; assert `In[n]` numbering continues from the
adopted `execution_count`.

## Change 5 — keep `embed_kernel(connection_file=...)` working, and test it

**Status:** `embed_kernel` already relays kwargs to the `IPKernelApp` constructor, so
`embed_kernel(connection_file="/dir/kernel-123.json")` works today *by accident of
plumbing* — it is undocumented and untested, and only effective on the first call.
The connection file written by `write_connection_file` already contains the
`kernel_name` and `key` fields that jupyter_server's `external_connection_dir`
discovery requires.

**Change.**
- Document `connection_file=` in the `embed_kernel` docstring (including the
  external-connection-dir use case shown in Background).
- Add a test: `embed_kernel`-style app with `connection_file` pointing into a temp
  dir; assert the file lands there with all 9 fields
  (`transport, ip, shell_port, iopub_port, stdin_port, control_port, hb_port, key,
  signature_scheme`) plus `kernel_name`.
- In `embed_kernel`, when `IPKernelApp.initialized()` short-circuits to the existing
  app (`embed.py:33-36`) *and* the caller passed kwargs, emit a warning that the
  kwargs are ignored (today they are silently dropped).

## Change 6 (small, optional) — quieter off-main-thread `init_signal`

`initialize()` catches `init_signal()` failure and logs a full ERROR traceback
(`kernelapp.py:766-774`). When the failure is the expected
`ValueError: signal only works in main thread of the main interpreter`, downgrade to a
single-line `log.info` (keep ERROR + traceback for anything else). Purely cosmetic for
background-thread embedders.

---

## Acceptance criteria (end-to-end)

A new integration test (can live in `ipykernel/tests/`) that reproduces the promotion
scenario **using only the public seams above** — no `clear_instance()`, no `_instance`
writes, no private attribute pokes:

1. In a subprocess, create an `InteractiveShell` subclass singleton and a host
   `Application` singleton (stand-ins for the terminal session); put a sentinel in its
   `user_ns`.
2. `IPKernelApp.embed_instance(connection_file=<tmpdir>/kernel-<pid>.json, quiet=False,
   capture_fd_output=False)`; `app.initialize([])`;
   `app.kernel.adopt_session_state(user_ns=..., user_module=..., execution_count=...)`;
   `app.start()` on the main thread.
3. From the parent process, attach a `BlockingKernelClient` on the connection file and
   assert:
   - execute sees the sentinel and can assign new names visible in the adopted dict;
   - `threading.current_thread().name == "MainThread"` inside an execution;
   - `print()` arrives as an iopub `stream`; `IPython.display.display()` arrives as
     `display_data`;
   - an `interrupt_request` on the control channel turns a `time.sleep(120)` execution
     into a `KeyboardInterrupt` error reply;
   - `shutdown_request` exits the subprocess cleanly.

All existing ipykernel tests must pass unchanged (Change 3 is a pure extraction;
Changes 1/2/4/5 are additive).

## Non-goals

- Adopting a `TerminalInteractiveShell` *object* as the kernel shell (needs IPython-side
  display-plumbing work first; Change 1 only opens the seam).
- History-manager transplantation (sqlite thread affinity; separate design).
- Background-thread (dual-frontend) operation as a supported mode — the changes happen
  to help it, but the supported story is main-thread hand-off.
- Any jupyter_client / jupyter_server changes (external_connection_dir already covers
  notebook attach).

## References

- Working PoC + exploration write-up: `ipython/ipython` branch
  `claude/ipython-terminal-kernel-migration-km1thx`,
  `exploration/terminal-to-kernel/` (README.md, promote_kernel.py, test_promote_e2e.py —
  the e2e test there is a template for the acceptance test).
- jupyter_server external kernels: jupyter/jupyter_client#961,
  jupyter-server/jupyter_server#1305.
- Prior art: `ipykernel.embed.embed_kernel`; albertz/background-zmq-ipython;
  wishlist issues ipython/ipython#8097, ipython/ipython#4032.
- Scoped singletons prototype: https://github.com/Carreau/traitlets/tree/multiton
  (`SingletonScope`) — would subsume the `_instance` handling in Change 2.
