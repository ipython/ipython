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

#-----------------------------------------------------------------------------
# Magic implementation classes
#-----------------------------------------------------------------------------

@magics_class
class PylabMagics(Magics):
    """Magics related to matplotlib's pylab support"""

    @skip_doctest
    @line_magic
    @magic_arguments.magic_arguments()
    @magic_arguments.argument(
        '--no-import', action='store_true', default=None,
        help="""Prevent IPython from populating the namespace"""
    )
    @magic_arguments.argument(
        'gui', nargs='?',
        help="""Name of the matplotlib backend to use
        ('qt', 'wx', 'gtk', 'osx', 'tk', 'inline', 'auto').
        If given, the corresponding matplotlib backend is used,
        otherwise it will be matplotlib's default
        (which you can set in your matplotlib config file).
        """
    )
    def pylab(self, line=''):
        """Load numpy and matplotlib to work interactively.

        %pylab [GUINAME]

        This function lets you activate pylab (matplotlib, numpy and
        interactive support) at any point during an IPython session.

        It will import at the top level numpy as np, pyplot as plt, matplotlib,
        pylab and mlab, as well as all names from numpy and pylab.

        If you are using the inline matplotlib backend for embedded figures,
        you can adjust its behavior via the %config magic::

            # enable SVG figures, necessary for SVG+XHTML export in the qtconsole
            In [1]: %config InlineBackend.figure_format = 'svg'

            # change the behavior of closing all figures at the end of each
            # execution (cell), or allowing reuse of active figures across
            # cells:
            In [2]: %config InlineBackend.close_figures = False

        Parameters
        ----------
        guiname : optional
          One of the valid arguments to the %gui magic ('qt', 'wx', 'gtk',
          'osx' or 'tk').  If given, the corresponding Matplotlib backend is
          used, otherwise matplotlib's default (which you can override in your
          matplotlib config file) is used.

        Examples
        --------
        In this case, where the MPL default is TkAgg::

            In [2]: %pylab

            Welcome to pylab, a matplotlib-based Python environment.
            Backend in use: TkAgg
            For more information, type 'help(pylab)'.

        But you can explicitly request a different backend::

            In [3]: %pylab qt

            Welcome to pylab, a matplotlib-based Python environment.
            Backend in use: Qt4Agg
            For more information, type 'help(pylab)'.
        """
        args = magic_arguments.parse_argstring(self.pylab, line)
        if args.no_import is None:
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
            import_all = not args.no_import

        self.shell.enable_pylab(args.gui, import_all=import_all, welcome_message=True)
