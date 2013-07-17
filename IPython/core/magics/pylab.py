"""Implementation of magic functions for matplotlib/pylab support.
"""
#-----------------------------------------------------------------------------
#  Copyright (c) 2012 The IPython Development Team.
#
#  Distributed under the terms of the Modified BSD License.
#
#  The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Our own packages
from IPython.config.application import Application
from IPython.core import magic_arguments
from IPython.core.magic import Magics, magics_class, line_magic
from IPython.testing.skipdoctest import skip_doctest
from IPython.utils.warn import warn
from IPython.core.pylabtools import backends

#-----------------------------------------------------------------------------
# Magic implementation classes
#-----------------------------------------------------------------------------

magic_gui_arg = magic_arguments.argument(
        'gui', nargs='?',
        help="""Name of the matplotlib backend to use %s.
        If given, the corresponding matplotlib backend is used,
        otherwise it will be matplotlib's default
        (which you can set in your matplotlib config file).
        """ % str(tuple(sorted(backends.keys())))
)


@magics_class
class PylabMagics(Magics):
    """Magics related to matplotlib's pylab support"""
    
    @skip_doctest
    @line_magic
    @magic_arguments.magic_arguments()
    @magic_gui_arg
    def matplotlib(self, line=''):
        """Set up matplotlib to work interactively.
        
        This function lets you activate matplotlib interactive support
        at any point during an IPython session.
        It does not import anything into the interactive namespace.
        
        If you are using the inline matplotlib backend for embedded figures,
        you can adjust its behavior via the %config magic::

            # enable SVG figures, necessary for SVG+XHTML export in the qtconsole
            In [1]: %config InlineBackend.figure_format = 'svg'

            # change the behavior of closing all figures at the end of each
            # execution (cell), or allowing reuse of active figures across
            # cells:
            In [2]: %config InlineBackend.close_figures = False

        Examples
        --------
        In this case, where the MPL default is TkAgg::

            In [2]: %matplotlib
            Using matplotlib backend: TkAgg

        But you can explicitly request a different backend::

            In [3]: %matplotlib qt
        """
        args = magic_arguments.parse_argstring(self.matplotlib, line)
        gui, backend = self.shell.enable_matplotlib(args.gui)
        self._show_matplotlib_backend(args.gui, backend)

    @skip_doctest
    @line_magic
    @magic_arguments.magic_arguments()
    @magic_arguments.argument(
        '--no-import-all', action='store_true', default=None,
        help="""Prevent IPython from performing ``import *`` into the interactive namespace.
        
        The names that will still be added to the namespace if this flag is given::
        
            numpy
            matplotlib
            np (numpy alias)
            plt (matplotlib.pyplot alias)
            pylab (from matplotlib)
            pyplot (from matplotlib)
            mlab (from matplotlib)
            display (from IPython)
            figsize (from IPython)
            getfigs (from IPython)
        
        You can govern the default behavior with the
        InteractiveShellApp.pylab_import_all configurable.
        """
    )
    @magic_gui_arg
    def pylab(self, line=''):
        """Load numpy and matplotlib to work interactively.

        This function lets you activate pylab (matplotlib, numpy and
        interactive support) at any point during an IPython session.

        It will import at the top level numpy as np, pyplot as plt, matplotlib,
        pylab and mlab, as well as all names from numpy and pylab.
        
        See the %matplotlib magic for more details.
        """
        args = magic_arguments.parse_argstring(self.pylab, line)
        if args.no_import_all is None:
            # get default from Application
            if Application.initialized():
                app = Application.instance()
                try:
                    import_all = app.pylab_import_all
                except AttributeError:
                    import_all = True
            else:
                # nothing specified, no app - default True
                import_all = True
        else:
            # invert no-import flag
            import_all = not args.no_import_all

        gui, backend, clobbered = self.shell.enable_pylab(args.gui, import_all=import_all)
        self._show_matplotlib_backend(args.gui, backend)
        if clobbered:
            warn("pylab import has clobbered these variables: %s"  % clobbered +
            "\n`%pylab --no-import-all` prevents importing * from pylab and numpy"
            )
    
    def _show_matplotlib_backend(self, gui, backend):
        """show matplotlib message backend message"""
        if not gui or gui == 'auto':
            print ("using matplotlib backend: %s" % backend)
    
