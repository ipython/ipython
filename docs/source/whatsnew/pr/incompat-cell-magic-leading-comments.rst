Cell magics after leading comments
----------------------------------

A cell magic can now follow comment-only and blank lines at the beginning of a
cell. For example::

    # Measure this cell
    %%time
    pass

The leading comments and blank lines are ignored, and the remaining cell is
passed to the cell magic. Comments and blank lines in its body are preserved.
This also works when pasting input with Python or IPython prompts.

Previously, a cell like this attempted to invoke a line magic whose name began
with ``%``. Code that registers such a line magic programmatically should use
``get_ipython().run_line_magic()`` explicitly for this case. Ordinary Python
cells and single-percent line magics keep their leading comments.
