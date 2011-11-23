# encoding: utf-8
"""
=============
parallelmagic
=============

Magic command interface for interactive parallel work.

Usage
=====

``%autopx``

@AUTOPX_DOC@

``%px``

@PX_DOC@

``%result``

@RESULT_DOC@

"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import ast
import re

from IPython.core.plugin import Plugin
from IPython.utils.traitlets import Bool, Any, Instance
from IPython.testing.skipdoctest import skip_doctest

#-----------------------------------------------------------------------------
# Definitions of magic functions for use with IPython
#-----------------------------------------------------------------------------


NO_ACTIVE_VIEW = """
Use activate() on a DirectView object to activate it for magics.
"""


class ParalleMagic(Plugin):
    """A component to manage the %result, %px and %autopx magics."""

    active_view = Instance('IPython.parallel.client.view.DirectView')
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

    @skip_doctest
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

    @skip_doctest
    def magic_px(self, ipself, parameter_s=''):
        """Executes the given python command in parallel.

        To use this a :class:`DirectView` instance must be created
        and then activated by calling its :meth:`activate` method.

        Then you can do the following::

            In [24]: %px a = 5
            Parallel execution on engine(s): all
            Out[24]:
            <Results List>
            [0] In [7]: a = 5
            [1] In [7]: a = 5
        """

        if self.active_view is None:
            print NO_ACTIVE_VIEW
            return
        print "Parallel execution on engine(s): %s" % self.active_view.targets
        result = self.active_view.execute(parameter_s, block=False)
        if self.active_view.block:
            result.get()
            self._maybe_display_output(result)

    @skip_doctest
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
            Parallel execution on engine(s): [0,1,2,3]
            In [27]: print a
            Parallel execution on engine(s): [0,1,2,3]
            [stdout:0] 10
            [stdout:1] 10
            [stdout:2] 10
            [stdout:3] 10


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

        # override run_cell and run_code
        self._original_run_cell = self.shell.run_cell
        self.shell.run_cell = self.pxrun_cell
        self._original_run_code = self.shell.run_code
        self.shell.run_code = self.pxrun_code

        self.autopx = True
        print "%autopx enabled"

    def _disable_autopx(self):
        """Disable %autopx by restoring the original InteractiveShell.run_cell.
        """
        if self.autopx:
            self.shell.run_cell = self._original_run_cell
            self.shell.run_code = self._original_run_code
            self.autopx = False
            print "%autopx disabled"

    def _maybe_display_output(self, result):
        """Maybe display the output of a parallel result.

        If self.active_view.block is True, wait for the result
        and display the result.  Otherwise, this is a noop.
        """
        if isinstance(result.stdout, basestring):
            # single result
            stdouts = [result.stdout.rstrip()]
        else:
            stdouts = [s.rstrip() for s in result.stdout]

        targets = self.active_view.targets
        if isinstance(targets, int):
            targets = [targets]
        elif targets == 'all':
            targets = self.active_view.client.ids

        if any(stdouts):
            for eid,stdout in zip(targets, stdouts):
                print '[stdout:%i]'%eid, stdout


    def pxrun_cell(self, raw_cell, store_history=True):
        """drop-in replacement for InteractiveShell.run_cell.

        This executes code remotely, instead of in the local namespace.

        See InteractiveShell.run_cell for details.
        """

        if (not raw_cell) or raw_cell.isspace():
            return

        ipself = self.shell

        with ipself.builtin_trap:
            cell = ipself.prefilter_manager.prefilter_lines(raw_cell)

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
                # ignore name errors, because we don't know the remote keys
                pass

        if store_history:
            # Write output to the database. Does nothing unless
            # history output logging is enabled.
            ipself.history_manager.store_output(ipself.execution_count)
            # Each cell is a *single* input, regardless of how many lines it has
            ipself.execution_count += 1
        if re.search(r'get_ipython\(\)\.magic\(u?["\']%?autopx', cell):
            self._disable_autopx()
            return False
        else:
            try:
                result = self.active_view.execute(cell, block=False)
            except:
                ipself.showtraceback()
                return True
            else:
                if self.active_view.block:
                    try:
                        result.get()
                    except:
                        self.shell.showtraceback()
                        return True
                    else:
                        self._maybe_display_output(result)
                return False

    def pxrun_code(self, code_obj):
        """drop-in replacement for InteractiveShell.run_code.

        This executes code remotely, instead of in the local namespace.

        See InteractiveShell.run_code for details.
        """
        ipself = self.shell
        # check code object for the autopx magic
        if 'get_ipython' in code_obj.co_names and 'magic' in code_obj.co_names and \
            any( [ isinstance(c, basestring) and 'autopx' in c for c in code_obj.co_consts ]):
            self._disable_autopx()
            return False
        else:
            try:
                result = self.active_view.execute(code_obj, block=False)
            except:
                ipself.showtraceback()
                return True
            else:
                if self.active_view.block:
                    try:
                        result.get()
                    except:
                        self.shell.showtraceback()
                        return True
                    else:
                        self._maybe_display_output(result)
                return False


__doc__ = __doc__.replace('@AUTOPX_DOC@',
                          "        " + ParalleMagic.magic_autopx.__doc__)
__doc__ = __doc__.replace('@PX_DOC@',
                          "        " + ParalleMagic.magic_px.__doc__)
__doc__ = __doc__.replace('@RESULT_DOC@',
                          "        " + ParalleMagic.magic_result.__doc__)


_loaded = False


def load_ipython_extension(ip):
    """Load the extension in IPython."""
    global _loaded
    if not _loaded:
        plugin = ParalleMagic(shell=ip, config=ip.config)
        ip.plugin_manager.register_plugin('parallelmagic', plugin)
        _loaded = True

