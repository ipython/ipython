Disable filename abbreviations in tab-completion with ``min_elide=0``
======================================================================

Setting ``c.TerminalInteractiveShell.min_elide = 0`` now completely disables
path elision in tab-completion output. Previously, the elision functions would
still attempt to shorten long paths even when configured to do so. This allows
users who prefer to see full completion paths to disable abbreviations entirely.
