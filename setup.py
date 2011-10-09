#!/usr/bin/env python
"""This calls the setup routine for Python 2 or 3 as required."""

import sys

if sys.version_info[0] >= 3:
    from setup3 import main
else:
    from setup2 import main

main()
