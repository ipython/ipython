# Deprecation, modernization, and performance changes — July 2026

Cleanup batch for the IPython codebase at 9.16.0.dev (Python floor: 3.11).

## Deprecated APIs removed

| Item | Deprecated in |
|---|---|
| `IPCompleter.limit_to__all__` trait | 5.0 |
| `IPCompleter.python_matches` | 8.27 |
| `OInfo.get()` | 8.13 |
| `pylabtools.backends` / `backend2gui` module `__getattr__` | 8.24 |
| `run_cell_async` / `should_run_async` auto-transform fallback (now `TypeError`) | 7.17 |

## Modernization

- Dropped the `decorator` runtime dependency (3 uses rewritten with
  `functools.wraps`, typed with `ParamSpec`; `types-decorator` removed from
  extras and mypy CI).
- Collapsed the `typing_extensions` conditional import in `completer.py`
  (everything there is stdlib `typing` on 3.11). `typing_extensions` is still
  needed on 3.11 for `TypeAliasType` in `guarded_eval.py`.
- Deleted dead `setup.cfg` (black config in INI syntax that black never read);
  the exclusion now lives in `[tool.black]` in `pyproject.toml`.
- Fixed `LineInfo.ofind` docstring/warning version mismatch (both now say 9.9).

## Performance

- **Lazy jedi import**: `completer.py` imported jedi (and transitively parso,
  which compiles grammars) at module import time, i.e. on every
  `import IPython`. Now deferred to first completion via `_get_jedi()`;
  `JEDI_INSTALLED` uses `importlib.util.find_spec`. Measured warm (median of
  3 runs in the dev container): `import IPython` ~340ms → ~277ms (~60ms,
  ~17%).
- Hoisted per-call `re.compile` to module level: `global_matches` snake-case
  regex (ran on every completion request), two colder completer regexes, five
  `format_latex` regexes in `magic.py`.
- Fixed memory retention in `debugger.py`: `@lru_cache(1024)` on instance
  methods keyed by frame objects kept every Pdb instance and up to 1024 frames
  (with locals and back-chains) alive for the process lifetime. Now
  per-instance, size-bounded caches cleared on each `interaction`.
- Bounded the unbounded `count_lines_in_py_file` lru_cache in `tbtools.py`.
- Fixed a latent import cycle in `IPython.terminal`
  (`interactiveshell` → `debugger` → `embed` → `interactiveshell`):
  `terminal/debugger.py` now imports `terminal.embed` inside `do_interact`,
  the only place it's used, instead of at module level.
