More startup work moved off the critical path
---------------------------------------------

A second pass over what IPython does before it can show a prompt, on top of the
lazy imports and lazy magic registration. Nothing here is visible in normal
use; it is all work that used to happen on every start and is now either
avoided or postponed until something actually needs it.

* Resolving a theme's base pygments style no longer imports
  :mod:`pygments.styles`, and with it the pygments plugin machinery,
  :mod:`importlib.metadata` and :mod:`email`. Only the base style's ``styles``
  mapping was ever used, so for the builtin styles IPython's own themes are
  based on the defining module is read directly. Styles that are not builtin --
  including any provided by a pygments plugin -- still resolve exactly as
  before.

* Detecting whether the terminal speaks the kitty graphics protocol no longer
  imports psutil on Linux. The walk up the process tree needs each ancestor's
  name and parent pid, and ``/proc/<pid>/stat`` has both. macOS still uses
  psutil. This one only ever showed up in an actual terminal: a headless
  ``ipython -c ...`` stops at the ``isatty`` check before reaching it. Setting
  ``IPYTHON_KITTY_GRAPHICS`` still skips detection entirely.

* The prompt style is built the first time it is drawn rather than each of the
  several times it is invalidated while a shell is being set up, and not at all
  for a run that never draws a prompt.

* More single-use imports moved to their use sites: :mod:`platform`,
  :mod:`pprint`, :mod:`textwrap`, :mod:`html`, :mod:`mimetypes`,
  :mod:`locale`, :mod:`glob` and :mod:`runpy`. The AST operator tables the
  terminal shortcut filters need moved out of
  :mod:`IPython.core.guarded_eval` into a module of their own, so evaluating
  a shortcut's filter expression no longer imports the whole guarded
  evaluation machinery (and ``typing_extensions``). They are still importable
  from :mod:`IPython.core.guarded_eval`.

Together this takes another ~13% off starting an interactive ``ipython`` in a
real terminal, ~9% off ``ipython -c pass``, and another ~43 modules off an
interactive start, on top of the previous rounds.
