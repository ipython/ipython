#!/usr/bin/env python
# encoding: utf-8

"""Magic command interface for interactive parallel work."""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2009  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import ast
import new
import re

from IPython.core.plugin import Plugin
from IPython.utils.traitlets import Bool, Any, Instance
from IPython.utils.autoattr import auto_attr
from IPython.testing import decorators as testdec

#-----------------------------------------------------------------------------
# Definitions of magic functions for use with IPython
#-----------------------------------------------------------------------------


NO_ACTIVE_VIEW = """
Use activate() on a DirectView object to activate it for magics.
"""


class ParalleMagic(Plugin):
    """A component to manage the %result, %px and %autopx magics."""

    active_view = Any()
    verbose = Bool(False, config=True)
    shell = Instance('IPython.core.interactiveshell.InteractiveShellABC')

    def __init__(self, shell=None, config=None):
        super(ParalleMagic, self).__init__(shell=shell, config=config)
        self._define_magics()
        # A flag showing if autopx is activated or not
        self.autopx = False

    def _define_magics(self):
        """Define the magic functions."""
        self.shell.define_magic('result', self.magic_result)
        self.shell.define_magic('px', self.magic_px)
        self.shell.define_magic('autopx', self.magic_autopx)

    @testdec.skip_doctest
    def magic_result(self, ipself, parameter_s=''):
        """Print the result of command i on all engines..

        To use this a :class:`DirectView` instance must be created 
        and then activated by calling its :meth:`activate` method.

        Then you can do the following::

            In [23]: %result
            Out[23]: 
            <Results List>
            [0] In [6]: a = 10
            [1] In [6]: a = 10
    
            In [22]: %result 6
            Out[22]: 
            <Results List>
            [0] In [6]: a = 10
            [1] In [6]: a = 10
        """
        if self.active_view is None:
            print NO_ACTIVE_VIEW
            return

        try:
            index = int(parameter_s)
        except:
            index = None
        result = self.active_view.get_result(index)
        return result

    @testdec.skip_doctest
    def magic_px(self, ipself, parameter_s=''):
        """Executes the given python command in parallel.

        To use this a :class:`DirectView` instance must be created 
        and then activated by calling its :meth:`activate` method.
        
        Then you can do the following::

            In [24]: %px a = 5
            Parallel execution on engines: all
            Out[24]: 
            <Results List>
            [0] In [7]: a = 5
            [1] In [7]: a = 5
        """

        if self.active_view is None:
            print NO_ACTIVE_VIEW
            return
        print "Parallel execution on engines: %s" % self.active_view.targets
        result = self.active_view.execute(parameter_s)
        return result

    @testdec.skip_doctest
    def magic_autopx(self, ipself, parameter_s=''):
        """Toggles auto parallel mode.

        To use this a :class:`DirectView` instance must be created 
        and then activated by calling its :meth:`activate` method. Once this
        is called, all commands typed at the command line are send to
        the engines to be executed in parallel. To control which engine
        are used, set the ``targets`` attributed of the multiengine client
        before entering ``%autopx`` mode.

        Then you can do the following::

            In [25]: %autopx
            %autopx to enabled

            In [26]: a = 10
            <Results List>
            [0] In [8]: a = 10
            [1] In [8]: a = 10


            In [27]: %autopx
            %autopx disabled
        """
        if self.autopx:
            self._disable_autopx()
        else:
            self._enable_autopx()

    def _enable_autopx(self):
        """Enable %autopx mode by saving the original run_cell and installing 
        pxrun_cell.
        """
        if self.active_view is None:
            print NO_ACTIVE_VIEW
            return

        self._original_run_cell = self.shell.run_cell
        self.shell.run_cell = new.instancemethod(
            self.pxrun_cell, self.shell, self.shell.__class__
        )
        self.autopx = True
        print "%autopx enabled"
    
    def _disable_autopx(self):
        """Disable %autopx by restoring the original InteractiveShell.run_cell.
        """
        if self.autopx:
            self.shell.run_cell = self._original_run_cell
            self.autopx = False
            print "%autopx disabled"

    def pxrun_cell(self, ipself, cell, store_history=True):
        """drop-in replacement for InteractiveShell.run_cell.
        
        This executes code remotely, instead of in the local namespace.
        """
        raw_cell = cell
        with ipself.builtin_trap:
            cell = ipself.prefilter_manager.prefilter_lines(cell)
        
            # Store raw and processed history
            if store_history:
                ipself.history_manager.store_inputs(ipself.execution_count, 
                                                  cell, raw_cell)

            # ipself.logger.log(cell, raw_cell)
        
            cell_name = ipself.compile.cache(cell, ipself.execution_count)
        
            try:
                code_ast = ast.parse(cell, filename=cell_name)
            except (OverflowError, SyntaxError, ValueError, TypeError, MemoryError):
                # Case 1
                ipself.showsyntaxerror()
                ipself.execution_count += 1
                return None
            except NameError:
                pass

        if store_history:
            # Write output to the database. Does nothing unless
            # history output logging is enabled.
            ipself.history_manager.store_output(ipself.execution_count)
            # Each cell is a *single* input, regardless of how many lines it has
            ipself.execution_count += 1
        print cell
        
        if re.search(r'get_ipython\(\)\.magic\(u?"%?autopx', cell):
            self._disable_autopx()
            return False
        else:
            try:
                result = self.active_view.execute(cell, block=False)
            except:
                ipself.showtraceback()
                return False
            
            if self.active_view.block:
                try:
                    result.get()
                except:
                    ipself.showtraceback()
                else:
                    targets = self.active_view.targets
                    if isinstance(targets, int):
                        targets = [targets]
                    if targets == 'all':
                        targets = self.active_view.client.ids
                    stdout = [s.rstrip() for s in result.stdout]
                    if any(stdout):
                        for i,eid in enumerate(targets):
                            print '[stdout:%i]'%eid, stdout[i]
            return False


_loaded = False


def load_ipython_extension(ip):
    """Load the extension in IPython."""
    global _loaded
    if not _loaded:
        plugin = ParalleMagic(shell=ip, config=ip.config)
        ip.plugin_manager.register_plugin('parallelmagic', plugin)
        _loaded = True

