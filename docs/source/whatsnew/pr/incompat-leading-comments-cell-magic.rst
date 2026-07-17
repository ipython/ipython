Leading comments before cell magics
===================================

Leading comments and blank lines are ignored before a cell magic, so a cell
such as ``# setup`` followed by ``%%time`` is treated as a cell magic instead
of an invalid line magic.
