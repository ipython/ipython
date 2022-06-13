Relative filenames in Latex rendering
=====================================

The `latex_to_png_dvipng` command internally generates input and output file arguments to `latex` and `dvipis`. These arguments are now generated as relative files to the current working directory instead of absolute file paths.
This solves a problem where the current working directory contains characters that are not handled properly by `latex` and `dvips`.
There are no changes to the user API.

