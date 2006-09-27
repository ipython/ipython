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

http://scipy.net/pipermail/ipython-user/2006-May/001705.html


NOTES:

 - This module requires pexpect, available in most linux distros, or which can
 be downloaded from

    http://pexpect.sourceforge.net

 - Because pexpect only works under Unix or Windows-Cygwin, this has the same
 limitations.  This means that it will NOT work under native windows Python.
"""

# Stdlib imports
import optparse
import os
import sys

# Third-party modules.
import pexpect

# Global usage strings, to avoid indentation issues when typing it below.
USAGE = """
Interactive script runner, type: %s

runner [opts] script_name
"""

# The generic runner class
class InteractiveRunner(object):
    """Class to run a sequence of commands through an interactive program."""
    
    def __init__(self,program,prompts,args=None):
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
        # Other public members which we don't make as parameters, but which
        # users may occasionally want to tweak
        self.delaybeforesend = 0
        
    def run_file(self,fname,interact=False):
        """Run the given file interactively.

        Inputs:

          -fname: name of the file to execute.

        See the run_source docstring for the meaning of the optional
        arguments."""

        fobj = open(fname,'r')
        try:
            self.run_source(fobj,interact)
        finally:
            fobj.close()

    def run_source(self,source,interact=False):
        """Run the given source code interactively.

        Inputs:

          - source: a string of code to be executed, or an open file object we
          can iterate over.

        Optional inputs:

          - interact(False): if true, start to interact with the running
          program at the end of the script.  Otherwise, just exit.
          """

        # if the source is a string, chop it up in lines so we can iterate
        # over it just as if it were an open file.
        if not isinstance(source,file):
            source = source.splitlines(True)

        # grab the true write method of stdout, in case anything later
        # reassigns sys.stdout, so that we really are writing to the true
        # stdout and not to something else.  We also normalize all strings we
        # write to use the native OS line separators.
        linesep  = os.linesep
        stdwrite = sys.stdout.write
        write    = lambda s: stdwrite(s.replace('\r\n',linesep))

        c = pexpect.spawn(self.program,self.args,timeout=None)
        c.delaybeforesend = self.delaybeforesend
            
        prompts = c.compile_pattern_list(self.prompts)

        prompt_idx = c.expect_list(prompts)
        # Flag whether the script ends normally or not, to know whether we can
        # do anything further with the underlying process.
        end_normal = True
        for cmd in source:
            # skip blank lines for all matches to the 'main' prompt, while the
            # secondary prompts do not
            if prompt_idx==0 and \
                   (cmd.isspace() or cmd.lstrip().startswith('#')):
                print cmd,
                continue

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
        
        if end_normal:
            if interact:
                c.send('\n')
                print '<< Starting interactive mode >>',
                try:
                    c.interact()
                except OSError:
                    # This is what fires when the child stops.  Simply print a
                    # newline so the system prompt is aligned.  The extra
                    # space is there to make sure it gets printed, otherwise
                    # OS buffering sometimes just suppresses it.
                    write(' \n')
                    sys.stdout.flush()
            else:
                c.close()
        else:
            if interact:
                e="Further interaction is not possible: child process is dead."
                print >> sys.stderr, e
                
    def main(self,argv=None):
        """Run as a command-line script."""

        parser = optparse.OptionParser(usage=USAGE % self.__class__.__name__)
        newopt = parser.add_option
        newopt('-i','--interact',action='store_true',default=False,
               help='Interact with the program after the script is run.')

        opts,args = parser.parse_args(argv)

        if len(args) != 1:
            print >> sys.stderr,"You must supply exactly one file to run."
            sys.exit(1)

        self.run_file(args[0],opts.interact)


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
    
    def __init__(self,program = 'ipython',args=None):
        """New runner, optionally passing the ipython command to use."""
        
        args0 = ['-colors','NoColor',
                 '-pi1','In [\\#]: ',
                 '-pi2','   .\\D.: ']
        if args is None: args = args0
        else: args = args0 + args
        prompts = [r'In \[\d+\]: ',r'   \.*: ']
        InteractiveRunner.__init__(self,program,prompts,args)


class PythonRunner(InteractiveRunner):
    """Interactive Python runner."""

    def __init__(self,program='python',args=None):
        """New runner, optionally passing the python command to use."""

        prompts = [r'>>> ',r'\.\.\. ']
        InteractiveRunner.__init__(self,program,prompts,args)


class SAGERunner(InteractiveRunner):
    """Interactive SAGE runner.
    
    WARNING: this runner only works if you manually configure your SAGE copy
    to use 'colors NoColor' in the ipythonrc config file, since currently the
    prompt matching regexp does not identify color sequences."""

    def __init__(self,program='sage',args=None):
        """New runner, optionally passing the sage command to use."""

        prompts = ['sage: ',r'\s*\.\.\. ']
        InteractiveRunner.__init__(self,program,prompts,args)

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

WARNING: the SAGE runner only works if you manually configure your SAGE copy
to use 'colors NoColor' in the ipythonrc config file, since currently the
prompt matching regexp does not identify color sequences.
"""

def main():
    """Run as a command-line script."""

    parser = optparse.OptionParser(usage=MAIN_USAGE)
    newopt = parser.add_option
    parser.set_defaults(mode='ipython')
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
    runners[opts.mode]().main(args)

if __name__ == '__main__':
    main()
