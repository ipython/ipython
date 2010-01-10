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

import new

from IPython.core.component import Component
from IPython.utils.traitlets import Bool, Any
from IPython.utils.autoattr import auto_attr
from IPython.testing import decorators as testdec

#-----------------------------------------------------------------------------
# Definitions of magic functions for use with IPython
#-----------------------------------------------------------------------------


NO_ACTIVE_MULTIENGINE_CLIENT = """
Use activate() on a MultiEngineClient object to activate it for magics.
"""


class ParalleMagicComponent(Component):
    """A component to manage the %result, %px and %autopx magics."""

    active_multiengine_client = Any()
    verbose = Bool(False, config=True)

    def __init__(self, parent, name=None, config=None):
        super(ParalleMagicComponent, self).__init__(parent, name=name, config=config)
        self._define_magics()
        # A flag showing if autopx is activated or not
        self.autopx = False

    # Access other components like this rather than by a regular attribute.
    # This won't lookup the InteractiveShell object until it is used and
    # then it is cached.  This is both efficient and couples this class 
    # more loosely to InteractiveShell.
    @auto_attr
    def shell(self):
        return Component.get_instances(
            root=self.root,
            klass='IPython.core.iplib.InteractiveShell')[0]

    def _define_magics(self):
        """Define the magic functions."""
        self.shell.define_magic('result', self.magic_result)
        self.shell.define_magic('px', self.magic_px)
        self.shell.define_magic('autopx', self.magic_autopx)

    @testdec.skip_doctest
    def magic_result(self, ipself, parameter_s=''):
        """Print the result of command i on all engines..

        To use this a :class:`MultiEngineClient` instance must be created 
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
        if self.active_multiengine_client is None:
            print NO_ACTIVE_MULTIENGINE_CLIENT
            return

        try:
            index = int(parameter_s)
        except:
            index = None
        result = self.active_multiengine_client.get_result(index)
        return result

    @testdec.skip_doctest
    def magic_px(self, ipself, parameter_s=''):
        """Executes the given python command in parallel.

        To use this a :class:`MultiEngineClient` instance must be created 
        and then activated by calling its :meth:`activate` method.
        
        Then you can do the following::

            In [24]: %px a = 5
            Parallel execution on engines: all
            Out[24]: 
            <Results List>
            [0] In [7]: a = 5
            [1] In [7]: a = 5
        """

        if self.active_multiengine_client is None:
            print NO_ACTIVE_MULTIENGINE_CLIENT
            return
        print "Parallel execution on engines: %s" % self.active_multiengine_client.targets
        result = self.active_multiengine_client.execute(parameter_s)
        return result

    @testdec.skip_doctest
    def magic_autopx(self, ipself, parameter_s=''):
        """Toggles auto parallel mode.

        To use this a :class:`MultiEngineClient` instance must be created 
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
        """Enable %autopx mode by saving the original runsource and installing 
        pxrunsource.
        """
        if self.active_multiengine_client is None:
            print NO_ACTIVE_MULTIENGINE_CLIENT
            return

        self._original_runsource = self.shell.runsource
        self.shell.runsource = new.instancemethod(
            self.pxrunsource, self.shell, self.shell.__class__
        )
        self.autopx = True
        print "%autopx enabled"
    
    def _disable_autopx(self):
        """Disable %autopx by restoring the original InteractiveShell.runsource."""
        if self.autopx:
            self.shell.runsource = self._original_runsource
            self.autopx = False
            print "%autopx disabled"

    def pxrunsource(self, ipself, source, filename="<input>", symbol="single"):
        """A parallel replacement for InteractiveShell.runsource."""

        try:
            code = ipself.compile(source, filename, symbol)
        except (OverflowError, SyntaxError, ValueError):
            # Case 1
            ipself.showsyntaxerror(filename)
            return None

        if code is None:
            # Case 2
            return True

        # Case 3
        # Because autopx is enabled, we now call executeAll or disable autopx if
        # %autopx or autopx has been called
        if 'get_ipython().magic("%autopx' in source or 'get_ipython().magic("autopx' in source:
            self._disable_autopx()
            return False
        else:
            try:
                result = self.active_multiengine_client.execute(source)
            except:
                ipself.showtraceback()
            else:
                print result.__repr__()
            return False


_loaded = False


def load_ipython_extension(ip):
    """Load the extension in IPython."""
    global _loaded
    if not _loaded:
        prd = ParalleMagicComponent(ip, name='parallel_magic')
        _loaded = True

