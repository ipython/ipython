The ``%%script`` (as well as ``%%bash``, ``ruby``... ) cell magic no raise by
default if the return code of the given code is non-zero (this halting execution
of further cells in a notebook). The behavior can be disable by passing the
``--no-raise-error`` flag.
