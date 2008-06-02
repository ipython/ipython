#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" IPykit launcher

w/o args, this launches a full ipykit session.

If the first arg is a .py script, it will be run WITHOUT ipython,
to facilitate running python scripts almost normally on machines w/o python
in their own process (as opposed to %run).

"""

import sys
if len(sys.argv) > 1 and sys.argv[1].endswith('.py'):
    # shortcut for running ipykit.exe directly on a .py file - do not bother
    # starting ipython, just handle as normal python scripts
    sys.argv = sys.argv[1:]
    execfile(sys.argv[0])
else:
    import IPython  
    IPython.Shell.start().mainloop()
