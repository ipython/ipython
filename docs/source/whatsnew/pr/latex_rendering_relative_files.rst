Relative filenames in Latex rendering
=====================================

The input and output file arguments to `latex` and `dvipis` are files relative to the current working directory.
This solves a problem where the current working directory contains characters that are not handled properly by `latex` and `dvips`.

