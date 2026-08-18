Most builtin magics are now registered lazily
----------------------------------------------

Previously, ``init_magics`` imported and instantiated every builtin
``Magics`` class up front, including ``IPython.core.magics.execution``,
``.namespace``, ``.osm``, ``.history``, ``.display``, ``.packaging``,
``.pylab``, ``.script``, ``.code`` and ``.logging`` -- pulling in things like
``pdb``, ``timeit``, ``subprocess`` machinery and more before a single cell
had run.

These modules are now registered via
:attr:`~IPython.core.magic.MagicsManager.lazy_magics`, the same mechanism
already used for user/config supplied lazy magics, and are only imported the
first time one of their magics (``%run``, ``%time``, ``%%bash``, ``%history``,
``%pip``, ...) is actually used -- whether typed explicitly, via automagic, as
a magic alias (e.g. ``%hist``), or through ``%alias_magic``. Tab completion
still lists these magics (and their line/cell kind) without importing them.

A handful of magics that are needed unconditionally during shell startup, or
that are already essentially free to import, are still registered eagerly:
``AutoMagics``, ``BasicMagics``, ``ConfigMagics``, ``ExtensionMagics`` and
``AsyncMagics``.
