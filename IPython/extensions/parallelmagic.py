# encoding: utf-8
"""
=============
parallelmagic
=============

Magic command interface for interactive parallel work.

Usage
=====

``%autopx``

{AUTOPX_DOC}

``%px``

{PX_DOC}

``%result``

{RESULT_DOC}

"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008 The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import ast
import re

from IPython.core.error import UsageError
from IPython.core.magic import Magics, magics_class, line_magic, cell_magic
from IPython.testing.skipdoctest import skip_doctest

#-----------------------------------------------------------------------------
# Definitions of magic functions for use with IPython
#-----------------------------------------------------------------------------


NO_ACTIVE_VIEW = "Use activate() on a DirectView object to use it with magics."


@magics_class
class ParallelMagics(Magics):
    """A set of magics useful when controlling a parallel IPython cluster.
    """
    
    # A flag showing if autopx is activated or not
    _autopx = False
    # the current view used by the magics:
    active_view = None

    @skip_doctest
    @line_magic
    def result(self, parameter_s=''):
        """Print the result of command i on all engines.

        To use this a :class:`DirectView` instance must be created
        and then activated by calling its :meth:`activate` method.
        
        This lets you recall the results of %px computations after
        asynchronous submission (view.block=False).

        Then you can do the following::

            In [23]: %px os.getpid()
            Async parallel execution on engine(s): all

            In [24]: %result
            [ 8] Out[10]: 60920
            [ 9] Out[10]: 60921
            [10] Out[10]: 60922
            [11] Out[10]: 60923
        """
        
        if self.active_view is None:
            raise UsageError(NO_ACTIVE_VIEW)
        
        stride = len(self.active_view)
        try:
            index = int(parameter_s)
        except:
            index = -1
        msg_ids = self.active_view.history[stride * index:(stride * (index + 1)) or None]
        
        result = self.active_view.get_result(msg_ids)
        
        result.get()
        result.display_outputs()

    @skip_doctest
    @line_magic
    def px(self, parameter_s=''):
        """Executes the given python command in parallel.
        
        To use this a :class:`DirectView` instance must be created
        and then activated by calling its :meth:`activate` method.

        Then you can do the following::

            In [24]: %px a = os.getpid()
            Parallel execution on engine(s): all
            
            In [25]: %px print a
            [stdout:0] 1234
            [stdout:1] 1235
            [stdout:2] 1236
            [stdout:3] 1237
        """
        return self.parallel_execute(parameter_s)
        
    def parallel_execute(self, cell, block=None, groupby='type'):
        """implementation used by %px and %%parallel"""

        if self.active_view is None:
            raise UsageError(NO_ACTIVE_VIEW)
        
        # defaults:
        block = self.active_view.block if block is None else block
        
        base = "Parallel" if block else "Async parallel"
        print base + " execution on engine(s): %s" % self.active_view.targets
        
        result = self.active_view.execute(cell, silent=False, block=False)
        if block:
            result.get()
            result.display_outputs(groupby)

    @skip_doctest
    @cell_magic('px')
    def cell_px(self, line='', cell=None):
        """Executes the given python command in parallel.
        
        Cell magic usage:
        
        %%px [-o] [-e] [--group-options=type|engine|order] [--[no]block]
        
        Options (%%px cell magic only):
        
        -o: collate outputs in oder (same as group-outputs=order)
        
        -e: group outputs by engine (same as group-outputs=engine)
        
        --group-outputs=type [default behavior]:
            each output type (stdout, stderr, displaypub) for all engines
            displayed together.
        
        --group-outputs=order:
            The same as 'type', but individual displaypub outputs (e.g. plots)
            will be interleaved, so it will display all of the first plots,
            then all of the second plots, etc.
        
        --group-outputs=engine:
            All of an engine's output is displayed before moving on to the next.
        
        --[no]block:
            Whether or not to block for the execution to complete
            (and display the results).  If unspecified, the active view's
        
        
        To use this a :class:`DirectView` instance must be created
        and then activated by calling its :meth:`activate` method.

        Then you can do the following::

            In [24]: %%parallel --noblock a = os.getpid()
            Async parallel execution on engine(s): all
            
            In [25]: %px print a
            [stdout:0] 1234
            [stdout:1] 1235
            [stdout:2] 1236
            [stdout:3] 1237
        """
        
        block = None
        groupby = 'type'
        # as a cell magic, we accept args
        opts, _ = self.parse_options(line, 'oe', 'group-outputs=', 'block', 'noblock')

        if 'group-outputs' in opts:
            groupby = opts['group-outputs']
        elif 'o' in opts:
            groupby = 'order'
        elif 'e' in opts:
            groupby = 'engine'
            
        if 'block' in opts:
            block = True
        elif 'noblock' in opts:
            block = False
        
        return self.parallel_execute(cell, block=block, groupby=groupby)

    @skip_doctest
    @line_magic
    def autopx(self, parameter_s=''):
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
        if self._autopx:
            self._disable_autopx()
        else:
            self._enable_autopx()

    def _enable_autopx(self):
        """Enable %autopx mode by saving the original run_cell and installing
        pxrun_cell.
        """
        if self.active_view is None:
            raise UsageError(NO_ACTIVE_VIEW)

        # override run_cell
        self._original_run_cell = self.shell.run_cell
        self.shell.run_cell = self.pxrun_cell

        self._autopx = True
        print "%autopx enabled"

    def _disable_autopx(self):
        """Disable %autopx by restoring the original InteractiveShell.run_cell.
        """
        if self._autopx:
            self.shell.run_cell = self._original_run_cell
            self._autopx = False
            print "%autopx disabled"

    def pxrun_cell(self, raw_cell, store_history=False, silent=False):
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
                ast.parse(cell, filename=cell_name)
            except (OverflowError, SyntaxError, ValueError, TypeError,
                    MemoryError):
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
                result = self.active_view.execute(cell, silent=False, block=False)
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
                        result.display_outputs()
                return False


__doc__ = __doc__.format(
                AUTOPX_DOC = ' '*8 + ParallelMagics.autopx.__doc__,
                PX_DOC = ' '*8 + ParallelMagics.px.__doc__,
                RESULT_DOC = ' '*8 + ParallelMagics.result.__doc__
)

_loaded = False


def load_ipython_extension(ip):
    """Load the extension in IPython."""
    global _loaded
    if not _loaded:
        ip.register_magics(ParallelMagics)
        _loaded = True
