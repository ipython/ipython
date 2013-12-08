"""Configurable for configuring the IPython inline backend

This module does not import anything from matplotlib.
"""
#-----------------------------------------------------------------------------
#       Copyright (C) 2011 The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from IPython.config.configurable import SingletonConfigurable
from IPython.utils.traitlets import Dict, Instance, CaselessStrEnum, Bool, Int
from IPython.utils.warn import warn

#-----------------------------------------------------------------------------
# Configurable for inline backend options
#-----------------------------------------------------------------------------

try:
    from PIL import Image
    has_pil = True
except:
    has_pil = False

# inherit from InlineBackendConfig for deprecation purposes
class InlineBackendConfig(SingletonConfigurable):
    pass

class InlineBackend(InlineBackendConfig):
    """An object to store configuration of the inline backend."""

    def _config_changed(self, name, old, new):
        # warn on change of renamed config section
        if new.InlineBackendConfig != old.InlineBackendConfig:
            warn("InlineBackendConfig has been renamed to InlineBackend")
        super(InlineBackend, self)._config_changed(name, old, new)

    # The typical default figure size is too large for inline use,
    # so we shrink the figure size to 6x4, and tweak fonts to
    # make that fit.
    rc = Dict({'figure.figsize': (6.0,4.0),
        # play nicely with white background in the Qt and notebook frontend
        'figure.facecolor': (1,1,1,0),
        'figure.edgecolor': (1,1,1,0),
        # 12pt labels get cutoff on 6x4 logplots, so use 10pt.
        'font.size': 10,
        # 72 dpi matches SVG/qtconsole
        # this only affects PNG export, as SVG has no dpi setting
        'savefig.dpi': 72,
        # 10pt still needs a little more room on the xlabel:
        'figure.subplot.bottom' : .125
        }, config=True,
        help="""Subset of matplotlib rcParams that should be different for the
        inline backend."""
    )

    fmts = ['svg', 'png', 'retina']

    if has_pil:
        # If we have PIL using jpeg as inline image format can save some bytes.
        fmts.append('jpg')

    # Matplotlib's JPEG printer supports a quality option that can be tweaked.
    # We expose it only if PIL is available so the user isn't confused. But it
    # isn't guarded by "has_pil" test because core/pylabtools.py expects this
    # field OR we need to propagate the has_pil test to that module too.
    quality = Int(default_value=90, config=has_pil,
                  help="Quality of compression [0-100], currently for lossy JPEG only.")

    figure_format = CaselessStrEnum(fmts, default_value='png', config=True,
        help="The image format for figures with the inline backend.")

    def _figure_format_changed(self, name, old, new):
        from IPython.core.pylabtools import select_figure_format
        if self.shell is None:
            return
        else:
            select_figure_format(self.shell, new)
    
    close_figures = Bool(True, config=True,
        help="""Close all figures at the end of each cell.
        
        When True, ensures that each cell starts with no active figures, but it
        also means that one must keep track of references in order to edit or
        redraw figures in subsequent cells. This mode is ideal for the notebook,
        where residual plots from other cells might be surprising.
        
        When False, one must call figure() to create new figures. This means
        that gcf() and getfigs() can reference figures created in other cells,
        and the active figure can continue to be edited with pylab/pyplot
        methods that reference the current active figure. This mode facilitates
        iterative editing of figures, and behaves most consistently with
        other matplotlib backends, but figure barriers between cells must
        be explicit.
        """)

    shell = Instance('IPython.core.interactiveshell.InteractiveShellABC')


