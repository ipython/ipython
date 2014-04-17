# encoding: utf-8
"""
Enable Clutter to be used interacive by IPython.

Authors: Thomas Schüßler
"""
#-----------------------------------------------------------------------------
# Copyright (c) 2012, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import sys
from gi.repository import Clutter, GLib

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------


def _main_quit(*args, **kwargs):
    Clutter.main_quit()
    return False


def inputhook_clutter():
    GLib.io_add_watch(sys.stdin, GLib.IO_IN, _main_quit)
    Clutter.main()
    return 0
