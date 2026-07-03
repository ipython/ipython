# Scoped Singleton Instances for IPython / traitlets

**Status:** Design proposal / migration plan (hand-off document for coding agents)
**Scope:** `SingletonConfigurable.instance()`, `get_ipython()`, and the migration away
from singleton service-location where cheap.

---

## 1. Problem statement and naming

### 1.1 What we want

Inside a `with` block, every `SomeSingleton.instance()` call — and therefore
`get_ipython()` — should resolve to a caller-supplied instance instead of the one
process-global `_instance`. Outside the block, behavior is byte-for-byte identical to
today.

```python
shell_a = InteractiveShell.instance()          # the process global
shell_b = InteractiveShell(...)                # a second, ordinarily illegal

with shell_b.as_current():
    assert get_ipython() is shell_b            # scoped override
    assert InteractiveShell.instance() is shell_b
assert get_ipython() is shell_a                # restored, exception-safe
```

### 1.2 The pattern has a name

This is **dynamic scoping** of a global binding — a value looked up by *when* control
passes through it, not by *where* the code is written (lexical scoping). Equivalently:
**context-local / dynamically-scoped state** with a **shadowing overlay** over a global
default.

Prior art, and what we borrow from each:

| Prior art | What it contributes to this design |
|---|---|
| Lisp special variables (`defvar` / dynamic `let`) | The canonical model: bind a name for the dynamic extent of a form, restore on exit. |
| `decimal.localcontext()` | Exact API shape we mimic: a CM that overlays a thread/context-local value on a process default, `__enter__` returns the active object. |
| PEP 567 `contextvars.ContextVar` | The storage primitive. Async-task-safe and thread-isolated by construction; `Token` gives precise nested restore. |
| Flask app/request context (`AppContext`, `current_app`) | The *stack* discipline for nesting, and the "current object proxy" idea (`get_ipython()` is our `current_app`). Flask itself moved this onto `ContextVar` in 2.0. |
| `numpy.errstate`, `warnings.catch_warnings` | Precedent that "scoped override of a global via CM" is idiomatic, expected Python, not exotic. |

The IPython codebase **already implements this pattern by hand, twice**: `BuiltinTrap`
reference-counts a nested save/restore of the builtins `get_ipython`
(`IPython/core/builtin_trap.py:38-44`), and `embed()` manually
saves/clears/restores `InteractiveShell._instance` (`IPython/terminal/embed.py:417-433`).
This proposal generalizes those into one correct primitive.

### 1.3 Why the obvious implementation (assign `_instance`, restore in `finally`) is not enough

Assigning `cls._instance = shell_b` is a **process-global mutation**. Any concurrent
thread — background jobs, the history-save thread, GUI event-loop callbacks — that calls
`get_ipython()` during the block sees `shell_b`, which is wrong and racy. A `ContextVar`
overlay confines the override to the current thread/task while leaving the global default
intact for everyone else. That distinction is the entire reason to prefer contextvars over
the embed-style save/restore for the general mechanism.

---

## 2. Recommended design

### 2.1 One-line summary

Add a **ContextVar overlay on top of the existing `_instance` class attribute**, changed
**only inside the four singleton methods** of `SingletonConfigurable`. `_instance` remains
the global default and source of truth for the single-instance case; the ContextVar, when
set, shadows it for the current context only. Ship a CM `inst.as_current()` that
sets/resets the ContextVar with a `Token` (exception-safe, nesting-safe). Do it in
**traitlets** (so `Application` and `get_config()` benefit), and have IPython consume it —
with a thin IPython-side fallback shim so IPython can ship before a traitlets release
lands.

### 2.2 Resolution order (the contract)

`instance()` / `initialized()` resolve in this order:

1. **ContextVar override for this class's singleton root**, if set in the current
   context → return it.
2. Else the classic **`cls._instance`** class attribute (today's behavior, including
   `_walk_mro` write-through).
3. Else (for `instance()`) **create** and write through as today.

"Singleton root" = the topmost class in `_walk_mro()` (the class directly below
`SingletonConfigurable`). Storing the override keyed on the root — resolved by the *same*
`_walk_mro` walk that write-through uses — makes `bam.as_current()` visible to
`Bar.instance()` and `Bam.instance()`, exactly matching the ancestor write-through
contract that `tests/config/test_configurable.py:315-339` pins.

### 2.3 traitlets code sketch

In `traitlets/config/configurable.py`:

```python
import contextlib
import contextvars

class SingletonConfigurable(LoggingConfigurable):

    _instance = None

    # One ContextVar per singleton root class, created lazily, keyed by the
    # root class object. The ContextVar holds the scoped override instance.
    _instance_overrides: t.ClassVar[
        dict[type, contextvars.ContextVar[t.Any]]
    ] = {}

    @classmethod
    def _singleton_root(cls) -> type[SingletonConfigurable]:
        """Topmost non-SingletonConfigurable ancestor — the write-through key."""
        root = cls
        for subclass in cls._walk_mro():   # yields cls ... root order
            root = subclass
        return root

    @classmethod
    def _override_var(cls) -> contextvars.ContextVar[t.Any]:
        root = cls._singleton_root()
        var = SingletonConfigurable._instance_overrides.get(root)
        if var is None:
            var = contextvars.ContextVar(
                f"singleton_override_{root.__name__}", default=None
            )
            SingletonConfigurable._instance_overrides[root] = var
        return var

    @classmethod
    def _current_override(cls: type[CT]) -> CT | None:
        return cls._override_var().get()

    @classmethod
    def instance(cls: type[CT], *args: t.Any, **kwargs: t.Any) -> CT:
        override = cls._current_override()
        if override is not None:
            if isinstance(override, cls):
                return override
            raise MultipleInstanceError(
                f"An incompatible sibling of {cls.__name__!r} is active "
                f"as a scoped override: {type(override).__name__}"
            )
        # ---- unchanged classic path below ----
        if cls._instance is None:
            inst = cls(*args, **kwargs)
            for subclass in cls._walk_mro():
                subclass._instance = inst
        if isinstance(cls._instance, cls):
            return cls._instance
        raise MultipleInstanceError(...)

    @classmethod
    def initialized(cls) -> bool:
        if cls._current_override() is not None:
            return True
        return hasattr(cls, "_instance") and cls._instance is not None

    @contextlib.contextmanager
    def as_current(self: CT) -> t.Iterator[CT]:
        """Dynamically scope ``instance()`` to *self* for the current context.

        Within the block, ``type(self).instance()`` (and any singleton class
        in its MRO) returns *self* in the current thread / async task only.
        The process-global instance and other threads are unaffected.
        """
        var = type(self)._override_var()
        token = var.set(self)
        try:
            yield self
        finally:
            var.reset(token)

    @classmethod
    @contextlib.contextmanager
    def scoped_instance(cls: type[CT], **kwargs: t.Any) -> t.Iterator[CT]:
        """Construct a fresh instance (never via ``instance()`` — the global
        is untouched) and make it current for the block."""
        inst = cls(**kwargs)
        with inst.as_current():
            yield inst
```

Notes on the sketch:

- **`as_current()` is an instance method** (scope *this* object); the auto-create form is
  the separate classmethod `scoped_instance(**kwargs)`, which constructs directly via
  `cls(**kwargs)` — deliberately *not* via `instance()` — so it never touches the global.
  (An earlier draft made `as_current` a classmethod taking `inst=None`; that reads
  wrong at call sites — `shell_b.as_current()` would have silently ignored `shell_b`.)
- `clear_instance()` is **unchanged** and continues to operate on the `_instance` class
  attribute. Inside an `as_current` block it does *not* touch the override (documented:
  the override is CM-managed, not clear-able). This preserves
  `test_application.py:599-632` subcommand choreography verbatim, because that path never
  enters `as_current`.
- `MultipleInstanceError` is preserved on both the override path (sibling override
  incompatible with a base-class `instance()` call) and the classic path.
- Typing: the `CT` bound TypeVar already in the module carries through;
  `from __future__ import annotations` is already on the file.
- The `_instance_overrides` dict is process-global metadata (which ContextVar exists per
  root), never the instances themselves — no leak, keyed by class.

### 2.4 Thread and async semantics (stated precisely, because it is the crux)

`ContextVar.get()` returns:

- the value **set in the current thread's / current async task's context**, else
- the ContextVar's **`default`** (here `None`), which then falls through to the global
  `_instance`.

Concretely:

- A thread created *inside* an `as_current` block does **not** inherit the override — a
  fresh thread starts with an empty `contextvars.Context`, so its `get()` sees
  `default=None` → falls through to the global `_instance`. This is the *correct*
  behavior for IPython: the history-save thread, background jobs, GUI callbacks keep
  resolving to the real global shell, not to a transient embedded one.
- `asyncio.create_task()` **copies** the current context at creation, so a task spawned
  inside the block *does* see the override for its lifetime. Also correct: `%autoawait`
  code and cell coroutines conceptually belong to the shell that launched them.
- `loop.run_in_executor` / `concurrent.futures` worker threads: **no** inheritance (fresh
  thread) unless the caller explicitly `contextvars.copy_context().run(...)`. Acceptable
  for v1.

The design deliberately makes the override an **overlay on a preserved global default**,
so "no inheritance" degrades to "you get the normal global shell", never to "you get
None". That is the hybrid we want: global by default, contextvar only as a scoped shadow.

### 2.5 Nesting and exception safety

`Token`-based `var.reset(token)` in a `finally` gives correct LIFO nesting for free —
this is what makes `tests/test_embed.py::test_nest_embed` (lines 74-149) correct
*without* the current save/restore gymnastics, and fixes `embed()`'s missing try/finally
(`terminal/embed.py` has no `finally` today: an exception in the embedded shell skips the
restore).

---

## 3. Where it lives: traitlets, with an IPython-side shim (two-stage)

### 3.1 Recommendation: traitlets is the home, staged.

**Stage 1 (IPython-only, ships immediately):** Override `instance()` / `initialized()` /
add `as_current()` on `InteractiveShell` itself, backed by a module-level `ContextVar` in
`IPython.core.getipython`. Make `get_ipython()` consult the ContextVar first. Rewrite
`embed()` to use `as_current`. Zero traitlets dependency bump; ships on IPython's
cadence.

**Stage 2 (traitlets):** Land the mechanism in `SingletonConfigurable` as in §2.3. Then
`InteractiveShell` deletes its Stage-1 override and inherits. `Application` (and thus
`get_config()` at `application.py:1124`, jupyter_server, nbconvert) transparently gain
scoped instances.

### 3.2 Justification

- The mechanism is a property of *singletons in general*, not of shells.
  `Application.instance()` and `get_config()` have the identical global-shadowing need
  (subcommand dispatch already fakes it with `clear_instance` + re-`instance`,
  `application.py:699-722`).
- Putting it in traitlets means one correct implementation, not one-per-downstream.
- But traitlets releases are slower and gate jupyter_server / nbconvert / qtconsole, all
  of which lean on `Application.instance()`. Staging de-risks: IPython proves the design
  on its own subclass first; traitlets adopts once the semantics are settled. Because
  Stage 1 only *overrides* the four methods (they are plain classmethods, no metaclass —
  verified `configurable.py:527-600`), the override is a clean, reversible seam.
- **Backward-compat invariant, both stages:** with no `as_current` active,
  `instance()`/`initialized()`/`clear_instance()`/`_instance` behave exactly as today.
  The ContextVar default is `None`; the entire new branch is dead code in the
  single-instance case. ipykernel poking `InteractiveShell._instance` directly still
  works — it writes the global default, which is still the fallback.

---

## 4. Alternatives considered

| # | Alternative | Pros | Cons | Verdict |
|---|---|---|---|---|
| A | **Pure parent/shell injection everywhere; no dynamic scope.** Delete `get_ipython()`-as-service-locator; thread `shell=` through all 35+ library call sites. | Most "correct"; no hidden global; testable. | Enormous breaking surface; `get_ipython()` is public API used in user cells, extensions, magics source-gen (`inputtransformer2` emits `get_ipython().run_line_magic(...)` into user_ns). Cannot delete. User code in a cell has no `shell` to inject. | **Rejected** as the *mechanism*. Adopted *partially* as the migration (§6) for internal call sites. |
| B | **Explicit Flask-style current-context stack object** (`push`/`pop`, `IPythonContext` with `_stack`). | Familiar; explicit lifecycle hooks. | Reinvents `contextvars` worse: manual thread-locality, manual async handling, manual reentrancy. `contextvars` *is* the modern, PEP-blessed version of Flask's stack (Flask itself moved to `ContextVar` in 2.0). | **Rejected** — strictly dominated by contextvars. |
| C | **`threading.local` instead of `ContextVar`.** | Simple; thread isolation. | No async-task isolation (all tasks on one thread share the local — breaks `%autoawait`/cell coroutines). No `Token` nesting. Requires manual copy for asyncio. Given IPython's asyncio integration (`async_helpers.py`, autoawait) this is a real defect. | **Rejected** — contextvars is a superset. requires-python ≥3.9 in both repos, so no availability excuse. |
| D | **Keep singleton; formalize embed's save/restore as a public CM on the class, no contextvars.** `with cls.temporary_instance(x):` that assigns `cls._instance` and restores in `finally`. | Trivial; exactly what embed does, made correct (adds the missing try/finally); no new concurrency model. | Process-global mutation: concurrent threads see the override — the exact bug §1.3 describes. Fine for *strictly single-threaded* embed, wrong as a general "multiple globals" mechanism. | **Deferred/subset** — this is literally what our CM reduces to when no other thread is active. We ship the ContextVar version; embed becomes correct as a side effect. Not shipped as a separate primitive. |
| E | **Do it entirely IPython-side, never touch traitlets.** | No traitlets coordination; fast. | Leaves `Application.instance()` / `get_config()` / traitlets `log.py:_logger` with the same latent bug; duplicated logic if traitlets ever wants it; other traitlets singletons unscoped. | **Adopted as Stage 1 only**, then upstreamed (§3). |

**Recommendation: the ContextVar overlay in traitlets, staged behind an IPython-first
shim (D-correctness for free, A applied surgically as migration).**

---

## 5. Satellite-state audit

A scoped `instance()` is a lie unless the adjacent global state is addressed. "v1" =
*scoped `.instance()`/`get_ipython()` resolution works, and single-active-shell-at-a-time
nesting (embed) is correct*. **Full concurrent multi-shell is explicitly out of scope for
v1.**

| Satellite state | Location | Coupling to "which shell" | v1 disposition |
|---|---|---|---|
| builtins `get_ipython` injection | `core/builtin_trap.py:38-44` (ref-counted nested save/restore) | High — user-cell `get_ipython()` resolves here | **Already dynamically scoped by hand.** Callers compose: `as_current` does not auto-enter traps; embed enters the target shell's `builtin_trap` as it does today. No change to BuiltinTrap itself. |
| `sys.displayhook` / `display_trap` | `interactiveshell.py`; mainloop uses `with self.display_trap` | High | Same: caller enters `shell.display_trap`. `as_current` stays a pure resolution primitive; embed composes them. |
| `__IPYTHON__` builtin flag | `interactiveshell.py:856-861` (single static flag) | Low — boolean "are we in IPython at all" | **Stays global.** Correct for nested/embedded (still "in IPython"). Documented non-goal. |
| traitlets `log.py` memoized `_logger` | `traitlets/log.py:10,21` | Medium — caches `Application.instance().log` once, stale after swap | **Known wart, left as-is in v1.** Note in docs. Fixing = make `_logger` override-aware or stop memoizing; deferred; independently landable later. |
| `HistoryManager._instances` WeakSet + `_max_inst` | `core/history.py:677-678,715-719` | Medium — guards "too many shells" | **Loosen the guard** (test_embed already bumps to 3). Not context-aware; acceptable because histories are per-shell-injected already. |
| `os.register_at_fork` hooks over `HistoryManager._instances` | `history.py:1103-1104` | Low | Stays global; iterates all live histories, correct regardless of scope. |
| `_asyncio_event_loop` module global | `core/async_helpers.py:18,44-47` ("one loop for IPython" by design) | Medium | **Stays global in v1.** Multi-shell-concurrent would need per-shell loop; out of scope. |
| `Application._instance` / `get_config()` | `application.py:1124-1132` | High for Jupyter apps | Gains scoping automatically in **Stage 2** (traitlets). Untouched in Stage 1. |

**v1 "supported" statement for the docs:** *`as_current` scopes
`instance()`/`initialized()`/`get_ipython()` resolution for the current thread and its
async tasks. To make user-executed code (cells, magics) see the scoped shell, compose
with that shell's `builtin_trap` and `display_trap` (as `embed()` does). Concurrent,
truly-parallel multiple live shells sharing one process (shared `__IPYTHON__`, single
asyncio loop, memoized logger) remain unsupported.*

---

## 6. Migration plan — ordered work items for coding agents

Legend: **IL** = independently landable (no dependency on the new mechanism);
**M** = depends on the mechanism existing.

### Phase 0 — mechanism (M, gates everything below except IL items)

**WI-0a — IPython Stage-1 shim.**
Scope: add module `ContextVar` + `as_current`/override of `instance`/`initialized` on
`InteractiveShell`; make `get_ipython()` (`core/getipython.py:16-24`) consult the
ContextVar before `initialized()/instance()`.
Files: `IPython/core/getipython.py`, `IPython/core/interactiveshell.py` (near :349-352).
Acceptance: existing test suite green; new tests —
`with shell_b.as_current(): assert get_ipython() is shell_b` and restoration after;
nested `as_current` restores LIFO; exception inside the block still restores; override
invisible to a `threading.Thread` started inside the block (asserts global shell).
IL=no.

**WI-0b — rewrite `embed()` on top of `as_current`.**
Scope: replace `terminal/embed.py:417-433` manual save/clear/restore with
`with shell.as_current():` (+ compose `builtin_trap`, `display_trap`). Gains try/finally
correctness.
Files: `IPython/terminal/embed.py`.
Acceptance: `tests/test_embed.py::test_nest_embed` passes; add a test that an exception
inside the embedded block still restores the outer `get_ipython()`. Also evaluate
dropping the :157-166 `_instance` write-through hack for #14164 if the CM subsumes it
(verify against that issue's repro). IL=no (needs WI-0a).

### Phase 1 — bug fixes, all independently landable *now* (no mechanism needed)

**WI-1 — fix missing guard in `publish_display_data`.** (Bug regardless of this project.)
Scope: `display_functions.py:65` calls `InteractiveShell.instance().display_pub` with
**no `initialized()` guard** → implicitly constructs a shell as a side effect of a
display call.
Change: guard with `initialized()`, no-op (or warn) when no shell.
Acceptance: `publish_display_data(...)` with no shell present does not construct one;
unit test asserts `InteractiveShell.initialized()` stays False. **IL=yes. Good first
item.**

**WI-2 — de-singletonize `LaTeXTool`.**
Scope: `lib/latextools.py:23` is a `SingletonConfigurable` only incidentally; call sites
`lib/latextools.py:84,218` do `LaTeXTool.instance()`.
Change: make it a plain `Configurable`; construct locally where used (or cache a
module-level default constructed from `get_ipython().config` when available). Drop the
`SingletonConfigurable` base.
Acceptance: latex rendering tests pass; `LaTeXTool` no longer appears in singleton
machinery; no `.instance()` call sites remain. **IL=yes. Good first item.**

**WI-3 — guard `debugger` fallback construction.**
Scope: `core/debugger.py:309` creates a shell after `get_ipython()` returned None.
Change: audit whether the fallback is needed; prefer using the passed
shell/`get_ipython()` and erroring cleanly rather than constructing a global.
Acceptance: debugger works with an explicit shell; does not spawn a global shell when
none exists. IL=yes.

### Phase 2 — convert service-locator call sites to injection (A, surgical)

For each: the object already receives `shell=`/`parent=` at construction (20+ subsystems
do — `interactiveshell.py:864-2824`), so prefer the injected reference over
`get_ipython()`.

**WI-4 — `core/formatters.py:288,1086`.** Module-level `format()` and formatter code use
`InteractiveShell.instance()`; formatters are constructed with `parent=shell`. Use
`self.parent`/stored shell. Acceptance: formatting tests pass; grep shows no
`.instance()` in formatters. IL=yes.

**WI-5 — `core/display_functions.py:243,269,365-366`.** `display()`/`clear_output()`
already `initialized()`-guarded; leave resolution via `get_ipython()` but ensure it's the
*scoped* one (automatic once WI-0a lands). Classify: **keep-on-top-of-mechanism.**
Acceptance: display in an `as_current` block targets the scoped shell's `display_pub`.
M=yes.

**WI-6 — batch: `terminal/shortcuts/*`, `lib/demo.py`, `lib/guisupport.py`,
`lib/backgroundjobs.py`, `lib/editorhooks.py`, `core/page.py:256`,
`core/completerlib.py`, `core/tbtools.py:185`, `core/ultratb.py:396,846`,
`utils/capture.py:152`.** These call module-level `get_ipython()`. **Keep as-is** — they
become scoped automatically via WI-0a. No code change; just add to a regression test that
they see the scoped shell. Split into ~3 agent work-items by directory. M=yes, but
zero-diff (verification only).

**WI-7 — `core/magic.py:238-250` frame-walking `get_ipython`.** Third lookup variant that
scans caller frames. Evaluate replacing with the scoped `get_ipython()`. Acceptance:
magics resolve shell without frame walking; behavior unchanged under embed nesting.
M=yes.

### Phase 3 — traitlets upstream (Stage 2)

**WI-8 — land mechanism in `SingletonConfigurable`** (§2.3). Files:
`traitlets/config/configurable.py`. Acceptance: existing
`tests/config/test_configurable.py:315-339,:588-634` and
`test_application.py:599-632` pass unchanged; new tests mirror WI-0a for a toy
`SingletonConfigurable` and for the `Bar`/`Bam` ancestor-scoping case. IL=yes
(traitlets-local).

**WI-9 — remove IPython Stage-1 override**, inherit from traitlets; bump `traitlets>=`
floor. Acceptance: full IPython suite green against new traitlets. M=yes (needs WI-8
released).

**WI-10 — `Application`/`get_config()` scoping test** (`application.py:1124`) and
optional fix of `log.py:_logger` memoization. IL=yes (traitlets-local, low priority).

### Ordering summary

Phase 1 (WI-1, WI-2, WI-3) can land **today, in parallel, by independent agents**.
Phase 0 (WI-0a → WI-0b) gates Phase 2. Phase 3 is a separate traitlets track that can
proceed in parallel with Phase 2 and merges via WI-9.

---

## 7. Open questions for the maintainer

1. **Auto-create form:** keep the classmethod `scoped_instance(**kwargs)` (constructs via
   `cls(**kwargs)`, never `instance()`, global untouched), or require callers to always
   construct explicitly and use only `inst.as_current()`?
2. **API name:** `as_current` (reads well: `with shell.as_current():`) vs
   `override_instance`/`scoped`. Also: expose a public IPython-level free-function alias
   in `IPython.core.getipython`?
3. **Should `as_current` auto-enter `builtin_trap`/`display_trap`** (convenient, but
   couples the resolution primitive to IPython trap machinery and can't live in
   traitlets), or stay a pure resolver that embed composes explicitly? Recommendation:
   pure resolver.
4. **Loosen `HistoryManager._max_inst`** globally, or keep it conftest-only?
   test_embed already bumps it to 3.

## 8. Risks

- **Thread non-inheritance surprises.** A user who spawns a raw `threading.Thread` inside
  `as_current` and calls `get_ipython()` gets the *global* shell, not the scoped one.
  Mitigated by design intent (fallback-to-global is the safe default, never None) and by
  documentation. Anyone needing propagation uses `contextvars.copy_context()`.
- **Third-party `_instance` pokers.** ipykernel and older embed code assign/read
  `InteractiveShell._instance` directly. Because the ContextVar defaults to None and
  falls through to `_instance`, direct pokes still work in the single-instance case. The
  one hazard: code that pokes `_instance` *expecting* to override resolution *inside* an
  `as_current` block will be silently shadowed by the ContextVar. Niche; document that
  `as_current` wins over direct `_instance` assignment.
- **Pickling / serialization.** ContextVars and the override dict are process-local and
  never pickled. Shells aren't pickled. No new surface, but note: a scoped instance
  captured in a closure/`copy_context()` extends its lifetime.
- **GC / lifecycle of scoped instances.** The override holds a strong ref for the block's
  duration only (`reset(token)` drops it). A `copy_context()` taken inside the block
  (e.g. by `asyncio.create_task`) keeps the instance alive until that context is
  collected — expected, matches asyncio semantics. `as_current` does **not** call
  `clear_instance()` on exit, so it never disturbs the global.
- **`MultipleInstanceError` semantics under override.** A base-class `instance()` call
  inside a subclass override where types are incompatible now raises from the override
  branch too — behavior preserved, but the error message differs ("active as a scoped
  override"); ensure downstream error-string matchers (if any) aren't pinned.

---

## Appendix A — supporting inventory (verified facts)

### traitlets

- `SingletonConfigurable` at `traitlets/config/configurable.py:517`; `_instance = None`
  (line 525); `instance()` (553-595), `clear_instance()` (542-551), `initialized()`
  (597-600), `_walk_mro()` (527-540). `_instance` is read/written **only** inside these
  four methods — a fully encapsulated single point of truth.
- No locking anywhere; TOCTOU race under threads; no reentrancy guard for construction.
- `Application` (`application.py:152`) is traitlets' only production
  `SingletonConfigurable`; `launch_instance()` (1074-1082) is the canonical entry;
  `initialize_subcommand` (699-722) does `clear_instance()` + `subapp.instance(parent=self)`.
- Hidden second global: `traitlets/log.py:get_logger()` memoizes into module-level
  `_logger` on first call, independent of singleton bookkeeping — stale after clear/swap.
- requires-python ≥3.9; `instance()` typed `(cls: type[CT], ...) -> CT`; mypy-checked.

### IPython

- Direct `SingletonConfigurable` subclasses: **2** — `InteractiveShell`
  (`core/interactiveshell.py:349`, redeclares `_instance = None` at 352) and `LaTeXTool`
  (`lib/latextools.py:23`, incidental). Plus ~9 `Application` subclasses
  (`TerminalIPythonApp`, `BaseIPythonApplication`, profile/history apps).
- `.instance()` production call sites: 5+2 bootstrap (`ipapp.py:300`, `embed.py:423`,
  `terminal/interactiveshell.py:1142`, `sphinxext/ipython_directive.py:366`,
  `testing/globalipapp.py:69`, `testing/ipunittest.py:91`, `docs/autogen_magics.py:7`);
  4 unguarded service-locator (`latextools.py:84,218`, `formatters.py:1086`,
  `display_functions.py:65`, `debugger.py:309`); 5 guarded `initialized()` patterns
  (`getipython.py:22`, `display_functions.py:243/269/365`, `magics/pylab.py:146`,
  `crashhandler.py:237`).
- `get_ipython()` has two parallel paths: (1) instance-bound
  `InteractiveShell.get_ipython(self) -> self` injected into builtins via `BuiltinTrap`
  and into user_ns — already dynamically scoped by hand; (2) module-level
  `core/getipython.py` singleton path used by ~35+ library call sites.
  `core/magic.py:238-250` is a third variant (frame walking).
- Prior art: `embed()` (`terminal/embed.py:417-433`) manually saves/clears/restores
  `_instance` with **no try/finally**; `tests/test_embed.py::test_nest_embed` proves
  nesting works today.
- "One at a time" assumptions: `interactiveshell.py:856-861` comment;
  `HistoryManager._instances`/`_max_inst` (`history.py:677,715`); `register_at_fork`
  hooks (`history.py:1103`); `_asyncio_event_loop` (`async_helpers.py:18,44`).
  Zero `contextvars` usage in either repo today.
- Injection already dominates: 20+ subsystems receive `shell=`/`parent=` at construction;
  ipykernel's extension seam (`displayhook_class`, `display_pub_class` Type traits) is
  parent-injection too.
