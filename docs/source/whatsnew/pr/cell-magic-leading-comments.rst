Cell magics after leading comments
==================================

A comment (or blank line) above a cell magic is now ignored, so a cell like::

    # setup
    %%time
    pass

runs the cell magic instead of failing with a "line magic not found" error.
