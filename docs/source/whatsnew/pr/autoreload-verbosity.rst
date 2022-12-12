Autoreload verbosity
====================

We introduce more descriptive names for the ``%autoreload`` parameter:

- ``%autoreload now`` (also ``%autoreload``) - perform autoreload immediately.
- ``%autoreload off`` (also ``%autoreload 0``) - turn off autoreload.
- ``%autoreload explicit`` (also ``%autoreload 1``) - turn on autoreload only for modules
  whitelisted by ``%aimport`` statements.
- ``%autoreload all`` (also ``%autoreload 2``) - turn on autoreload for all modules except those
  blacklisted by ``%aimport`` statements.
- ``%autoreload complete`` (also ``%autoreload 3``) - all the fatures of ``all`` but also adding new
  objects from the imported modules (see
  IPython/extensions/tests/test_autoreload.py::test_autoload_newly_added_objects).

The original designations (e.g. "2") still work, and these new ones are case-insensitive.

Additionally, the option ``--print`` or ``-p`` can be added to the line to print the names of
modules being reloaded. Similarly, ``--log`` or ``-l`` will output the names to the logger at INFO
level. Both can be used simultaneously.

The parsing logic for ``%aimport`` is now improved such that modules can be whitelisted and
blacklisted in the same line, e.g. it's now possible to call ``%aimport os, -math`` to include
``os`` for ``%autoreload explicit`` and exclude ``math`` for modes ``all`` and ``complete``.


