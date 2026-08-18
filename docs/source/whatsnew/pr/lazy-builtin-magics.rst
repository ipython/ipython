IPython's own magics are now declared lazily. Starting a shell used to import
all fifteen modules under :mod:`IPython.core.magics` and instantiate every
:class:`~IPython.core.magic.Magics` class in them, even though a session
typically uses a handful of magics at most. Only the magic *names* are now known
up front, from a hand-maintained table in ``IPython.core.magics._table``, and the
module implementing a magic is imported the first time it is looked up. This
takes roughly 25 ms off ``import IPython`` and shell startup.

This reuses :attr:`~IPython.core.magic.MagicsManager.lazy_magics`, which already
existed for extensions, so third-party code can declare its magics the same way::

    shell.magics_manager.register_lazy("my_magic", "my_package.magics:MyMagics")

Its values may now be either ``"package.module"``, loaded as an IPython extension
as before, or ``"package.module:MagicsClass"``, imported and registered directly.
Unlike before, a magic declared through
:meth:`~IPython.core.magic.MagicsManager.register_lazy` shows up in ``%lsmagic``
and in completion right away rather than only after its first use.

Until a magic is loaded, ``shell.magics_manager.magics[kind][name]`` holds a
:class:`~IPython.core.magic.LazyMagic` placeholder. Calling it, or reading any
attribute of it, loads and delegates to the real magic, so existing code that
reaches into that table keeps working. A magics class only appears in
``shell.configurables`` once loaded; ``%config`` loads everything first, so the
list of configurable classes it shows is unchanged.
