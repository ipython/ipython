Empty History Ranges
====================

A number of magics that take history ranges can now be used with an empty
range. These magics are:

 * ``%save``
 * ``%load``
 * ``%pastebin``
 * ``%pycat``

Using them this way will make them take the history of the current session up
to the point of the magic call (such that the magic itself will not be
included).

Therefore it is now possible to save the whole history to a file using simple
``%save <filename>``, load and edit it using ``%load`` (makes for a nice usage
when followed with :kbd:`F2`), send it to dpaste.org using ``%pastebin``, or
view the whole thing syntax-highlighted with a single ``%pycat``.
