# -*- coding: utf-8 -*-
"""
%cache magic for variable caching.

"""
#-----------------------------------------------------------------------------
#  Copyright (c) 2012, The IPython Development Team.
#
#  Distributed under the terms of the Modified BSD License.
#
#  The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Stdlib
import inspect, os, sys, textwrap, cPickle

# Our own
from IPython.config.configurable import Configurable
from IPython.core import magic_arguments
from IPython.core.magic import Magics, magics_class, line_magic, cell_magic

#-----------------------------------------------------------------------------
# Functions and classes
#-----------------------------------------------------------------------------
@magics_class
class CacheMagics(Magics, Configurable):
    """Variable caching.

    Provides the %cache magic."""
    
    @magic_arguments.magic_arguments()
    @magic_arguments.argument(
        'vars', nargs='*', type=str,
        help="Variables to save."
    )
    @magic_arguments.argument(
        '-t', '--to',
        help="Path to the file containing the cached variables."
    )
    @magic_arguments.argument(
        '-f', '--force', action='store_true', default=False,
        help="Force the cell's execution and save the variables."
    )
    @cell_magic
    def cache(self, line, cell):
        """Cache user variables in a file, and skip the cell if the cached
        variables exist.
        
        Usage::
        
            %%cache var1 var2 --to=myfile.pkl
            # If myfile.pkl doesn't exist, this cell is executed and 
            # var1 and var2 are saved in this file.
            # Otherwise, the cell is skipped and these variables are
            # injected from the file to the interactive namespace.
            var1 = ...
            var2 = ...
        
        """
        ip = self.shell
        args = magic_arguments.parse_argstring(self.cache, line)
        code = cell if cell.endswith('\n') else cell+'\n'
        path = args.to
        if not path:
            raise ValueError("The path needs to be specified with --to.")
        # If the cache file exists, and no --force mode, load the requested 
        # variables from the specified file into the interactive namespace.
        if os.path.exists(path) and not args.force:
            with open(path, 'r') as f:
                cache = cPickle.load(f)
                print(("Skipping the cell's code and loading variables {0:s} "
                       "from file '{1:s}'.").format(
                    ', '.join(sorted(cache.keys())), path))
                ip.push(cache)
        # Otherwise, execute the cell and save the variables.
        else:
            ip.run_cell(cell)
            print("Saving variables {0:s} to file '{1:s}'.".format(
                ', '.join(args.vars), path))
            cache = {}
            for var in args.vars:
                try:
                    cache[var] = ip.user_ns[var]
                except KeyError:
                    print(("Warning: variable '{0:s}' does not exist in the "
                           "interactive namespace.").format(var))
            with open(path, 'wb') as f:
                cPickle.dump(cache, f)
        

def load_ipython_extension(ip):
    """Load the extension in IPython."""
    ip.register_magics(CacheMagics)
    
