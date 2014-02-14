"""Set a default cell magic for all subsequent inputs in IPython notebook.

See docs for %default_cell_magic for details.
"""
#-----------------------------------------------------------------------------
# Copyright (c) 2014, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

from IPython.core.magic import Magics, magics_class,  line_magic
from IPython.core.inputsplitter import IPythonInputSplitter

class OverrideSplitter(IPythonInputSplitter):
    """Wrapper for the original IPythonInputSplitter that changes
    cell input by prepending a default magic or removing %%python
    as needed.
    """
    def __init__(self, splitter, magic=""):
        self.splitter = splitter
        self.magic = "%%" + magic

    def patch_magic(self, text):
        """Patch cell text with magic, unless it already has a magic,
        or it starts with %%python.
        """
        python_magic = "%%python"
        if text.startswith(python_magic):
            return text[len(python_magic):]
        if text.startswith("%"):
            return text
        return ("%s\n" % self.magic) + text

    def transform_cell(self, cell):
        """Patch the cell contents, then delegate to original
        IPythonInputSplitter.
        """
        patched = self.patch_magic(cell)
        return self.splitter.transform_cell(patched)

@magics_class
class DefaultCellMagic(Magics):

    @line_magic
    def default_cell_magic(self, parameters):
        """Set a default cell magic in IPython notebook.

        Example:

        > %load_ext default_cell_magic
        > %default_cell_magic bash

        From now on all cells will be interpreted as bash commands by
        prepending them with `%%bash` before they are executed. You can
        switch back to python by using the %%python cell magic:

        > %%python
        > print "Hello from %s" % python.capitalize()

        Cells that already start with a cell magic (or a line magic) are left unchanged.

        You can switch back to IPython's normal behavior by using
        %default_cell_magic with no argument:

        > %default_cell_magic
        """
        itm_old = self.shell.input_transformer_manager
        if isinstance(itm_old, OverrideSplitter):
            itm_old = itm_old.splitter
        args = parameters.split()
        if args == []:
            self.shell.input_transformer_manager = itm_old
        else:
            self.shell.input_transformer_manager = OverrideSplitter(itm_old, args[0])


def load_ipython_extension(ip):
    dcm = DefaultCellMagic(ip)
    ip.register_magics(dcm)

# TODO: implement unload, reload_extension has problems ATM.
