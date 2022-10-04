Autoreload verbosity
====================

We introduce more descriptive names for the `%autoreload` parameter:
- `%autoreload now` (also `%autoreload`) - perform autoreload immediately.
- `%autoreload off` (also `%autoreload 0`) - turn off autoreload.
- `%autoreload explicit` (also `%autoreload 1`) - turn on autoreload only for modules
   whitelisted by `%aimport` statements.
- `%autoreload all` (also `%autoreload 2`) - turn on autoreload for all modules except those
  blacklisted by `%aimport` statements.
- `%autoreload complete` (also `%autoreload 3`) - all the fatures of `all` but also adding new
  objects from the imported modules (see
  IPython/extensions/tests/test_autoreload.py::test_autoload_newly_added_objects).

The original designations (e.g. "2") still work, and these new ones are case-insensitive.

The parsing logic for `%aimport` is now improved such that modules can be whitelisted and
blacklisted in the same line, e.g. it's now possible to call `%aimport os, -math` to include `os`
for `%autoreload explicit` and exclude `math` for modes 2 and 3.

A new magic command `%averbose` controls printing of the names of modules about to be autoreloaded.
- `%averbose off` / `%averbose 0` - turns off all output (default behavior)
- `%averbose on` / `%averbose 1`  - uses `print` to display module name
- `%averbose log` / `%averbose 2` - logs an `INFO` message with the module name

