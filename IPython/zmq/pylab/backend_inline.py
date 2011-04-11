"""Produce SVG versions of active plots for display by the rich Qt frontend.
"""
#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import print_function

# Standard library imports
import sys

# Third-party imports
import matplotlib
from matplotlib.backends.backend_svg import new_figure_manager
from matplotlib._pylab_helpers import Gcf

# Local imports.
from IPython.core.displaypub import publish_display_data
from IPython.lib.pylabtools import figure_to_svg

#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------

def show(close=True):
    """Show all figures as SVG payloads sent to the IPython clients.

    Parameters
    ----------
    close : bool, optional
      If true, a ``plt.close('all')`` call is automatically issued after
      sending all the SVG figures. If this is set, the figures will entirely
      removed from the internal list of figures.
    """
    for figure_manager in Gcf.get_all_fig_managers():
        send_svg_figure(figure_manager.canvas.figure)
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


def flush_svg():
    """Call show, close all open figures, sending all SVG images.

    This is meant to be called automatically and will call show() if, during
    prior code execution, there had been any calls to draw_if_interactive.
    """
    if show._draw_called:
        show()
        show._draw_called = False


def send_svg_figure(fig):
    """Draw the current figure and send it as an SVG payload.
    """
    # For an empty figure, don't even bother calling figure_to_svg, to avoid
    # big blank spaces in the qt console
    if not fig.axes:
        return

    svg = figure_to_svg(fig)
    # flush text streams before sending figures, helps a little with output
    # synchronization in the console (though it's a bandaid, not a real sln)
    sys.stdout.flush(); sys.stderr.flush()
    publish_display_data(
        'IPython.zmq.pylab.backend_inline.send_svg_figure',
        'Matplotlib Plot',
        {'image/svg+xml' : svg}
    )

