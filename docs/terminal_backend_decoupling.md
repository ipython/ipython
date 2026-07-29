# Decoupling the terminal frontend from prompt_toolkit

Working design note. Not a commitment to replace prompt_toolkit — the goal is
to make it *a* backend rather than *the* implementation, so alternatives can be
prototyped behind a flag and so prompt_toolkit's API stops leaking into
user-facing configuration.

## Why now

There is no drop-in replacement today. `_pyrepl` (CPython 3.13+) is the only
serious candidate and it is private, undocumented, and architecturally not
separable — `multiline_input()` is a method on an instance welded to `Console`
and `Reader`. Everything else (ptpython, pymux, mypython) *is* prompt_toolkit;
the C/Rust line editors (replxx, reedline, linenoise) have no maintained Python
bindings and no story for async or GUI event-loop integration.

So the near-term win is not the swap. It is that:

1. The `prompt_toolkit:` prefix currently appears in documented user config
   (`c.TerminalInteractiveShell.shortcuts`), which makes any future swap a
   breaking change rather than an implementation detail. That is worth undoing
   regardless of what we eventually run on.
2. A backend seam lets us ship an opt-in `_pyrepl` backend as an experiment,
   which is the concrete artifact needed to make the upstream case for a public
   `pyrepl` API. Core devs' stated objection is the maintenance burden of a new
   public surface; a real consumer answers that.
3. `simple_prompt` already *is* a second backend — a five-line `input()` loop at
   `IPython/terminal/interactiveshell.py:783-797`. The seam exists, it is just
   in the wrong place and only covers one of the seven coupling surfaces.

## Inventory of the coupling

Seven distinct surfaces, in rough order of replacement cost.

| # | Surface | Call sites | Cost |
|---|---|---|---|
| 1 | Session construction and per-prompt options | `interactiveshell.py:811-825`, `:882-931`, `debugger.py:74-90` | low |
| 2 | Content providers (completer, lexer, history, auto-suggest) | `ptutils.py:102`, `ptutils.py:201`, `interactiveshell.py:168`, `shortcuts/auto_suggest.py:200-205` | medium |
| 3 | Live-mutable settings written from traitlet observers | `interactiveshell.py:330`, `:543`, `:629` | low |
| 4 | Editing state read back out of the session | `prompts.py:24-26`, `:35-36`, `:130-132`, `interactiveshell.py:1116-1118` | low |
| 5 | Keybindings, filters, and the command namespace | `shortcuts/__init__.py`, `shortcuts/filters.py` | **high — user-visible** |
| 6 | Event loop / inputhook integration | `interactiveshell.py:946-962`, `pt_inputhooks/` (8 files) | **high — nothing else does this** |
| 7 | Output helpers (`patch_stdout`, `print_formatted_text`) | `interactiveshell.py:946`, `:1117`, `prompts.py:131` | medium |

Surfaces 1–4 and 7 are mechanical. Surfaces 5 and 6 are the actual project.

### Surface 5 in detail — why it is user-visible

`c.TerminalInteractiveShell.shortcuts` takes command identifiers as literal
strings, and the documented examples in the trait's own help text
(`interactiveshell.py:611`, `:616`) are:

```python
c.TerminalInteractiveShell.shortcuts = [
    {"new_keys": ["c-q"], "command": "prompt_toolkit:named_commands.capitalize_word", "create": True},
]
```

`create_identifier()` (`shortcuts/__init__.py:64`) derives these from
`handler.__module__`, so every binding that happens to live in prompt_toolkit
gets a `prompt_toolkit:` identifier automatically. Users have these in their
config files. `_merge_shortcuts` (`interactiveshell.py:634`) validates against
an allow-list built the same way (`interactiveshell.py:632`).

Alongside it, `KEYBINDING_FILTERS` and `filter_from_string`
(`shortcuts/filters.py:317`) define a small boolean DSL over prompt_toolkit
`Condition` objects, also referenced by name from config.

Any backend swap has to keep both of these working, which means IPython needs
to own the command namespace and the filter vocabulary before it can own the
backend.

### Surface 6 in detail — why it is the hard one

`prompt_for_code` (`interactiveshell.py:933-964`) has two paths:

- **asyncio integrated**: `asyncio_loop.run_until_complete(pt_app.prompt_async(...))`,
  so user coroutines and the prompt share one loop.
- **everything else**: `pt_app.prompt(inputhook=self._inputhook, ...)`, where
  `_inputhook` is one of the eight GUI integrations in `pt_inputhooks/`
  (qt, wx, gtk/gtk3/gtk4, glut, pyglet, osx, tk).

The inputhook contract is "call this callable while idle, and stop when this
file descriptor becomes readable" — prompt_toolkit exposes it as
`InputHookContext.fileno()` / `input_is_ready()`. No other line editor exposes
an equivalent hook. `_pyrepl` has no concept of it at all. This is the surface
that determines whether a candidate backend is viable for `%gui`, and it should
be the *first* thing prototyped against any alternative, not the last.

`patch_stdout` (surface 7) is adjacent: it is what keeps background-thread
output from corrupting the prompt, and it is equally prompt_toolkit-specific.

## Sketch of the interface

Proposed home: `IPython/terminal/backends/`, with `prompt_toolkit_backend.py`
and `simple_backend.py` as the initial two implementations.

```python
class TerminalInputBackend(Protocol):
    """What TerminalInteractiveShell needs from a line editor."""

    # --- lifecycle ---------------------------------------------------
    @classmethod
    def create(cls, shell: TerminalInteractiveShell) -> Self:
        """Build a session from the shell's traits and providers."""

    def close(self) -> None: ...

    # --- the calls interact() makes ----------------------------------
    def prompt_for_code(self, default: str = "", *, inputhook=None) -> str: ...
    async def prompt_for_code_async(self, default: str = "") -> str: ...

    # --- settings pushed in when traits change (surface 3) -----------
    def set_editing_mode(self, mode: Literal["emacs", "vi"]) -> None: ...
    def set_auto_suggest(self, provider: AutoSuggestProvider | None) -> None: ...
    def set_key_bindings(self, bindings: Sequence[ResolvedBinding]) -> None: ...
    def set_style(self, style: Style) -> None: ...

    # --- state read back out (surface 4) -----------------------------
    @property
    def vi_input_mode(self) -> str | None:
        """For the `[ins]`/`[nav]` prompt segment; None if not in vi mode."""

    @property
    def cursor_position_row(self) -> int:
        """For prompt_line_number_format."""

    # --- output (surface 7) ------------------------------------------
    def print_tokens(self, tokens: list[tuple[Token, str]], *, end: str = "\n") -> None:
        """Styled output using the session's own style object."""

    @contextmanager
    def patch_stdout(self) -> Iterator[None]:
        """Keep background output from corrupting the prompt."""
```

Content providers (surface 2) go the other direction — the shell supplies
backend-neutral objects and each backend adapts them:

```python
class CompletionProvider(Protocol):
    def completions(self, text: str, cursor_pos: int) -> Iterable[CompletionItem]: ...

class HighlightProvider(Protocol):
    def tokens_for_line(self, line: str) -> list[tuple[Token, str]]: ...

class HistoryProvider(Protocol):
    def load(self) -> Iterable[str]: ...
    def append(self, entry: str) -> None: ...
```

`IPythonPTCompleter` and `IPythonPTLexer` (`ptutils.py:102`, `:201`) then become
thin prompt_toolkit adapters over these, rather than the interface itself. Note
that `IPythonPTCompleter` already does the real work in `_get_completions`
(`ptutils.py:139`) and only wraps it in `Completion` objects at the boundary —
the split is close to free.

Deliberately **not** in the protocol:

- Anything about layout, processors, or `input_processors`. Bracket matching
  and inline auto-suggestion rendering become backend capabilities that degrade
  to no-ops, queried via a `capabilities` set rather than assumed.
- `mouse_support`, `color_depth`, `complete_style`. These stay as shell traits
  and are consumed by `create()`; a backend that cannot honour one ignores it.

## Staged plan

Each stage is independently shippable, non-breaking, and useful on its own even
if the next stage never happens.

**Stage 0 — freeze the leak.** Add IPython-owned aliases for every
`prompt_toolkit:named_commands.*` identifier currently reachable from config
(e.g. `ipython:capitalize_word`), document those instead, and keep the
`prompt_toolkit:` spellings working as deprecated aliases. This is the only
stage with a deprecation cycle attached, so it should start first and run in
the background while everything else proceeds.

**Stage 1 — introduce the package.** Create `IPython/terminal/backends/` with
the Protocol above and `PromptToolkitBackend` as a straight lift of the current
code. `init_prompt_toolkit_cli` becomes `init_terminal_backend`, keeping the old
name as an alias. `self.pt_app` stays exactly where it is, populated by the
prompt_toolkit backend. No behaviour change, no deprecations.

**Stage 2 — move `simple_prompt` behind it.** Turn the `input()` loop at
`interactiveshell.py:783-797` into `SimpleBackend`. This validates the Protocol
against a genuinely different implementation for free, and it is the one case
where we already know the answer. Expect this to shake out one or two
assumptions in the sketch above (most likely around `print_tokens` and the
absent `vi_input_mode`).

**Stage 3 — invert the providers.** Split `IPythonPTCompleter` and
`IPythonPTLexer` into neutral core + prompt_toolkit adapter. Same for
`PtkHistoryAdapter`. Mostly moving code.

**Stage 4 — own the binding model.** Make `Binding`/`RuntimeBinding`
(`shortcuts/__init__.py:39-61`) backend-neutral dataclasses, and make
`filter_from_string` produce IPython predicates that each backend wraps in its
own condition type. `create_ipython_shortcuts` returns a list of
`ResolvedBinding`, and the prompt_toolkit backend converts to `KeyBindings`.
This is where Stage 0's alias work pays off.

**Stage 5 — prototype a second real backend.** Only now is `_pyrepl` worth
attempting, and it should start with a single question: can it be driven with an
inputhook, or under an asyncio loop, at all? If the answer is no, the prototype
stops there and we have learned the useful thing cheaply. If yes, it ships as
`c.TerminalInteractiveShell.backend = "pyrepl"`, explicitly experimental, and
becomes the artifact for the upstream public-API conversation.

## Compatibility surface to keep working

Things outside IPython that reach into prompt_toolkit through us, and which any
staging has to preserve:

- `ip.pt_app` — documented in `docs/source/config/details.rst:365,387` and used
  in `examples/auto_suggest_llm.py:93` to add key bindings at runtime. Must keep
  returning a real `PromptSession` for as long as the prompt_toolkit backend is
  the default.
- `TerminalPdb(pt_session_options=...)` (`debugger.py:27`) — kwargs forwarded
  verbatim to `PromptSession`. madbg and similar debuggers rely on this, along
  with the `create_app_session()` handling at `debugger.py:100`.
- `c.TerminalInteractiveShell.shortcuts` command strings and filter names, per
  Stage 0.
- The `pt_inputhooks` entry points — third-party GUI integrations register here.

## Open questions

- Does the `capabilities` set belong on the backend class or on the instance?
  Instance is more honest (colour depth is terminal-dependent) but harder to
  introspect for docs.
- `prompts.py` reaches into `pt_app.app.style` to print styled text. Should
  `print_tokens` own style resolution entirely, or should the backend expose a
  style object? Owning it is cleaner but means the shell can no longer hand a
  style to arbitrary prompt_toolkit code.
- Whether `TerminalPdb` gets its own backend instance or shares the shell's.
  Currently separate (`debugger.py:90`), and the threading model there
  (`cmdloop` runs `_prompt` in a `ThreadPoolExecutor`) may not transfer to a
  backend that is not thread-safe.
