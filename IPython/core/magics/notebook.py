"""
Notebook related magics.
"""

import os

from IPython.core.magic import Magics, magics_class, line_magic
from IPython.core.magic_arguments import (argument, magic_arguments,
                                          parse_argstring)


@magics_class
class NotebookMagics(Magics):

    def notebook_dir(self):
        return self.shell.config.get('NotebookManager', {}).get('notebook_dir')

    @line_magic
    def pnd(self, parameter_s=''):
        """Return the notebook directory."""
        ndir = self.notebook_dir()
        if ndir:
            return ndir
        else:
            print "No associated notebook for this kernel."

    @magic_arguments()
    @argument(
        'reldir', default=[], nargs='*',
        help="Relative path from where notebook file is.")
    @line_magic
    def cdnb(self, parameter_s=''):
        """Change directory to where the notebook locates."""
        args = parse_argstring(self.cdnb, parameter_s)
        ndir = self.notebook_dir()
        if ndir:
            ncwd = os.path.join(ndir, *args.reldir)
            os.chdir(ncwd)
            print ncwd
        else:
            print "No associated notebook for this kernel."
