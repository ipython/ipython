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
import signal
import time
from subprocess import Popen, PIPE
import atexit

# Our own packages
from IPython.config.configurable import Configurable
from IPython.core import magic_arguments
from IPython.core.error import UsageError
from IPython.core.magic import  (
    Magics, magics_class, line_magic, cell_magic
)
from IPython.lib.backgroundjobs import BackgroundJobManager
from IPython.testing.skipdoctest import skip_doctest
from IPython.utils import py3compat
from IPython.utils.process import find_cmd, FindCmdError, arg_split
from IPython.utils.traitlets import List, Dict

#-----------------------------------------------------------------------------
# Magic implementation classes
#-----------------------------------------------------------------------------

def script_args(f):
    """single decorator for adding script args"""
    args = [
        magic_arguments.argument(
            '--out', type=str,
            help="""The variable in which to store stdout from the script.
            If the script is backgrounded, this will be the stdout *pipe*,
            instead of the stderr text itself.
            """
        ),
        magic_arguments.argument(
            '--err', type=str,
            help="""The variable in which to store stderr from the script.
            If the script is backgrounded, this will be the stderr *pipe*,
            instead of the stderr text itself.
            """
        ),
        magic_arguments.argument(
            '--bg', action="store_true",
            help="""Whether to run the script in the background.
            If given, the only way to see the output of the command is
            with --out/err.
            """
        ),
        magic_arguments.argument(
            '--proc', type=str,
            help="""The variable in which to store Popen instance.
            This is used only when --bg option is given.
            """
        ),
    ]
    for arg in args:
        f = arg(f)
    return f

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
        self.job_manager = BackgroundJobManager()
        self.bg_processes = []
        atexit.register(self.kill_bg_processes)

    def __del__(self):
        self.kill_bg_processes()
    
    def _generate_script_magics(self):
        cell_magics = self.magics['cell']
        for name in self.script_magics:
            cell_magics[name] = self._make_script_magic(name)
    
    def _make_script_magic(self, name):
        """make a named magic, that calls %%script with a particular program"""
        # expand to explicit path if necessary:
        script = self.script_paths.get(name, name)
        
        @magic_arguments.magic_arguments()
        @script_args
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
    
    @magic_arguments.magic_arguments()
    @script_args
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
        argv = arg_split(line, posix = not sys.platform.startswith('win'))
        args, cmd = self.shebang.parser.parse_known_args(argv)

        p = Popen(cmd, stdout=PIPE, stderr=PIPE, stdin=PIPE)
        
        cell = cell.encode('utf8', 'replace')
        if args.bg:
            self.bg_processes.append(p)
            self._gc_bg_processes()
            if args.out:
                self.shell.user_ns[args.out] = p.stdout
            if args.err:
                self.shell.user_ns[args.err] = p.stderr
            self.job_manager.new(self._run_script, p, cell, daemon=True)
            if args.proc:
                self.shell.user_ns[args.proc] = p
            return
        
        try:
            out, err = p.communicate(cell)
        except KeyboardInterrupt:
            try:
                p.send_signal(signal.SIGINT)
                time.sleep(0.1)
                if p.poll() is not None:
                    print "Process is interrupted."
                    return
                p.terminate()
                time.sleep(0.1)
                if p.poll() is not None:
                    print "Process is terminated."
                    return
                p.kill()
                print "Process is killed."
            except OSError:
                pass
            except Exception as e:
                print "Error while terminating subprocess (pid=%i): %s" \
                    % (p.pid, e)
            return
        out = py3compat.bytes_to_str(out)
        err = py3compat.bytes_to_str(err)
        if args.out:
            self.shell.user_ns[args.out] = out
        else:
            sys.stdout.write(out)
            sys.stdout.flush()
        if args.err:
            self.shell.user_ns[args.err] = err
        else:
            sys.stderr.write(err)
            sys.stderr.flush()
    
    def _run_script(self, p, cell):
        """callback for running the script in the background"""
        p.stdin.write(cell)
        p.stdin.close()
        p.wait()

    @line_magic("killbgscripts")
    def killbgscripts(self, _nouse_=''):
        """Kill all BG processes started by %%script and its family."""
        self.kill_bg_processes()
        print "All background processes were killed."

    def kill_bg_processes(self):
        """Kill all BG processes which are still running."""
        for p in self.bg_processes:
            if p.poll() is None:
                try:
                    p.send_signal(signal.SIGINT)
                except:
                    pass
        time.sleep(0.1)
        for p in self.bg_processes:
            if p.poll() is None:
                try:
                    p.terminate()
                except:
                    pass
        time.sleep(0.1)
        for p in self.bg_processes:
            if p.poll() is None:
                try:
                    p.kill()
                except:
                    pass
        self._gc_bg_processes()

    def _gc_bg_processes(self):
        self.bg_processes = [p for p in self.bg_processes if p.poll() is None]
