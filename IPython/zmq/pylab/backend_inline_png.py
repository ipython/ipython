"""Produce Agg-rendered PNG versions of active plots for display by the rich Qt frontend.
"""
#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import print_function

# Standard library imports
import sys

# Third-party imports
import matplotlib
from matplotlib.backends.backend_agg import new_figure_manager
from matplotlib._pylab_helpers import Gcf

# Local imports.
from IPython.core.displaypub import publish_display_data
from IPython.lib.pylabtools import print_figure

#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------

def show(close=True):
    """Show all figures as PNG payloads sent to the IPython clients.

    Parameters
    ----------
    close : bool, optional
      If true, a ``plt.close('all')`` call is automatically issued after
      sending all the PNG figures. If this is set, the figures will entirely
      removed from the internal list of figures.
    """
    for figure_manager in Gcf.get_all_fig_managers():
        send_png_figure(figure_manager.canvas.figure)
    if close:
        matplotlib.pyplot.close('all')


# This flag will be reset by draw_if_interactive when called
show._draw_called = False


def draw_if_interactive():
    """
    Is called after every pylab drawing command
    """
    # We simply flag we were called and otherwise do nothing.  At the end of
    # the code execution, a separate call to show_close() will act upon this.
    show._draw_called = True


def send_png_figure(fig):
    """Draw the current figure and send it as a PNG payload.
    """
    # For an empty figure, don't even bother calling print_figure, to avoid
    # big blank spaces in the qt console
    if not fig.axes:
        return

    png = print_figure(fig, 'png')
    # flush text streams before sending figures, helps a little with output
    # synchronization in the console (though it's a bandaid, not a real sln)
    sys.stdout.flush(); sys.stderr.flush()
    publish_display_data(
        'IPython.zmq.pylab.backend_inline.send_png_figure',
        'Matplotlib Plot',
        {'image/png' : png}
    )

