"""
Enable Gtk4 to be used interactively by IPython.
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2021, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import sys

from gi.repository import GLib

# -----------------------------------------------------------------------------
# Code
# -----------------------------------------------------------------------------


class _InputHook:
    def __init__(self, context):
        self._quit = False
        GLib.io_add_watch(sys.stdin, GLib.PRIORITY_DEFAULT, GLib.IO_IN, self.quit)

    def quit(self, *args, **kwargs):
        self._quit = True
        return False

    def run(self):
        context = GLib.MainContext.default()
        while not self._quit:
            context.iteration(True)


def inputhook_gtk4():
    hook = _InputHook()
    hook.run()
    return 0
