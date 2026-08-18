Themes are now declarative data, and installable
================================================

The bundled themes used to be Python dictionaries mapping pygments token
objects to style strings, built when :mod:`IPython.utils.PyColorize` was
imported. They are now JSON files, read only when a theme is looked up, with
token types written as dotted paths: ``Token.Prompt.Continuation.L1`` becomes
``"Prompt.Continuation.L1"``. The themes themselves are unchanged.

This means a theme no longer has to be part of IPython. A JSON file dropped in
``themes/`` inside your IPython directory is picked up under the file's name,
so ``~/.ipython/themes/my-theme.json`` gives you ``%colors my-theme`` with no
code to write, and a package can ship themes by advertising them in the new
``ipython.themes`` entry point group.

Since a theme can now arrive from elsewhere, it is validated before it loads
and refused with a warning if it fails: token paths must name tokens, and
symbols must be printable and at most 20 characters, so that a theme cannot
write an escape sequence to your terminal.

``theme_table`` is now a lazy :class:`~collections.abc.Mapping` rather than a
plain ``dict``; looking themes up by name, iterating it and calling ``.keys()``
work as before, but it can no longer be mutated. The individual themes are no
longer module-level objects in ``IPython.utils.PyColorize``; use
``theme_table["linux"]`` rather than ``PyColorize.linux_theme``.

See :ref:`the theme documentation <termcolour>` for the file format.
