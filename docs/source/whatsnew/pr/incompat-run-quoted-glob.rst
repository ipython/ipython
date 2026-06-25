Quoted arguments to ``%run`` no longer undergo glob expansion
-------------------------------------------------------------

Wrapping a ``%run`` argument in single or double quotes now suppresses glob
expansion of that argument, matching real shells. Previously quoting was
documented as *not* suppressing expansion which was suprising.

For example with ``foo.txt`` and ``bar.txt`` in the working directory::

    %run script.py "*.txt"    # before: ['foo.txt', 'bar.txt']
                              # after:  ['*.txt']

The unquoted form (``%run script.py *.txt``) and the backslash-escape form
(``%run script.py \*.txt``) are unchanged. Pass ``-G`` to disable expansion
entirely.

See :ghissue:`12726`.
