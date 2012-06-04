"""Magic functions for running cells in various scripts."""
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

# Stdlib
import os
import re
import sys
from subprocess import Popen, PIPE

# Our own packages
from IPython.config.configurable import Configurable
from IPython.core.error import UsageError
from IPython.core.magic import  (
    Magics, magics_class, line_magic, cell_magic
)
from IPython.testing.skipdoctest import skip_doctest
from IPython.utils.process import find_cmd, FindCmdError
from IPython.utils.traitlets import List, Dict

#-----------------------------------------------------------------------------
# Magic implementation classes
#-----------------------------------------------------------------------------

@magics_class
class ScriptMagics(Magics, Configurable):
    """Magics for talking to scripts
    
    This defines a base `%%script` cell magic for running a cell
    with a program in a subprocess, and registers a few top-level
    magics that call %%script with common interpreters.
    """
    script_magics = List(config=True,
        help="""Extra script cell magics to define
        
        This generates simple wrappers of `%%script foo` as `%%foo`.
        
        If you want to add script magics that aren't on your path,
        specify them in script_paths
        """,
    )
    def _script_magics_default(self):
        """default to a common list of programs if we find them"""
        
        defaults = []
        to_try = []
        if os.name == 'nt':
            defaults.append('cmd')
            to_try.append('powershell')
        to_try.extend([
            'sh',
            'bash',
            'perl',
            'ruby',
            'python3',
            'pypy',
        ])
        
        for cmd in to_try:
            if cmd in self.script_paths:
                defaults.append(cmd)
            else:
                try:
                    find_cmd(cmd)
                except FindCmdError:
                    # command not found, ignore it
                    pass
                except ImportError:
                    # Windows without pywin32, find_cmd doesn't work
                    pass
                else:
                    defaults.append(cmd)
        return defaults
    
    script_paths = Dict(config=True,
        help="""Dict mapping short 'ruby' names to full paths, such as '/opt/secret/bin/ruby'
        
        Only necessary for items in script_magics where the default path will not
        find the right interpreter.
        """
    )
    
    def __init__(self, shell=None):
        Configurable.__init__(self, config=shell.config)
        self._generate_script_magics()
        Magics.__init__(self, shell=shell)
    
    def _generate_script_magics(self):
        cell_magics = self.magics['cell']
        for name in self.script_magics:
            cell_magics[name] = self._make_script_magic(name)
    
    def _make_script_magic(self, name):
        """make a named magic, that calls %%script with a particular program"""
        # expand to explicit path if necessary:
        script = self.script_paths.get(name, name)
        
        def named_script_magic(line, cell):
            # if line, add it as cl-flags
            if line:
                 line = "%s %s" % (script, line)
            else:
                line = script
            return self.shebang(line, cell)
        
        # write a basic docstring:
        named_script_magic.__doc__ = \
        """%%{name} script magic
        
        Run cells with {script} in a subprocess.
        
        This is a shortcut for `%%script {script}`
        """.format(**locals())
        
        return named_script_magic

    @cell_magic("script")
    def shebang(self, line, cell):
        """Run a cell via a shell command
        
        The `%%script` line is like the #! line of script,
        specifying a program (bash, perl, ruby, etc.) with which to run.
        
        The rest of the cell is run by that program.
        
        Examples
        --------
        ::
        
            In [1]: %%script bash
               ...: for i in 1 2 3; do
               ...:   echo $i
               ...: done
            1
            2
            3
        """
        p = Popen(line, stdout=PIPE, stderr=PIPE, stdin=PIPE)
        out,err = p.communicate(cell)
        sys.stdout.write(out)
        sys.stdout.flush()
        sys.stderr.write(err)
        sys.stderr.flush()
    
    # expose %%script as %%!
    cell_magic('!')(shebang)
