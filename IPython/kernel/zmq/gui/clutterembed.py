"""GUI support for the IPython ZeroMQ kernel - GTK toolkit support.
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2010-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING.txt, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
# stdlib
import sys

# Third-party
from gi.repository import Clutter, GObject

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------


class ClutterEmbed(object):
    """A class to embed a kernel into the Clutter main event loop.
    """
    def __init__(self, kernel):
        self.kernel = kernel
        # These two will later store the real Clutter functions when we hijack them
        self.clutter_main = None
        self.clutter_main_quit = None

    def start(self):
        """Starts the Clutter main event loop and sets our kernel startup routine.
        """
        # Register our function to initiate the kernel and start Clutter
        GObject.idle_add(self._wire_kernel)
        Clutter.main()

    def _wire_kernel(self):
        """Initializes the kernel inside Clutter.

        This is meant to run only once at startup, so it does its job and
        returns False to ensure it doesn't get run again by Clutter.
        """
        self.clutter_main, self.clutter_main_quit = self._hijack_clutter()
        GObject.timeout_add(int(1000*self.kernel._poll_interval),
                            self.iterate_kernel)
        return False

    def iterate_kernel(self):
        """Run one iteration of the kernel and return True.

        Clutter timer functions must return True to be called again, so we make the
        call to :meth:`do_one_iteration` and then return True for Clutter.
        """
        self.kernel.do_one_iteration()
        return True

    def stop(self):
        # FIXME: this one isn't getting called because we have no reliable
        # kernel shutdown.  We need to fix that: once the kernel has a
        # shutdown mechanism, it can call this.
        self.clutter_main_quit()
        sys.exit()

    def _hijack_clutter(self):
        """Hijack a few key functions in Clutter for IPython integration.

        Modifies Clutters main and main_quit with a dummy so user code does not
        block IPython.  This allows us to use %run to run arbitrary Clutter
        scripts from a long-lived IPython session, and when they attempt to
        start or stop

        Returns
        -------
        The original functions that have been hijacked:
        - Clutter.main
        - Clutter.main_quit
        """
        def dummy(*args, **kw):
            pass
        # save and trap main and main_quit from Clutter
        orig_main, Clutter.main = Clutter.main, dummy
        orig_main_quit, Clutter.main_quit = Clutter.main_quit, dummy
        return orig_main, orig_main_quit
