"""Magic functions for InteractiveShell.
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2001 Janko Hauser <jhauser@zscout.de> and
#  Copyright (C) 2001 Fernando Perez <fperez@colorado.edu>
#  Copyright (C) 2008 The IPython Development Team

#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Stdlib
import __builtin__ as builtin_mod
import bdb
import gc
import inspect
import io
import json
import os
import re
import sys
import time
from StringIO import StringIO
from pprint import pformat
from urllib2 import urlopen

# cProfile was added in Python2.5
try:
    import cProfile as profile
    import pstats
except ImportError:
    # profile isn't bundled by default in Debian for license reasons
    try:
        import profile, pstats
    except ImportError:
        profile = pstats = None

# Our own packages
from IPython.config.application import Application
from IPython.core import debugger, oinspect
from IPython.core import page
from IPython.core.error import UsageError, StdinNotImplementedError, TryNext
from IPython.core.macro import Macro
from IPython.core.magic import (Bunch, Magics, compress_dhist,
                                on_off, needs_local_scope,
                                register_magics, line_magic, cell_magic)
from IPython.testing.skipdoctest import skip_doctest
from IPython.utils import openpy
from IPython.utils import py3compat
from IPython.utils.encoding import DEFAULT_ENCODING
from IPython.utils.io import file_read, nlprint
from IPython.utils.ipstruct import Struct
from IPython.utils.module_paths import find_mod
from IPython.utils.path import get_py_filename, unquote_filename
from IPython.utils.process import abbrev_cwd
from IPython.utils.terminal import set_term_title
from IPython.utils.timing import clock, clock2
from IPython.utils.warn import warn, error

#-----------------------------------------------------------------------------
# Magic implementation classes
#-----------------------------------------------------------------------------

@register_magics
class AutoMagics(Magics):
    """Magics that control various autoX behaviors."""

    def __init__(self, shell):
        super(AutoMagics, self).__init__(shell)
        # namespace for holding state we may need
        self._magic_state = Bunch()

    @line_magic
    def automagic(self, parameter_s=''):
        """Make magic functions callable without having to type the initial %.

        Without argumentsl toggles on/off (when off, you must call it as
        %automagic, of course).  With arguments it sets the value, and you can
        use any of (case insensitive):

         - on, 1, True: to activate

         - off, 0, False: to deactivate.

        Note that magic functions have lowest priority, so if there's a
        variable whose name collides with that of a magic fn, automagic won't
        work for that function (you get the variable instead). However, if you
        delete the variable (del var), the previously shadowed magic function
        becomes visible to automagic again."""

        arg = parameter_s.lower()
        mman = self.shell.magics_manager
        if arg in ('on', '1', 'true'):
            val = True
        elif arg in ('off', '0', 'false'):
            val = False
        else:
            val = not mman.auto_magic
        mman.auto_magic = val
        print '\n' + self.shell.magics_manager.auto_status()

    @skip_doctest
    @line_magic
    def autocall(self, parameter_s=''):
        """Make functions callable without having to type parentheses.

        Usage:

           %autocall [mode]

        The mode can be one of: 0->Off, 1->Smart, 2->Full.  If not given, the
        value is toggled on and off (remembering the previous state).

        In more detail, these values mean:

        0 -> fully disabled

        1 -> active, but do not apply if there are no arguments on the line.

        In this mode, you get::

          In [1]: callable
          Out[1]: <built-in function callable>

          In [2]: callable 'hello'
          ------> callable('hello')
          Out[2]: False

        2 -> Active always.  Even if no arguments are present, the callable
        object is called::

          In [2]: float
          ------> float()
          Out[2]: 0.0

        Note that even with autocall off, you can still use '/' at the start of
        a line to treat the first argument on the command line as a function
        and add parentheses to it::

          In [8]: /str 43
          ------> str(43)
          Out[8]: '43'

        # all-random (note for auto-testing)
        """

        if parameter_s:
            arg = int(parameter_s)
        else:
            arg = 'toggle'

        if not arg in (0, 1, 2,'toggle'):
            error('Valid modes: (0->Off, 1->Smart, 2->Full')
            return

        if arg in (0, 1, 2):
            self.shell.autocall = arg
        else: # toggle
            if self.shell.autocall:
                self._magic_state.autocall_save = self.shell.autocall
                self.shell.autocall = 0
            else:
                try:
                    self.shell.autocall = self._magic_state.autocall_save
                except AttributeError:
                    self.shell.autocall = self._magic_state.autocall_save = 1

        print "Automatic calling is:",['OFF','Smart','Full'][self.shell.autocall]


@register_magics
class OSMagics(Magics):
    """Magics to interact with the underlying OS (shell-type functionality).
    """

    @skip_doctest
    @line_magic
    def alias(self, parameter_s=''):
        """Define an alias for a system command.

        '%alias alias_name cmd' defines 'alias_name' as an alias for 'cmd'

        Then, typing 'alias_name params' will execute the system command 'cmd
        params' (from your underlying operating system).

        Aliases have lower precedence than magic functions and Python normal
        variables, so if 'foo' is both a Python variable and an alias, the
        alias can not be executed until 'del foo' removes the Python variable.

        You can use the %l specifier in an alias definition to represent the
        whole line when the alias is called.  For example::

          In [2]: alias bracket echo "Input in brackets: <%l>"
          In [3]: bracket hello world
          Input in brackets: <hello world>

        You can also define aliases with parameters using %s specifiers (one
        per parameter)::

          In [1]: alias parts echo first %s second %s
          In [2]: %parts A B
          first A second B
          In [3]: %parts A
          Incorrect number of arguments: 2 expected.
          parts is an alias to: 'echo first %s second %s'

        Note that %l and %s are mutually exclusive.  You can only use one or
        the other in your aliases.

        Aliases expand Python variables just like system calls using ! or !!
        do: all expressions prefixed with '$' get expanded.  For details of
        the semantic rules, see PEP-215:
        http://www.python.org/peps/pep-0215.html.  This is the library used by
        IPython for variable expansion.  If you want to access a true shell
        variable, an extra $ is necessary to prevent its expansion by
        IPython::

          In [6]: alias show echo
          In [7]: PATH='A Python string'
          In [8]: show $PATH
          A Python string
          In [9]: show $$PATH
          /usr/local/lf9560/bin:/usr/local/intel/compiler70/ia32/bin:...

        You can use the alias facility to acess all of $PATH.  See the %rehash
        and %rehashx functions, which automatically create aliases for the
        contents of your $PATH.

        If called with no parameters, %alias prints the current alias table."""

        par = parameter_s.strip()
        if not par:
            aliases = sorted(self.shell.alias_manager.aliases)
            # stored = self.shell.db.get('stored_aliases', {} )
            # for k, v in stored:
            #     atab.append(k, v[0])

            print "Total number of aliases:", len(aliases)
            sys.stdout.flush()
            return aliases

        # Now try to define a new one
        try:
            alias,cmd = par.split(None, 1)
        except:
            print oinspect.getdoc(self.alias)
        else:
            self.shell.alias_manager.soft_define_alias(alias, cmd)
    # end magic_alias

    @line_magic
    def unalias(self, parameter_s=''):
        """Remove an alias"""

        aname = parameter_s.strip()
        self.shell.alias_manager.undefine_alias(aname)
        stored = self.shell.db.get('stored_aliases', {} )
        if aname in stored:
            print "Removing %stored alias",aname
            del stored[aname]
            self.shell.db['stored_aliases'] = stored

    @line_magic
    def rehashx(self, parameter_s=''):
        """Update the alias table with all executable files in $PATH.

        This version explicitly checks that every entry in $PATH is a file
        with execute access (os.X_OK), so it is much slower than %rehash.

        Under Windows, it checks executability as a match against a
        '|'-separated string of extensions, stored in the IPython config
        variable win_exec_ext.  This defaults to 'exe|com|bat'.

        This function also resets the root module cache of module completer,
        used on slow filesystems.
        """
        from IPython.core.alias import InvalidAliasError

        # for the benefit of module completer in ipy_completers.py
        del self.shell.db['rootmodules']

        path = [os.path.abspath(os.path.expanduser(p)) for p in
            os.environ.get('PATH','').split(os.pathsep)]
        path = filter(os.path.isdir,path)

        syscmdlist = []
        # Now define isexec in a cross platform manner.
        if os.name == 'posix':
            isexec = lambda fname:os.path.isfile(fname) and \
                     os.access(fname,os.X_OK)
        else:
            try:
                winext = os.environ['pathext'].replace(';','|').replace('.','')
            except KeyError:
                winext = 'exe|com|bat|py'
            if 'py' not in winext:
                winext += '|py'
            execre = re.compile(r'(.*)\.(%s)$' % winext,re.IGNORECASE)
            isexec = lambda fname:os.path.isfile(fname) and execre.match(fname)
        savedir = os.getcwdu()

        # Now walk the paths looking for executables to alias.
        try:
            # write the whole loop for posix/Windows so we don't have an if in
            # the innermost part
            if os.name == 'posix':
                for pdir in path:
                    os.chdir(pdir)
                    for ff in os.listdir(pdir):
                        if isexec(ff):
                            try:
                                # Removes dots from the name since ipython
                                # will assume names with dots to be python.
                                self.shell.alias_manager.define_alias(
                                    ff.replace('.',''), ff)
                            except InvalidAliasError:
                                pass
                            else:
                                syscmdlist.append(ff)
            else:
                no_alias = self.shell.alias_manager.no_alias
                for pdir in path:
                    os.chdir(pdir)
                    for ff in os.listdir(pdir):
                        base, ext = os.path.splitext(ff)
                        if isexec(ff) and base.lower() not in no_alias:
                            if ext.lower() == '.exe':
                                ff = base
                                try:
                                    # Removes dots from the name since ipython
                                    # will assume names with dots to be python.
                                    self.shell.alias_manager.define_alias(
                                        base.lower().replace('.',''), ff)
                                except InvalidAliasError:
                                    pass
                                syscmdlist.append(ff)
            self.shell.db['syscmdlist'] = syscmdlist
        finally:
            os.chdir(savedir)

    @skip_doctest
    @line_magic
    def pwd(self, parameter_s=''):
        """Return the current working directory path.

        Examples
        --------
        ::

          In [9]: pwd
          Out[9]: '/home/tsuser/sprint/ipython'
        """
        return os.getcwdu()

    @skip_doctest
    @line_magic
    def cd(self, parameter_s=''):
        """Change the current working directory.

        This command automatically maintains an internal list of directories
        you visit during your IPython session, in the variable _dh. The
        command %dhist shows this history nicely formatted. You can also
        do 'cd -<tab>' to see directory history conveniently.

        Usage:

          cd 'dir': changes to directory 'dir'.

          cd -: changes to the last visited directory.

          cd -<n>: changes to the n-th directory in the directory history.

          cd --foo: change to directory that matches 'foo' in history

          cd -b <bookmark_name>: jump to a bookmark set by %bookmark
             (note: cd <bookmark_name> is enough if there is no
              directory <bookmark_name>, but a bookmark with the name exists.)
              'cd -b <tab>' allows you to tab-complete bookmark names.

        Options:

        -q: quiet.  Do not print the working directory after the cd command is
        executed.  By default IPython's cd command does print this directory,
        since the default prompts do not display path information.

        Note that !cd doesn't work for this purpose because the shell where
        !command runs is immediately discarded after executing 'command'.

        Examples
        --------
        ::

          In [10]: cd parent/child
          /home/tsuser/parent/child
        """

        #bkms = self.shell.persist.get("bookmarks",{})

        oldcwd = os.getcwdu()
        numcd = re.match(r'(-)(\d+)$',parameter_s)
        # jump in directory history by number
        if numcd:
            nn = int(numcd.group(2))
            try:
                ps = self.shell.user_ns['_dh'][nn]
            except IndexError:
                print 'The requested directory does not exist in history.'
                return
            else:
                opts = {}
        elif parameter_s.startswith('--'):
            ps = None
            fallback = None
            pat = parameter_s[2:]
            dh = self.shell.user_ns['_dh']
            # first search only by basename (last component)
            for ent in reversed(dh):
                if pat in os.path.basename(ent) and os.path.isdir(ent):
                    ps = ent
                    break

                if fallback is None and pat in ent and os.path.isdir(ent):
                    fallback = ent

            # if we have no last part match, pick the first full path match
            if ps is None:
                ps = fallback

            if ps is None:
                print "No matching entry in directory history"
                return
            else:
                opts = {}


        else:
            #turn all non-space-escaping backslashes to slashes,
            # for c:\windows\directory\names\
            parameter_s = re.sub(r'\\(?! )','/', parameter_s)
            opts,ps = self.parse_options(parameter_s,'qb',mode='string')
        # jump to previous
        if ps == '-':
            try:
                ps = self.shell.user_ns['_dh'][-2]
            except IndexError:
                raise UsageError('%cd -: No previous directory to change to.')
        # jump to bookmark if needed
        else:
            if not os.path.isdir(ps) or opts.has_key('b'):
                bkms = self.shell.db.get('bookmarks', {})

                if bkms.has_key(ps):
                    target = bkms[ps]
                    print '(bookmark:%s) -> %s' % (ps,target)
                    ps = target
                else:
                    if opts.has_key('b'):
                        raise UsageError("Bookmark '%s' not found.  "
                              "Use '%%bookmark -l' to see your bookmarks." % ps)

        # strip extra quotes on Windows, because os.chdir doesn't like them
        ps = unquote_filename(ps)
        # at this point ps should point to the target dir
        if ps:
            try:
                os.chdir(os.path.expanduser(ps))
                if hasattr(self.shell, 'term_title') and self.shell.term_title:
                    set_term_title('IPython: ' + abbrev_cwd())
            except OSError:
                print sys.exc_info()[1]
            else:
                cwd = os.getcwdu()
                dhist = self.shell.user_ns['_dh']
                if oldcwd != cwd:
                    dhist.append(cwd)
                    self.shell.db['dhist'] = compress_dhist(dhist)[-100:]

        else:
            os.chdir(self.shell.home_dir)
            if hasattr(self.shell, 'term_title') and self.shell.term_title:
                set_term_title('IPython: ' + '~')
            cwd = os.getcwdu()
            dhist = self.shell.user_ns['_dh']

            if oldcwd != cwd:
                dhist.append(cwd)
                self.shell.db['dhist'] = compress_dhist(dhist)[-100:]
        if not 'q' in opts and self.shell.user_ns['_dh']:
            print self.shell.user_ns['_dh'][-1]


    @line_magic
    def env(self, parameter_s=''):
        """List environment variables."""

        return dict(os.environ)

    @line_magic
    def pushd(self, parameter_s=''):
        """Place the current dir on stack and change directory.

        Usage:\\
          %pushd ['dirname']
        """

        dir_s = self.shell.dir_stack
        tgt = os.path.expanduser(unquote_filename(parameter_s))
        cwd = os.getcwdu().replace(self.shell.home_dir,'~')
        if tgt:
            self.cd(parameter_s)
        dir_s.insert(0,cwd)
        return self.shell.magic('dirs')

    @line_magic
    def popd(self, parameter_s=''):
        """Change to directory popped off the top of the stack.
        """
        if not self.shell.dir_stack:
            raise UsageError("%popd on empty stack")
        top = self.shell.dir_stack.pop(0)
        self.cd(top)
        print "popd ->",top

    @line_magic
    def dirs(self, parameter_s=''):
        """Return the current directory stack."""

        return self.shell.dir_stack

    @line_magic
    def dhist(self, parameter_s=''):
        """Print your history of visited directories.

        %dhist       -> print full history\\
        %dhist n     -> print last n entries only\\
        %dhist n1 n2 -> print entries between n1 and n2 (n1 not included)\\

        This history is automatically maintained by the %cd command, and
        always available as the global list variable _dh. You can use %cd -<n>
        to go to directory number <n>.

        Note that most of time, you should view directory history by entering
        cd -<TAB>.

        """

        dh = self.shell.user_ns['_dh']
        if parameter_s:
            try:
                args = map(int,parameter_s.split())
            except:
                self.arg_err(self.dhist)
                return
            if len(args) == 1:
                ini,fin = max(len(dh)-(args[0]),0),len(dh)
            elif len(args) == 2:
                ini,fin = args
            else:
                self.arg_err(self.dhist)
                return
        else:
            ini,fin = 0,len(dh)
        nlprint(dh,
                header = 'Directory history (kept in _dh)',
                start=ini,stop=fin)

    @skip_doctest
    @line_magic
    def sc(self, parameter_s=''):
        """Shell capture - execute a shell command and capture its output.

        DEPRECATED. Suboptimal, retained for backwards compatibility.

        You should use the form 'var = !command' instead. Example:

         "%sc -l myfiles = ls ~" should now be written as

         "myfiles = !ls ~"

        myfiles.s, myfiles.l and myfiles.n still apply as documented
        below.

        --
        %sc [options] varname=command

        IPython will run the given command using commands.getoutput(), and
        will then update the user's interactive namespace with a variable
        called varname, containing the value of the call.  Your command can
        contain shell wildcards, pipes, etc.

        The '=' sign in the syntax is mandatory, and the variable name you
        supply must follow Python's standard conventions for valid names.

        (A special format without variable name exists for internal use)

        Options:

          -l: list output.  Split the output on newlines into a list before
          assigning it to the given variable.  By default the output is stored
          as a single string.

          -v: verbose.  Print the contents of the variable.

        In most cases you should not need to split as a list, because the
        returned value is a special type of string which can automatically
        provide its contents either as a list (split on newlines) or as a
        space-separated string.  These are convenient, respectively, either
        for sequential processing or to be passed to a shell command.

        For example::

            # Capture into variable a
            In [1]: sc a=ls *py

            # a is a string with embedded newlines
            In [2]: a
            Out[2]: 'setup.py\\nwin32_manual_post_install.py'

            # which can be seen as a list:
            In [3]: a.l
            Out[3]: ['setup.py', 'win32_manual_post_install.py']

            # or as a whitespace-separated string:
            In [4]: a.s
            Out[4]: 'setup.py win32_manual_post_install.py'

            # a.s is useful to pass as a single command line:
            In [5]: !wc -l $a.s
              146 setup.py
              130 win32_manual_post_install.py
              276 total

            # while the list form is useful to loop over:
            In [6]: for f in a.l:
              ...:      !wc -l $f
              ...:
            146 setup.py
            130 win32_manual_post_install.py

        Similarly, the lists returned by the -l option are also special, in
        the sense that you can equally invoke the .s attribute on them to
        automatically get a whitespace-separated string from their contents::

            In [7]: sc -l b=ls *py

            In [8]: b
            Out[8]: ['setup.py', 'win32_manual_post_install.py']

            In [9]: b.s
            Out[9]: 'setup.py win32_manual_post_install.py'

        In summary, both the lists and strings used for output capture have
        the following special attributes::

            .l (or .list) : value as list.
            .n (or .nlstr): value as newline-separated string.
            .s (or .spstr): value as space-separated string.
        """

        opts,args = self.parse_options(parameter_s,'lv')
        # Try to get a variable name and command to run
        try:
            # the variable name must be obtained from the parse_options
            # output, which uses shlex.split to strip options out.
            var,_ = args.split('=',1)
            var = var.strip()
            # But the command has to be extracted from the original input
            # parameter_s, not on what parse_options returns, to avoid the
            # quote stripping which shlex.split performs on it.
            _,cmd = parameter_s.split('=',1)
        except ValueError:
            var,cmd = '',''
        # If all looks ok, proceed
        split = 'l' in opts
        out = self.shell.getoutput(cmd, split=split)
        if opts.has_key('v'):
            print '%s ==\n%s' % (var,pformat(out))
        if var:
            self.shell.user_ns.update({var:out})
        else:
            return out

    @line_magic
    def sx(self, parameter_s=''):
        """Shell execute - run a shell command and capture its output.

        %sx command

        IPython will run the given command using commands.getoutput(), and
        return the result formatted as a list (split on '\\n').  Since the
        output is _returned_, it will be stored in ipython's regular output
        cache Out[N] and in the '_N' automatic variables.

        Notes:

        1) If an input line begins with '!!', then %sx is automatically
        invoked.  That is, while::

          !ls

        causes ipython to simply issue system('ls'), typing::

          !!ls

        is a shorthand equivalent to::

          %sx ls

        2) %sx differs from %sc in that %sx automatically splits into a list,
        like '%sc -l'.  The reason for this is to make it as easy as possible
        to process line-oriented shell output via further python commands.
        %sc is meant to provide much finer control, but requires more
        typing.

        3) Just like %sc -l, this is a list with special attributes:
        ::

          .l (or .list) : value as list.
          .n (or .nlstr): value as newline-separated string.
          .s (or .spstr): value as whitespace-separated string.

        This is very useful when trying to use such lists as arguments to
        system commands."""

        if parameter_s:
            return self.shell.getoutput(parameter_s)


    @line_magic
    def bookmark(self, parameter_s=''):
        """Manage IPython's bookmark system.

        %bookmark <name>       - set bookmark to current dir
        %bookmark <name> <dir> - set bookmark to <dir>
        %bookmark -l           - list all bookmarks
        %bookmark -d <name>    - remove bookmark
        %bookmark -r           - remove all bookmarks

        You can later on access a bookmarked folder with::

          %cd -b <name>

        or simply '%cd <name>' if there is no directory called <name> AND
        there is such a bookmark defined.

        Your bookmarks persist through IPython sessions, but they are
        associated with each profile."""

        opts,args = self.parse_options(parameter_s,'drl',mode='list')
        if len(args) > 2:
            raise UsageError("%bookmark: too many arguments")

        bkms = self.shell.db.get('bookmarks',{})

        if opts.has_key('d'):
            try:
                todel = args[0]
            except IndexError:
                raise UsageError(
                    "%bookmark -d: must provide a bookmark to delete")
            else:
                try:
                    del bkms[todel]
                except KeyError:
                    raise UsageError(
                        "%%bookmark -d: Can't delete bookmark '%s'" % todel)

        elif opts.has_key('r'):
            bkms = {}
        elif opts.has_key('l'):
            bks = bkms.keys()
            bks.sort()
            if bks:
                size = max(map(len,bks))
            else:
                size = 0
            fmt = '%-'+str(size)+'s -> %s'
            print 'Current bookmarks:'
            for bk in bks:
                print fmt % (bk,bkms[bk])
        else:
            if not args:
                raise UsageError("%bookmark: You must specify the bookmark name")
            elif len(args)==1:
                bkms[args[0]] = os.getcwdu()
            elif len(args)==2:
                bkms[args[0]] = args[1]
        self.shell.db['bookmarks'] = bkms

    @line_magic
    def pycat(self, parameter_s=''):
        """Show a syntax-highlighted file through a pager.

        This magic is similar to the cat utility, but it will assume the file
        to be Python source and will show it with syntax highlighting. """

        try:
            filename = get_py_filename(parameter_s)
            cont = file_read(filename)
        except IOError:
            try:
                cont = eval(parameter_s, self.shell.user_ns)
            except NameError:
                cont = None
        if cont is None:
            print "Error: no such file or variable"
            return

        page.page(self.shell.pycolorize(cont))


@register_magics
class LoggingMagics(Magics):
    """Magics related to all logging machinery."""

    @line_magic
    def logstart(self, parameter_s=''):
        """Start logging anywhere in a session.

        %logstart [-o|-r|-t] [log_name [log_mode]]

        If no name is given, it defaults to a file named 'ipython_log.py' in your
        current directory, in 'rotate' mode (see below).

        '%logstart name' saves to file 'name' in 'backup' mode.  It saves your
        history up to that point and then continues logging.

        %logstart takes a second optional parameter: logging mode. This can be one
        of (note that the modes are given unquoted):\\
          append: well, that says it.\\
          backup: rename (if exists) to name~ and start name.\\
          global: single logfile in your home dir, appended to.\\
          over  : overwrite existing log.\\
          rotate: create rotating logs name.1~, name.2~, etc.

        Options:

          -o: log also IPython's output.  In this mode, all commands which
          generate an Out[NN] prompt are recorded to the logfile, right after
          their corresponding input line.  The output lines are always
          prepended with a '#[Out]# ' marker, so that the log remains valid
          Python code.

          Since this marker is always the same, filtering only the output from
          a log is very easy, using for example a simple awk call::

            awk -F'#\\[Out\\]# ' '{if($2) {print $2}}' ipython_log.py

          -r: log 'raw' input.  Normally, IPython's logs contain the processed
          input, so that user lines are logged in their final form, converted
          into valid Python.  For example, %Exit is logged as
          _ip.magic("Exit").  If the -r flag is given, all input is logged
          exactly as typed, with no transformations applied.

          -t: put timestamps before each input line logged (these are put in
          comments)."""

        opts,par = self.parse_options(parameter_s,'ort')
        log_output = 'o' in opts
        log_raw_input = 'r' in opts
        timestamp = 't' in opts

        logger = self.shell.logger

        # if no args are given, the defaults set in the logger constructor by
        # ipython remain valid
        if par:
            try:
                logfname,logmode = par.split()
            except:
                logfname = par
                logmode = 'backup'
        else:
            logfname = logger.logfname
            logmode = logger.logmode
        # put logfname into rc struct as if it had been called on the command
        # line, so it ends up saved in the log header Save it in case we need
        # to restore it...
        old_logfile = self.shell.logfile
        if logfname:
            logfname = os.path.expanduser(logfname)
        self.shell.logfile = logfname

        loghead = '# IPython log file\n\n'
        try:
            logger.logstart(logfname, loghead, logmode, log_output, timestamp,
                            log_raw_input)
        except:
            self.shell.logfile = old_logfile
            warn("Couldn't start log: %s" % sys.exc_info()[1])
        else:
            # log input history up to this point, optionally interleaving
            # output if requested

            if timestamp:
                # disable timestamping for the previous history, since we've
                # lost those already (no time machine here).
                logger.timestamp = False

            if log_raw_input:
                input_hist = self.shell.history_manager.input_hist_raw
            else:
                input_hist = self.shell.history_manager.input_hist_parsed

            if log_output:
                log_write = logger.log_write
                output_hist = self.shell.history_manager.output_hist
                for n in range(1,len(input_hist)-1):
                    log_write(input_hist[n].rstrip() + '\n')
                    if n in output_hist:
                        log_write(repr(output_hist[n]),'output')
            else:
                logger.log_write('\n'.join(input_hist[1:]))
                logger.log_write('\n')
            if timestamp:
                # re-enable timestamping
                logger.timestamp = True

            print ('Activating auto-logging. '
                   'Current session state plus future input saved.')
            logger.logstate()

    @line_magic
    def logstop(self, parameter_s=''):
        """Fully stop logging and close log file.

        In order to start logging again, a new %logstart call needs to be made,
        possibly (though not necessarily) with a new filename, mode and other
        options."""
        self.logger.logstop()

    @line_magic
    def logoff(self, parameter_s=''):
        """Temporarily stop logging.

        You must have previously started logging."""
        self.shell.logger.switch_log(0)

    @line_magic
    def logon(self, parameter_s=''):
        """Restart logging.

        This function is for restarting logging which you've temporarily
        stopped with %logoff. For starting logging for the first time, you
        must use the %logstart function, which allows you to specify an
        optional log filename."""

        self.shell.logger.switch_log(1)

    @line_magic
    def logstate(self, parameter_s=''):
        """Print the status of the logging system."""

        self.shell.logger.logstate()


@register_magics
class ExtensionsMagics(Magics):
    """Magics to manage the IPython extensions system."""

    @line_magic
    def install_ext(self, parameter_s=''):
        """Download and install an extension from a URL, e.g.::

            %install_ext https://bitbucket.org/birkenfeld/ipython-physics/raw/d1310a2ab15d/physics.py

        The URL should point to an importable Python module - either a .py file
        or a .zip file.

        Parameters:

          -n filename : Specify a name for the file, rather than taking it from
                        the URL.
        """
        opts, args = self.parse_options(parameter_s, 'n:')
        try:
            filename = self.shell.extension_manager.install_extension(args,
                                                                 opts.get('n'))
        except ValueError as e:
            print e
            return

        filename = os.path.basename(filename)
        print "Installed %s. To use it, type:" % filename
        print "  %%load_ext %s" % os.path.splitext(filename)[0]


    @line_magic
    def load_ext(self, module_str):
        """Load an IPython extension by its module name."""
        return self.shell.extension_manager.load_extension(module_str)

    @line_magic
    def unload_ext(self, module_str):
        """Unload an IPython extension by its module name."""
        self.shell.extension_manager.unload_extension(module_str)

    @line_magic
    def reload_ext(self, module_str):
        """Reload an IPython extension by its module name."""
        self.shell.extension_manager.reload_extension(module_str)


@register_magics
class PylabMagics(Magics):
    """Magics related to matplotlib's pylab support"""

    @skip_doctest
    @line_magic
    def pylab(self, parameter_s=''):
        """Load numpy and matplotlib to work interactively.

        %pylab [GUINAME]

        This function lets you activate pylab (matplotlib, numpy and
        interactive support) at any point during an IPython session.

        It will import at the top level numpy as np, pyplot as plt, matplotlib,
        pylab and mlab, as well as all names from numpy and pylab.

        If you are using the inline matplotlib backend for embedded figures,
        you can adjust its behavior via the %config magic::

            # enable SVG figures, necessary for SVG+XHTML export in the qtconsole
            In [1]: %config InlineBackend.figure_format = 'svg'

            # change the behavior of closing all figures at the end of each
            # execution (cell), or allowing reuse of active figures across
            # cells:
            In [2]: %config InlineBackend.close_figures = False

        Parameters
        ----------
        guiname : optional
          One of the valid arguments to the %gui magic ('qt', 'wx', 'gtk',
          'osx' or 'tk').  If given, the corresponding Matplotlib backend is
          used, otherwise matplotlib's default (which you can override in your
          matplotlib config file) is used.

        Examples
        --------
        In this case, where the MPL default is TkAgg::

            In [2]: %pylab

            Welcome to pylab, a matplotlib-based Python environment.
            Backend in use: TkAgg
            For more information, type 'help(pylab)'.

        But you can explicitly request a different backend::

            In [3]: %pylab qt

            Welcome to pylab, a matplotlib-based Python environment.
            Backend in use: Qt4Agg
            For more information, type 'help(pylab)'.
        """

        if Application.initialized():
            app = Application.instance()
            try:
                import_all_status = app.pylab_import_all
            except AttributeError:
                import_all_status = True
        else:
            import_all_status = True

        self.shell.enable_pylab(parameter_s, import_all=import_all_status)


@register_magics
class DeprecatedMagics(Magics):
    """Magics slated for later removal."""

    @line_magic
    def install_profiles(self, parameter_s=''):
        """%install_profiles has been deprecated."""
        print '\n'.join([
            "%install_profiles has been deprecated.",
            "Use `ipython profile list` to view available profiles.",
            "Requesting a profile with `ipython profile create <name>`",
            "or `ipython --profile=<name>` will start with the bundled",
            "profile of that name if it exists."
        ])

    @line_magic
    def install_default_config(self, parameter_s=''):
        """%install_default_config has been deprecated."""
        print '\n'.join([
            "%install_default_config has been deprecated.",
            "Use `ipython profile create <name>` to initialize a profile",
            "with the default config files.",
            "Add `--reset` to overwrite already existing config files with defaults."
        ])
