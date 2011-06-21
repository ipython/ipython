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
from matplotlib.backends.backend_agg import new_figure_manager
from matplotlib._pylab_helpers import Gcf

# Local imports.
from IPython.config.configurable import SingletonConfigurable
from IPython.core.displaypub import publish_display_data
from IPython.lib.pylabtools import print_figure, select_figure_format
from IPython.utils.traitlets import Dict, Instance, CaselessStrEnum
#-----------------------------------------------------------------------------
# Configurable for inline backend options
#-----------------------------------------------------------------------------

class InlineBackendConfig(SingletonConfigurable):
    """An object to store configuration of the inline backend."""

    # The typical default figure size is too large for inline use,
    # so we shrink the figure size to 6x4, and tweak fonts to
    # make that fit.  This is configurable via Global.pylab_inline_rc,
    # or rather it will be once the zmq kernel is hooked up to
    # the config system.
    rc = Dict({'figure.figsize': (6.0,4.0),
        # 12pt labels get cutoff on 6x4 logplots, so use 10pt.
        'font.size': 10,
        # 10pt still needs a little more room on the xlabel:
        'figure.subplot.bottom' : .125
        }, config=True,
        help="""Subset of matplotlib rcParams that should be different for the
        inline backend."""
    )
    figure_format = CaselessStrEnum(['svg', 'png'], default_value='png', config=True,
        help="The image format for figures with the inline backend.")

    def _figure_format_changed(self, name, old, new):
        if self.shell is None:
            return
        else:
            select_figure_format(self.shell, new)

    shell = Instance('IPython.core.interactiveshell.InteractiveShellABC')


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
        send_figure(figure_manager.canvas.figure)
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


def flush_figures():
    """Call show, close all open figures, sending all figure images.

    This is meant to be called automatically and will call show() if, during
    prior code execution, there had been any calls to draw_if_interactive.
    """
    if show._draw_called:
        show()
        show._draw_called = False


def send_figure(fig):
    """Draw the current figure and send it as a PNG payload.
    """
    # For an empty figure, don't even bother calling figure_to_svg, to avoid
    # big blank spaces in the qt console
    if not fig.axes:
        return
    fmt = InlineBackendConfig.instance().figure_format
    data = print_figure(fig, fmt)
    mimetypes = { 'png' : 'image/png', 'svg' : 'image/svg+xml' }
    mime = mimetypes[fmt]
    # flush text streams before sending figures, helps a little with output
    # synchronization in the console (though it's a bandaid, not a real sln)
    sys.stdout.flush(); sys.stderr.flush()
    publish_display_data(
        'IPython.zmq.pylab.backend_inline.send_figure',
        'Matplotlib Plot',
        {mime : data}
    )

