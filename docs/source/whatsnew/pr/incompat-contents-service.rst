- The NotebookManager and ``/api/notebooks`` service has been replaced by
  a more generic ContentsManager and ``/api/contents`` service,
  which supports all kinds of files.
- The Dashboard now lists all files, not just notebooks and directories.
- The ``--script`` hook for saving notebooks to Python scripts is removed,
  use ``ipython nbconvert --to python [notebook]`` instead.
