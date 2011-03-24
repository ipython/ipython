"""Compiler tools with improved interactive support.

Provides compilation machinery similar to codeop, but with caching support so
we can provide interactive tracebacks.

Authors
-------
* Robert Kern
* Fernando Perez
"""

# Note: though it might be more natural to name this module 'compiler', that
# name is in the stdlib and name collisions with the stdlib tend to produce
# weird problems (often with third-party tools).

#-----------------------------------------------------------------------------
#  Copyright (C) 2010 The IPython Development Team.
#
#  Distributed under the terms of the BSD License.
#
#  The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import print_function

# Stdlib imports
import codeop
import hashlib
import linecache
import time

#-----------------------------------------------------------------------------
# Local utilities
#-----------------------------------------------------------------------------

def code_name(code, number=0):
    """ Compute a (probably) unique name for code for caching.
    
    This now expects code to be unicode.
    """
    hash_digest = hashlib.md5(code.encode("utf-8")).hexdigest()
    # Include the number and 12 characters of the hash in the name.  It's
    # pretty much impossible that in a single session we'll have collisions
    # even with truncated hashes, and the full one makes tracebacks too long
    return '<ipython-input-{0}-{1}>'.format(number, hash_digest[:12])

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

class CachingCompiler(object):
    """A compiler that caches code compiled from interactive statements.
    """

    def __init__(self):
        self._compiler = codeop.CommandCompiler()
        
        # This is ugly, but it must be done this way to allow multiple
        # simultaneous ipython instances to coexist.  Since Python itself
        # directly accesses the data structures in the linecache module, and
        # the cache therein is global, we must work with that data structure.
        # We must hold a reference to the original checkcache routine and call
        # that in our own check_cache() below, but the special IPython cache
        # must also be shared by all IPython instances.  If we were to hold
        # separate caches (one in each CachingCompiler instance), any call made
        # by Python itself to linecache.checkcache() would obliterate the
        # cached data from the other IPython instances.
        if not hasattr(linecache, '_ipython_cache'):
            linecache._ipython_cache = {}
        if not hasattr(linecache, '_checkcache_ori'):
            linecache._checkcache_ori = linecache.checkcache
        # Now, we must monkeypatch the linecache directly so that parts of the
        # stdlib that call it outside our control go through our codepath
        # (otherwise we'd lose our tracebacks).
        linecache.checkcache = self.check_cache

    @property
    def compiler_flags(self):
        """Flags currently active in the compilation process.
        """
        return self._compiler.compiler.flags
        
    def __call__(self, code, symbol, number=0):
        """Compile some code while caching its contents such that the inspect
        module can find it later.

        Parameters
        ----------
        code : str
          Source code to be compiled, one or more lines.

        symbol : str
          One of 'single', 'exec' or 'eval' (see the builtin ``compile``
          documentation for further details on these fields).

        number : int, optional
          An integer argument identifying the code, useful for informational
          purposes in tracebacks (typically it will be the IPython prompt
          number).
        """
        name = code_name(code, number)
        code_obj = self._compiler(code, name, symbol)
        entry = (len(code), time.time(),
                 [line+'\n' for line in code.splitlines()], name)
        # Cache the info both in the linecache (a global cache used internally
        # by most of Python's inspect/traceback machinery), and in our cache
        linecache.cache[name] = entry
        linecache._ipython_cache[name] = entry
        return code_obj

    def check_cache(self, *args):
        """Call linecache.checkcache() safely protecting our cached values.
        """
        # First call the orignal checkcache as intended
        linecache._checkcache_ori(*args)
        # Then, update back the cache with our data, so that tracebacks related
        # to our compiled codes can be produced.
        linecache.cache.update(linecache._ipython_cache)
