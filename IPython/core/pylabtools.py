# -*- coding: utf-8 -*-
"""Pylab (matplotlib) support utilities.

Authors
-------
Fernando Perez.
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2009  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from IPython.utils.genutils import flag_calls

#-----------------------------------------------------------------------------
# Main classes and functions
#-----------------------------------------------------------------------------

def pylab_activate(user_ns, gui=None, import_all=True):
    """Activate pylab mode in the user's namespace.

    Loads and initializes numpy, matplotlib and friends for interactive use.

    Parameters
    ----------
    user_ns : dict
      Namespace where the imports will occur.

    gui : optional, string
      A valid gui name following the conventions of the %gui magic.

    import_all : optional, boolean
      If true, an 'import *' is done from numpy and pylab.

    Returns
    -------
    The actual gui used (if not given as input, it was obtained from matplotlib
    itself, and will be needed next to configure IPython's gui integration.
    """

    # Initialize matplotlib to interactive mode always
    import matplotlib

    # If user specifies a GUI, that dictates the backend, otherwise we read the
    # user's mpl default from the mpl rc structure
    g2b = {'tk': 'TkAgg',
           'gtk': 'GTKAgg',
           'wx': 'WXAgg',
           'qt': 'Qt4Agg', # qt3 not supported
           'qt4': 'Qt4Agg' }

    if gui:
        # select backend based on requested gui
        backend = g2b[gui]
    else:
        backend = matplotlib.rcParams['backend']
        # In this case, we need to find what the appropriate gui selection call
        # should be for IPython, so we can activate inputhook accordingly
        b2g = dict(zip(g2b.values(),g2b.keys()))
        gui = b2g[backend]

    # We must set the desired backend before importing pylab
    matplotlib.use(backend)
    
    # This must be imported last in the matplotlib series, after
    # backend/interactivity choices have been made
    import matplotlib.pylab as pylab

    # XXX For now leave this commented out, but depending on discussions with
    # mpl-dev, we may be able to allow interactive switching...
    #import matplotlib.pyplot
    #matplotlib.pyplot.switch_backend(backend)

    pylab.show._needmain = False
    # We need to detect at runtime whether show() is called by the user.
    # For this, we wrap it into a decorator which adds a 'called' flag.
    pylab.draw_if_interactive = flag_calls(pylab.draw_if_interactive)

    # Import numpy as np/pyplot as plt are conventions we're trying to
    # somewhat standardize on.  Making them available to users by default
    # will greatly help this. 
    exec ("import numpy\n"
          "import matplotlib\n"
          "from matplotlib import pylab, mlab, pyplot\n"
          "np = numpy\n"
          "plt = pyplot\n"
          ) in user_ns

    if import_all:
        exec("from matplotlib.pylab import *\n"
             "from numpy import *\n") in user_ns

    matplotlib.interactive(True)

    print """
Welcome to pylab, a matplotlib-based Python environment.
Backend in use: %s
For more information, type 'help(pylab)'.""" % backend
    
    return gui

# We need a little factory function here to create the closure where
# safe_execfile can live.
def mpl_runner(safe_execfile):
    """Factory to return a matplotlib-enabled runner for %run.

    Parameters
    ----------
    safe_execfile : function
      This must be a function with the same interface as the
      :meth:`safe_execfile` method of IPython.

    Returns
    -------
    A function suitable for use as the ``runner`` argument of the %run magic
    function.
    """
    
    def mpl_execfile(fname,*where,**kw):
        """matplotlib-aware wrapper around safe_execfile.

        Its interface is identical to that of the :func:`execfile` builtin.

        This is ultimately a call to execfile(), but wrapped in safeties to
        properly handle interactive rendering."""

        import matplotlib
        import matplotlib.pylab as pylab

        #print '*** Matplotlib runner ***' # dbg
        # turn off rendering until end of script
        is_interactive = matplotlib.rcParams['interactive']
        matplotlib.interactive(False)
        safe_execfile(fname,*where,**kw)
        matplotlib.interactive(is_interactive)
        # make rendering call now, if the user tried to do it
        if pylab.draw_if_interactive.called:
            pylab.draw()
            pylab.draw_if_interactive.called = False

    return mpl_execfile
