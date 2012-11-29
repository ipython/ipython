#!/usr/bin/env python
"""Module for interactively running scripts.

This module implements classes for interactively running scripts written for
any system with a prompt which can be matched by a regexp suitable for
pexpect.  It can be used to run as if they had been typed up interactively, an
arbitrary series of commands for the target system.

The module includes classes ready for IPython (with the default prompts),
plain Python and SAGE, but making a new one is trivial.  To see how to use it,
simply run the module as a script:

./irunner.py --help


This is an extension of Ken Schutte <kschutte-AT-csail.mit.edu>'s script
contributed on the ipython-user list:

http://mail.scipy.org/pipermail/ipython-user/2006-May/003539.html

Notes
-----

 - This module requires pexpect, available in most linux distros, or which can
   be downloaded from http://pexpect.sourceforge.net

 - Because pexpect only works under Unix or Windows-Cygwin, this has the same
   limitations.  This means that it will NOT work under native windows Python.
"""
from __future__ import print_function

# Stdlib imports
import optparse
import os
import sys

# Third-party modules: we carry a copy of pexpect to reduce the need for
# external dependencies, but our import checks for a system version first.
from IPython.external import pexpect
from IPython.utils import py3compat

# Global usage strings, to avoid indentation issues when typing it below.
USAGE = """
Interactive script runner, type: %s

runner [opts] script_name
"""

def pexpect_monkeypatch():
    """Patch pexpect to prevent unhandled exceptions at VM teardown.

    Calling this function will monkeypatch the pexpect.spawn class and modify
    its __del__ method to make it more robust in the face of failures that can
    occur if it is called when the Python VM is shutting down.

    Since Python may fire __del__ methods arbitrarily late, it's possible for
    them to execute during the teardown of the Python VM itself.  At this
    point, various builtin modules have been reset to None.  Thus, the call to
    self.close() will trigger an exception because it tries to call os.close(),
    and os is now None.
    """

    if pexpect.__version__[:3] >= '2.2':
        # No need to patch, fix is already the upstream version.
        return

    def __del__(self):
        """This makes sure that no system resources are left open.
        Python only garbage collects Python objects. OS file descriptors
        are not Python objects, so they must be handled explicitly.
        If the child file descriptor was opened outside of this class
        (passed to the constructor) then this does not close it.
        """
        if not self.closed:
            try:
                self.close()
            except AttributeError:
                pass

    pexpect.spawn.__del__ = __del__

pexpect_monkeypatch()

# The generic runner class
class InteractiveRunner(object):
    """Class to run a sequence of commands through an interactive program."""

    def __init__(self,program,prompts,args=None,out=sys.stdout,echo=True):
        """Construct a runner.

        Inputs:

          - program: command to execute the given program.

          - prompts: a list of patterns to match as valid prompts, in the
          format used by pexpect.  This basically means that it can be either
          a string (to be compiled as a regular expression) or a list of such
          (it must be a true list, as pexpect does type checks).

          If more than one prompt is given, the first is treated as the main
          program prompt and the others as 'continuation' prompts, like
          python's.  This means that blank lines in the input source are
          ommitted when the first prompt is matched, but are NOT ommitted when
          the continuation one matches, since this is how python signals the
          end of multiline input interactively.

        Optional inputs:

          - args(None): optional list of strings to pass as arguments to the
          child program.

          - out(sys.stdout): if given, an output stream to be used when writing
          output.  The only requirement is that it must have a .write() method.

        Public members not parameterized in the constructor:

          - delaybeforesend(0): Newer versions of pexpect have a delay before
          sending each new input.  For our purposes here, it's typically best
          to just set this to zero, but if you encounter reliability problems
          or want an interactive run to pause briefly at each prompt, just
          increase this value (it is measured in seconds).  Note that this
          variable is not honored at all by older versions of pexpect.
        """

        self.program = program
        self.prompts = prompts
        if args is None: args = []
        self.args = args
        self.out = out
        self.echo = echo
        # Other public members which we don't make as parameters, but which
        # users may occasionally want to tweak
        self.delaybeforesend = 0

        # Create child process and hold on to it so we don't have to re-create
        # for every single execution call
        c = self.child = pexpect.spawn(self.program,self.args,timeout=None)
        c.delaybeforesend = self.delaybeforesend
        # pexpect hard-codes the terminal size as (24,80) (rows,columns).
        # This causes problems because any line longer than 80 characters gets
        # completely overwrapped on the printed outptut (even though
        # internally the code runs fine).  We reset this to 99 rows X 200
        # columns (arbitrarily chosen), which should avoid problems in all
        # reasonable cases.
        c.setwinsize(99,200)

    def close(self):
        """close child process"""

        self.child.close()

    def run_file(self,fname,interact=False,get_output=False):
        """Run the given file interactively.

        Inputs:

          -fname: name of the file to execute.

        See the run_source docstring for the meaning of the optional
        arguments."""

        fobj = open(fname,'r')
        try:
            out = self.run_source(fobj,interact,get_output)
        finally:
            fobj.close()
        if get_output:
            return out

    def run_source(self,source,interact=False,get_output=False):
        """Run the given source code interactively.

        Inputs:

          - source: a string of code to be executed, or an open file object we
          can iterate over.

        Optional inputs:

          - interact(False): if true, start to interact with the running
          program at the end of the script.  Otherwise, just exit.

          - get_output(False): if true, capture the output of the child process
          (filtering the input commands out) and return it as a string.

        Returns:
          A string containing the process output, but only if requested.
          """

        # if the source is a string, chop it up in lines so we can iterate
        # over it just as if it were an open file.
        if isinstance(source, basestring):
            source = source.splitlines(True)

        if self.echo:
            # normalize all strings we write to use the native OS line
            # separators.
            linesep  = os.linesep
            stdwrite = self.out.write
            write    = lambda s: stdwrite(s.replace('\r\n',linesep))
        else:
            # Quiet mode, all writes are no-ops
            write = lambda s: None

        c = self.child
        prompts = c.compile_pattern_list(self.prompts)
        prompt_idx = c.expect_list(prompts)

        # Flag whether the script ends normally or not, to know whether we can
        # do anything further with the underlying process.
        end_normal = True

        # If the output was requested, store it in a list for return at the end
        if get_output:
            output = []
            store_output = output.append

        for cmd in source:
            # skip blank lines for all matches to the 'main' prompt, while the
            # secondary prompts do not
            if prompt_idx==0 and \
                   (cmd.isspace() or cmd.lstrip().startswith('#')):
                write(cmd)
                continue

            # write('AFTER: '+c.after)  # dbg
            write(c.after)
            c.send(cmd)
            try:
                prompt_idx = c.expect_list(prompts)
            except pexpect.EOF:
                # this will happen if the child dies unexpectedly
                write(c.before)
                end_normal = False
                break

            write(c.before)

            # With an echoing process, the output we get in c.before contains
            # the command sent, a newline, and then the actual process output
            if get_output:
                store_output(c.before[len(cmd+'\n'):])
                #write('CMD: <<%s>>' % cmd)  # dbg
                #write('OUTPUT: <<%s>>' % output[-1])  # dbg

        self.out.flush()
        if end_normal:
            if interact:
                c.send('\n')
                print('<< Starting interactive mode >>', end=' ')
                try:
                    c.interact()
                except OSError:
                    # This is what fires when the child stops.  Simply print a
                    # newline so the system prompt is aligned.  The extra
                    # space is there to make sure it gets printed, otherwise
                    # OS buffering sometimes just suppresses it.
                    write(' \n')
                    self.out.flush()
        else:
            if interact:
                e="Further interaction is not possible: child process is dead."
                print(e, file=sys.stderr)

        # Leave the child ready for more input later on, otherwise select just
        # hangs on the second invocation.
        if c.isalive():
            c.send('\n')

        # Return any requested output
        if get_output:
            return ''.join(output)

    def main(self,argv=None):
        """Run as a command-line script."""

        parser = optparse.OptionParser(usage=USAGE % self.__class__.__name__)
        newopt = parser.add_option
        newopt('-i','--interact',action='store_true',default=False,
               help='Interact with the program after the script is run.')

        opts,args = parser.parse_args(argv)

        if len(args) != 1:
            print("You must supply exactly one file to run.", file=sys.stderr)
            sys.exit(1)

        self.run_file(args[0],opts.interact)

_ipython_cmd = "ipython3" if py3compat.PY3 else "ipython"

# Specific runners for particular programs
class IPythonRunner(InteractiveRunner):
    """Interactive IPython runner.

    This initalizes IPython in 'nocolor' mode for simplicity.  This lets us
    avoid having to write a regexp that matches ANSI sequences, though pexpect
    does support them.  If anyone contributes patches for ANSI color support,
    they will be welcome.

    It also sets the prompts manually, since the prompt regexps for
    pexpect need to be matched to the actual prompts, so user-customized
    prompts would break this.
    """

    def __init__(self,program = _ipython_cmd, args=None, out=sys.stdout, echo=True):
        """New runner, optionally passing the ipython command to use."""
        args0 = ['--colors=NoColor',
                 '--no-term-title',
                 '--no-autoindent',
                 # '--quick' is important, to prevent loading default config:
                 '--quick']
        if args is None: args = args0
        else: args = args0 + args
        prompts = [r'In \[\d+\]: ',r'   \.*: ']
        InteractiveRunner.__init__(self,program,prompts,args,out,echo)


class PythonRunner(InteractiveRunner):
    """Interactive Python runner."""

    def __init__(self,program=sys.executable, args=None, out=sys.stdout, echo=True):
        """New runner, optionally passing the python command to use."""

        prompts = [r'>>> ',r'\.\.\. ']
        InteractiveRunner.__init__(self,program,prompts,args,out,echo)


class SAGERunner(InteractiveRunner):
    """Interactive SAGE runner.

    WARNING: this runner only works if you manually adjust your SAGE
    configuration so that the 'color' option in the configuration file is set to
    'NoColor', because currently the prompt matching regexp does not identify
    color sequences."""

    def __init__(self,program='sage',args=None,out=sys.stdout,echo=True):
        """New runner, optionally passing the sage command to use."""

        prompts = ['sage: ',r'\s*\.\.\. ']
        InteractiveRunner.__init__(self,program,prompts,args,out,echo)


class RunnerFactory(object):
    """Code runner factory.

    This class provides an IPython code runner, but enforces that only one
    runner is ever instantiated.  The runner is created based on the extension
    of the first file to run, and it raises an exception if a runner is later
    requested for a different extension type.

    This ensures that we don't generate example files for doctest with a mix of
    python and ipython syntax.
    """

    def __init__(self,out=sys.stdout):
        """Instantiate a code runner."""

        self.out = out
        self.runner = None
        self.runnerClass = None

    def _makeRunner(self,runnerClass):
        self.runnerClass = runnerClass
        self.runner = runnerClass(out=self.out)
        return self.runner

    def __call__(self,fname):
        """Return a runner for the given filename."""

        if fname.endswith('.py'):
            runnerClass = PythonRunner
        elif fname.endswith('.ipy'):
            runnerClass = IPythonRunner
        else:
            raise ValueError('Unknown file type for Runner: %r' % fname)

        if self.runner is None:
            return self._makeRunner(runnerClass)
        else:
            if runnerClass==self.runnerClass:
                return self.runner
            else:
                e='A runner of type %r can not run file %r' % \
                   (self.runnerClass,fname)
                raise ValueError(e)


# Global usage string, to avoid indentation issues if typed in a function def.
MAIN_USAGE = """
%prog [options] file_to_run

This is an interface to the various interactive runners available in this
module.  If you want to pass specific options to one of the runners, you need
to first terminate the main options with a '--', and then provide the runner's
options.  For example:

irunner.py --python -- --help

will pass --help to the python runner.  Similarly,

irunner.py --ipython -- --interact script.ipy

will run the script.ipy file under the IPython runner, and then will start to
interact with IPython at the end of the script (instead of exiting).

The already implemented runners are listed below; adding one for a new program
is a trivial task, see the source for examples.
"""

def main():
    """Run as a command-line script."""

    parser = optparse.OptionParser(usage=MAIN_USAGE)
    newopt = parser.add_option
    newopt('--ipython',action='store_const',dest='mode',const='ipython',
           help='IPython interactive runner (default).')
    newopt('--python',action='store_const',dest='mode',const='python',
           help='Python interactive runner.')
    newopt('--sage',action='store_const',dest='mode',const='sage',
           help='SAGE interactive runner.')

    opts,args = parser.parse_args()
    runners = dict(ipython=IPythonRunner,
                   python=PythonRunner,
                   sage=SAGERunner)

    try:
        ext = os.path.splitext(args[0])[-1]
    except IndexError:
        ext = ''
    modes = {'.ipy':'ipython',
             '.py':'python',
             '.sage':'sage'}
    mode = modes.get(ext,"ipython")
    if opts.mode:
        mode = opts.mode
    runners[mode]().main(args)

if __name__ == '__main__':
    main()
