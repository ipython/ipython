'''Pexpect is a Python module for spawning child applications and controlling
them automatically. Pexpect can be used for automating interactive applications
such as ssh, ftp, passwd, telnet, etc. It can be used to a automate setup
scripts for duplicating software package installations on different servers. It
can be used for automated software testing. Pexpect is in the spirit of Don
Libes' Expect, but Pexpect is pure Python. Other Expect-like modules for Python
require TCL and Expect or require C extensions to be compiled. Pexpect does not
use C, Expect, or TCL extensions. It should work on any platform that supports
the standard Python pty module. The Pexpect interface focuses on ease of use so
that simple tasks are easy.

There are two main interfaces to the Pexpect system; these are the function,
run() and the class, spawn. The spawn class is more powerful. The run()
function is simpler than spawn, and is good for quickly calling program. When
you call the run() function it executes a given program and then returns the
output. This is a handy replacement for os.system().

For example::

    pexpect.run('ls -la')

The spawn class is the more powerful interface to the Pexpect system. You can
use this to spawn a child program then interact with it by sending input and
expecting responses (waiting for patterns in the child's output).

For example::

    child = pexpect.spawn('scp foo user@example.com:.')
    child.expect('Password:')
    child.sendline(mypassword)

This works even for commands that ask for passwords or other input outside of
the normal stdio streams. For example, ssh reads input directly from the TTY
device which bypasses stdin.

Credits: Noah Spurrier, Richard Holden, Marco Molteni, Kimberley Burchett,
Robert Stone, Hartmut Goebel, Chad Schroeder, Erick Tryzelaar, Dave Kirby, Ids
vander Molen, George Todd, Noel Taylor, Nicolas D. Cesar, Alexander Gattin,
Jacques-Etienne Baudoux, Geoffrey Marshall, Francisco Lourenco, Glen Mabey,
Karthik Gurusamy, Fernando Perez, Corey Minyard, Jon Cohen, Guillaume
Chazarain, Andrew Ryan, Nick Craig-Wood, Andrew Stone, Jorgen Grahn, John
Spiegel, Jan Grant, and Shane Kerr. Let me know if I forgot anyone.

Pexpect is free, open source, and all that good stuff.
http://pexpect.sourceforge.net/

PEXPECT LICENSE

    This license is approved by the OSI and FSF as GPL-compatible.
        http://opensource.org/licenses/isc-license.txt

    Copyright (c) 2012, Noah Spurrier <noah@noah.org>
    PERMISSION TO USE, COPY, MODIFY, AND/OR DISTRIBUTE THIS SOFTWARE FOR ANY
    PURPOSE WITH OR WITHOUT FEE IS HEREBY GRANTED, PROVIDED THAT THE ABOVE
    COPYRIGHT NOTICE AND THIS PERMISSION NOTICE APPEAR IN ALL COPIES.
    THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
    WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
    MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
    ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
    WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
    ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
    OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

'''

try:
    import os
    import sys
    import time
    import select
    import re
    import struct
    import resource
    import types
    import pty
    import tty
    import termios
    import fcntl
    import errno
    import traceback
    import signal
    import codecs
except ImportError:  # pragma: no cover
    err = sys.exc_info()[1]
    raise ImportError(str(err) + '''

A critical module was not found. Probably this operating system does not
support it. Pexpect is intended for UNIX-like operating systems.''')

__version__ = '3.2'
__revision__ = ''
__all__ = ['ExceptionPexpect', 'EOF', 'TIMEOUT', 'spawn', 'spawnu', 'run', 'runu',
           'which', 'split_command_line', '__version__', '__revision__']

PY3 = (sys.version_info[0] >= 3)

# Exception classes used by this module.
class ExceptionPexpect(Exception):
    '''Base class for all exceptions raised by this module.
    '''

    def __init__(self, value):
        super(ExceptionPexpect, self).__init__(value)
        self.value = value

    def __str__(self):
        return str(self.value)

    def get_trace(self):
        '''This returns an abbreviated stack trace with lines that only concern
        the caller. In other words, the stack trace inside the Pexpect module
        is not included. '''

        tblist = traceback.extract_tb(sys.exc_info()[2])
        tblist = [item for item in tblist if 'pexpect/__init__' not in item[0]]
        tblist = traceback.format_list(tblist)
        return ''.join(tblist)


class EOF(ExceptionPexpect):
    '''Raised when EOF is read from a child.
    This usually means the child has exited.'''


class TIMEOUT(ExceptionPexpect):
    '''Raised when a read time exceeds the timeout. '''

##class TIMEOUT_PATTERN(TIMEOUT):
##    '''Raised when the pattern match time exceeds the timeout.
##    This is different than a read TIMEOUT because the child process may
##    give output, thus never give a TIMEOUT, but the output
##    may never match a pattern.
##    '''
##class MAXBUFFER(ExceptionPexpect):
##    '''Raised when a buffer fills before matching an expected pattern.'''


def run(command, timeout=-1, withexitstatus=False, events=None,
        extra_args=None, logfile=None, cwd=None, env=None):

    '''
    This function runs the given command; waits for it to finish; then
    returns all output as a string. STDERR is included in output. If the full
    path to the command is not given then the path is searched.

    Note that lines are terminated by CR/LF (\\r\\n) combination even on
    UNIX-like systems because this is the standard for pseudottys. If you set
    'withexitstatus' to true, then run will return a tuple of (command_output,
    exitstatus). If 'withexitstatus' is false then this returns just
    command_output.

    The run() function can often be used instead of creating a spawn instance.
    For example, the following code uses spawn::

        from pexpect import *
        child = spawn('scp foo user@example.com:.')
        child.expect('(?i)password')
        child.sendline(mypassword)

    The previous code can be replace with the following::

        from pexpect import *
        run('scp foo user@example.com:.', events={'(?i)password': mypassword})

    **Examples**

    Start the apache daemon on the local machine::

        from pexpect import *
        run("/usr/local/apache/bin/apachectl start")

    Check in a file using SVN::

        from pexpect import *
        run("svn ci -m 'automatic commit' my_file.py")

    Run a command and capture exit status::

        from pexpect import *
        (command_output, exitstatus) = run('ls -l /bin', withexitstatus=1)

    The following will run SSH and execute 'ls -l' on the remote machine. The
    password 'secret' will be sent if the '(?i)password' pattern is ever seen::

        run("ssh username@machine.example.com 'ls -l'",
            events={'(?i)password':'secret\\n'})

    This will start mencoder to rip a video from DVD. This will also display
    progress ticks every 5 seconds as it runs. For example::

        from pexpect import *
        def print_ticks(d):
            print d['event_count'],
        run("mencoder dvd://1 -o video.avi -oac copy -ovc copy",
            events={TIMEOUT:print_ticks}, timeout=5)

    The 'events' argument should be a dictionary of patterns and responses.
    Whenever one of the patterns is seen in the command out run() will send the
    associated response string. Note that you should put newlines in your
    string if Enter is necessary. The responses may also contain callback
    functions. Any callback is function that takes a dictionary as an argument.
    The dictionary contains all the locals from the run() function, so you can
    access the child spawn object or any other variable defined in run()
    (event_count, child, and extra_args are the most useful). A callback may
    return True to stop the current run process otherwise run() continues until
    the next event. A callback may also return a string which will be sent to
    the child. 'extra_args' is not used by directly run(). It provides a way to
    pass data to a callback function through run() through the locals
    dictionary passed to a callback.
    '''
    return _run(command, timeout=timeout, withexitstatus=withexitstatus,
                events=events, extra_args=extra_args, logfile=logfile, cwd=cwd,
                env=env, _spawn=spawn)

def runu(command, timeout=-1, withexitstatus=False, events=None,
        extra_args=None, logfile=None, cwd=None, env=None, **kwargs):
    """This offers the same interface as :func:`run`, but using unicode.

    Like :class:`spawnu`, you can pass ``encoding`` and ``errors`` parameters,
    which will be used for both input and output.
    """
    return _run(command, timeout=timeout, withexitstatus=withexitstatus,
                events=events, extra_args=extra_args, logfile=logfile, cwd=cwd,
                env=env, _spawn=spawnu, **kwargs)

def _run(command, timeout, withexitstatus, events, extra_args, logfile, cwd,
         env, _spawn, **kwargs):
    if timeout == -1:
        child = _spawn(command, maxread=2000, logfile=logfile, cwd=cwd, env=env,
                        **kwargs)
    else:
        child = _spawn(command, timeout=timeout, maxread=2000, logfile=logfile,
                cwd=cwd, env=env, **kwargs)
    if events is not None:
        patterns = list(events.keys())
        responses = list(events.values())
    else:
        # This assumes EOF or TIMEOUT will eventually cause run to terminate.
        patterns = None
        responses = None
    child_result_list = []
    event_count = 0
    while True:
        try:
            index = child.expect(patterns)
            if isinstance(child.after, child.allowed_string_types):
                child_result_list.append(child.before + child.after)
            else:
                # child.after may have been a TIMEOUT or EOF,
                # which we don't want appended to the list.
                child_result_list.append(child.before)
            if isinstance(responses[index], child.allowed_string_types):
                child.send(responses[index])
            elif isinstance(responses[index], types.FunctionType):
                callback_result = responses[index](locals())
                sys.stdout.flush()
                if isinstance(callback_result, child.allowed_string_types):
                    child.send(callback_result)
                elif callback_result:
                    break
            else:
                raise TypeError('The callback must be a string or function.')
            event_count = event_count + 1
        except TIMEOUT:
            child_result_list.append(child.before)
            break
        except EOF:
            child_result_list.append(child.before)
            break
    child_result = child.string_type().join(child_result_list)
    if withexitstatus:
        child.close()
        return (child_result, child.exitstatus)
    else:
        return child_result

class spawn(object):
    '''This is the main class interface for Pexpect. Use this class to start
    and control child applications. '''
    string_type = bytes
    if PY3:
        allowed_string_types = (bytes, str)
        @staticmethod
        def _chr(c):
            return bytes([c])
        linesep = os.linesep.encode('ascii')

        @staticmethod
        def write_to_stdout(b):
            try:
                return sys.stdout.buffer.write(b)
            except AttributeError:
                # If stdout has been replaced, it may not have .buffer
                return sys.stdout.write(b.decode('ascii', 'replace'))
    else:
        allowed_string_types = (basestring,)  # analysis:ignore
        _chr = staticmethod(chr)
        linesep = os.linesep
        write_to_stdout = sys.stdout.write

    encoding = None

    def __init__(self, command, args=[], timeout=30, maxread=2000,
        searchwindowsize=None, logfile=None, cwd=None, env=None,
        ignore_sighup=True):

        '''This is the constructor. The command parameter may be a string that
        includes a command and any arguments to the command. For example::

            child = pexpect.spawn('/usr/bin/ftp')
            child = pexpect.spawn('/usr/bin/ssh user@example.com')
            child = pexpect.spawn('ls -latr /tmp')

        You may also construct it with a list of arguments like so::

            child = pexpect.spawn('/usr/bin/ftp', [])
            child = pexpect.spawn('/usr/bin/ssh', ['user@example.com'])
            child = pexpect.spawn('ls', ['-latr', '/tmp'])

        After this the child application will be created and will be ready to
        talk to. For normal use, see expect() and send() and sendline().

        Remember that Pexpect does NOT interpret shell meta characters such as
        redirect, pipe, or wild cards (``>``, ``|``, or ``*``). This is a
        common mistake.  If you want to run a command and pipe it through
        another command then you must also start a shell. For example::

            child = pexpect.spawn('/bin/bash -c "ls -l | grep LOG > logs.txt"')
            child.expect(pexpect.EOF)

        The second form of spawn (where you pass a list of arguments) is useful
        in situations where you wish to spawn a command and pass it its own
        argument list. This can make syntax more clear. For example, the
        following is equivalent to the previous example::

            shell_cmd = 'ls -l | grep LOG > logs.txt'
            child = pexpect.spawn('/bin/bash', ['-c', shell_cmd])
            child.expect(pexpect.EOF)

        The maxread attribute sets the read buffer size. This is maximum number
        of bytes that Pexpect will try to read from a TTY at one time. Setting
        the maxread size to 1 will turn off buffering. Setting the maxread
        value higher may help performance in cases where large amounts of
        output are read back from the child. This feature is useful in
        conjunction with searchwindowsize.

        The searchwindowsize attribute sets the how far back in the incoming
        seach buffer Pexpect will search for pattern matches. Every time
        Pexpect reads some data from the child it will append the data to the
        incoming buffer. The default is to search from the beginning of the
        incoming buffer each time new data is read from the child. But this is
        very inefficient if you are running a command that generates a large
        amount of data where you want to match. The searchwindowsize does not
        affect the size of the incoming data buffer. You will still have
        access to the full buffer after expect() returns.

        The logfile member turns on or off logging. All input and output will
        be copied to the given file object. Set logfile to None to stop
        logging. This is the default. Set logfile to sys.stdout to echo
        everything to standard output. The logfile is flushed after each write.

        Example log input and output to a file::

            child = pexpect.spawn('some_command')
            fout = file('mylog.txt','w')
            child.logfile = fout

        Example log to stdout::

            child = pexpect.spawn('some_command')
            child.logfile = sys.stdout

        The logfile_read and logfile_send members can be used to separately log
        the input from the child and output sent to the child. Sometimes you
        don't want to see everything you write to the child. You only want to
        log what the child sends back. For example::

            child = pexpect.spawn('some_command')
            child.logfile_read = sys.stdout

        To separately log output sent to the child use logfile_send::

            self.logfile_send = fout

        If ``ignore_sighup`` is True, the child process will ignore SIGHUP
        signals. For now, the default is True, to preserve the behaviour of
        earlier versions of Pexpect, but you should pass this explicitly if you
        want to rely on it.

        The delaybeforesend helps overcome a weird behavior that many users
        were experiencing. The typical problem was that a user would expect() a
        "Password:" prompt and then immediately call sendline() to send the
        password. The user would then see that their password was echoed back
        to them. Passwords don't normally echo. The problem is caused by the
        fact that most applications print out the "Password" prompt and then
        turn off stdin echo, but if you send your password before the
        application turned off echo, then you get your password echoed.
        Normally this wouldn't be a problem when interacting with a human at a
        real keyboard. If you introduce a slight delay just before writing then
        this seems to clear up the problem. This was such a common problem for
        many users that I decided that the default pexpect behavior should be
        to sleep just before writing to the child application. 1/20th of a
        second (50 ms) seems to be enough to clear up the problem. You can set
        delaybeforesend to 0 to return to the old behavior. Most Linux machines
        don't like this to be below 0.03. I don't know why.

        Note that spawn is clever about finding commands on your path.
        It uses the same logic that "which" uses to find executables.

        If you wish to get the exit status of the child you must call the
        close() method. The exit or signal status of the child will be stored
        in self.exitstatus or self.signalstatus. If the child exited normally
        then exitstatus will store the exit return code and signalstatus will
        be None. If the child was terminated abnormally with a signal then
        signalstatus will store the signal value and exitstatus will be None.
        If you need more detail you can also read the self.status member which
        stores the status returned by os.waitpid. You can interpret this using
        os.WIFEXITED/os.WEXITSTATUS or os.WIFSIGNALED/os.TERMSIG. '''

        self.STDIN_FILENO = pty.STDIN_FILENO
        self.STDOUT_FILENO = pty.STDOUT_FILENO
        self.STDERR_FILENO = pty.STDERR_FILENO
        self.stdin = sys.stdin
        self.stdout = sys.stdout
        self.stderr = sys.stderr

        self.searcher = None
        self.ignorecase = False
        self.before = None
        self.after = None
        self.match = None
        self.match_index = None
        self.terminated = True
        self.exitstatus = None
        self.signalstatus = None
        # status returned by os.waitpid
        self.status = None
        self.flag_eof = False
        self.pid = None
        # the chile filedescriptor is initially closed
        self.child_fd = -1
        self.timeout = timeout
        self.delimiter = EOF
        self.logfile = logfile
        # input from child (read_nonblocking)
        self.logfile_read = None
        # output to send (send, sendline)
        self.logfile_send = None
        # max bytes to read at one time into buffer
        self.maxread = maxread
        # This is the read buffer. See maxread.
        self.buffer = self.string_type()
        # Data before searchwindowsize point is preserved, but not searched.
        self.searchwindowsize = searchwindowsize
        # Delay used before sending data to child. Time in seconds.
        # Most Linux machines don't like this to be below 0.03 (30 ms).
        self.delaybeforesend = 0.05
        # Used by close() to give kernel time to update process status.
        # Time in seconds.
        self.delayafterclose = 0.1
        # Used by terminate() to give kernel time to update process status.
        # Time in seconds.
        self.delayafterterminate = 0.1
        self.softspace = False
        self.name = '<' + repr(self) + '>'
        self.closed = True
        self.cwd = cwd
        self.env = env
        self.ignore_sighup = ignore_sighup
        # This flags if we are running on irix
        self.__irix_hack = (sys.platform.lower().find('irix') >= 0)
        # Solaris uses internal __fork_pty(). All others use pty.fork().
        if ((sys.platform.lower().find('solaris') >= 0)
            or (sys.platform.lower().find('sunos5') >= 0)):
            self.use_native_pty_fork = False
        else:
            self.use_native_pty_fork = True

        # Support subclasses that do not use command or args.
        if command is None:
            self.command = None
            self.args = None
            self.name = '<pexpect factory incomplete>'
        else:
            self._spawn(command, args)

    @staticmethod
    def _coerce_expect_string(s):
        if not isinstance(s, bytes):
            return s.encode('ascii')
        return s

    @staticmethod
    def _coerce_send_string(s):
        if not isinstance(s, bytes):
            return s.encode('utf-8')
        return s

    @staticmethod
    def _coerce_read_string(s):
        return s

    def __del__(self):
        '''This makes sure that no system resources are left open. Python only
        garbage collects Python objects. OS file descriptors are not Python
        objects, so they must be handled explicitly. If the child file
        descriptor was opened outside of this class (passed to the constructor)
        then this does not close it. '''

        if not self.closed:
            # It is possible for __del__ methods to execute during the
            # teardown of the Python VM itself. Thus self.close() may
            # trigger an exception because os.close may be None.
            try:
                self.close()
            # which exception, shouldnt' we catch explicitly .. ?
            except:
                pass

    def __str__(self):
        '''This returns a human-readable string that represents the state of
        the object. '''

        s = []
        s.append(repr(self))
        s.append('version: ' + __version__)
        s.append('command: ' + str(self.command))
        s.append('args: %r' % (self.args,))
        s.append('searcher: %r' % (self.searcher,))
        s.append('buffer (last 100 chars): %r' % (self.buffer)[-100:],)
        s.append('before (last 100 chars): %r' % (self.before)[-100:],)
        s.append('after: %r' % (self.after,))
        s.append('match: %r' % (self.match,))
        s.append('match_index: ' + str(self.match_index))
        s.append('exitstatus: ' + str(self.exitstatus))
        s.append('flag_eof: ' + str(self.flag_eof))
        s.append('pid: ' + str(self.pid))
        s.append('child_fd: ' + str(self.child_fd))
        s.append('closed: ' + str(self.closed))
        s.append('timeout: ' + str(self.timeout))
        s.append('delimiter: ' + str(self.delimiter))
        s.append('logfile: ' + str(self.logfile))
        s.append('logfile_read: ' + str(self.logfile_read))
        s.append('logfile_send: ' + str(self.logfile_send))
        s.append('maxread: ' + str(self.maxread))
        s.append('ignorecase: ' + str(self.ignorecase))
        s.append('searchwindowsize: ' + str(self.searchwindowsize))
        s.append('delaybeforesend: ' + str(self.delaybeforesend))
        s.append('delayafterclose: ' + str(self.delayafterclose))
        s.append('delayafterterminate: ' + str(self.delayafterterminate))
        return '\n'.join(s)

    def _spawn(self, command, args=[]):
        '''This starts the given command in a child process. This does all the
        fork/exec type of stuff for a pty. This is called by __init__. If args
        is empty then command will be parsed (split on spaces) and args will be
        set to parsed arguments. '''

        # The pid and child_fd of this object get set by this method.
        # Note that it is difficult for this method to fail.
        # You cannot detect if the child process cannot start.
        # So the only way you can tell if the child process started
        # or not is to try to read from the file descriptor. If you get
        # EOF immediately then it means that the child is already dead.
        # That may not necessarily be bad because you may have spawned a child
        # that performs some task; creates no stdout output; and then dies.

        # If command is an int type then it may represent a file descriptor.
        if isinstance(command, type(0)):
            raise ExceptionPexpect('Command is an int type. ' +
                    'If this is a file descriptor then maybe you want to ' +
                    'use fdpexpect.fdspawn which takes an existing ' +
                    'file descriptor instead of a command string.')

        if not isinstance(args, type([])):
            raise TypeError('The argument, args, must be a list.')

        if args == []:
            self.args = split_command_line(command)
            self.command = self.args[0]
        else:
            # Make a shallow copy of the args list.
            self.args = args[:]
            self.args.insert(0, command)
            self.command = command

        command_with_path = which(self.command)
        if command_with_path is None:
            raise ExceptionPexpect('The command was not found or was not ' +
                    'executable: %s.' % self.command)
        self.command = command_with_path
        self.args[0] = self.command

        self.name = '<' + ' '.join(self.args) + '>'

        assert self.pid is None, 'The pid member must be None.'
        assert self.command is not None, 'The command member must not be None.'

        if self.use_native_pty_fork:
            try:
                self.pid, self.child_fd = pty.fork()
            except OSError:
                err = sys.exc_info()[1]
                raise ExceptionPexpect('pty.fork() failed: ' + str(err))
        else:
            # Use internal __fork_pty
            self.pid, self.child_fd = self.__fork_pty()

        if self.pid == 0:
            # Child
            try:
                # used by setwinsize()
                self.child_fd = sys.stdout.fileno()
                self.setwinsize(24, 80)
            # which exception, shouldnt' we catch explicitly .. ?
            except:
                # Some platforms do not like setwinsize (Cygwin).
                # This will cause problem when running applications that
                # are very picky about window size.
                # This is a serious limitation, but not a show stopper.
                pass
            # Do not allow child to inherit open file descriptors from parent.
            max_fd = resource.getrlimit(resource.RLIMIT_NOFILE)[0]
            for i in range(3, max_fd):
                try:
                    os.close(i)
                except OSError:
                    pass

            if self.ignore_sighup:
                signal.signal(signal.SIGHUP, signal.SIG_IGN)

            if self.cwd is not None:
                os.chdir(self.cwd)
            if self.env is None:
                os.execv(self.command, self.args)
            else:
                os.execvpe(self.command, self.args, self.env)

        # Parent
        self.terminated = False
        self.closed = False

    def __fork_pty(self):
        '''This implements a substitute for the forkpty system call. This
        should be more portable than the pty.fork() function. Specifically,
        this should work on Solaris.

        Modified 10.06.05 by Geoff Marshall: Implemented __fork_pty() method to
        resolve the issue with Python's pty.fork() not supporting Solaris,
        particularly ssh. Based on patch to posixmodule.c authored by Noah
        Spurrier::

            http://mail.python.org/pipermail/python-dev/2003-May/035281.html

        '''

        parent_fd, child_fd = os.openpty()
        if parent_fd < 0 or child_fd < 0:
            raise ExceptionPexpect("Could not open with os.openpty().")

        pid = os.fork()
        if pid < 0:
            raise ExceptionPexpect("Failed os.fork().")
        elif pid == 0:
            # Child.
            os.close(parent_fd)
            self.__pty_make_controlling_tty(child_fd)

            os.dup2(child_fd, 0)
            os.dup2(child_fd, 1)
            os.dup2(child_fd, 2)

            if child_fd > 2:
                os.close(child_fd)
        else:
            # Parent.
            os.close(child_fd)

        return pid, parent_fd

    def __pty_make_controlling_tty(self, tty_fd):
        '''This makes the pseudo-terminal the controlling tty. This should be
        more portable than the pty.fork() function. Specifically, this should
        work on Solaris. '''

        child_name = os.ttyname(tty_fd)

        # Disconnect from controlling tty. Harmless if not already connected.
        try:
            fd = os.open("/dev/tty", os.O_RDWR | os.O_NOCTTY)
            if fd >= 0:
                os.close(fd)
        # which exception, shouldnt' we catch explicitly .. ?
        except:
            # Already disconnected. This happens if running inside cron.
            pass

        os.setsid()

        # Verify we are disconnected from controlling tty
        # by attempting to open it again.
        try:
            fd = os.open("/dev/tty", os.O_RDWR | os.O_NOCTTY)
            if fd >= 0:
                os.close(fd)
                raise ExceptionPexpect('Failed to disconnect from ' +
                    'controlling tty. It is still possible to open /dev/tty.')
        # which exception, shouldnt' we catch explicitly .. ?
        except:
            # Good! We are disconnected from a controlling tty.
            pass

        # Verify we can open child pty.
        fd = os.open(child_name, os.O_RDWR)
        if fd < 0:
            raise ExceptionPexpect("Could not open child pty, " + child_name)
        else:
            os.close(fd)

        # Verify we now have a controlling tty.
        fd = os.open("/dev/tty", os.O_WRONLY)
        if fd < 0:
            raise ExceptionPexpect("Could not open controlling tty, /dev/tty")
        else:
            os.close(fd)

    def fileno(self):
        '''This returns the file descriptor of the pty for the child.
        '''
        return self.child_fd

    def close(self, force=True):
        '''This closes the connection with the child application. Note that
        calling close() more than once is valid. This emulates standard Python
        behavior with files. Set force to True if you want to make sure that
        the child is terminated (SIGKILL is sent if the child ignores SIGHUP
        and SIGINT). '''

        if not self.closed:
            self.flush()
            os.close(self.child_fd)
            # Give kernel time to update process status.
            time.sleep(self.delayafterclose)
            if self.isalive():
                if not self.terminate(force):
                    raise ExceptionPexpect('Could not terminate the child.')
            self.child_fd = -1
            self.closed = True
            #self.pid = None

    def flush(self):
        '''This does nothing. It is here to support the interface for a
        File-like object. '''

        pass

    def isatty(self):
        '''This returns True if the file descriptor is open and connected to a
        tty(-like) device, else False. '''

        return os.isatty(self.child_fd)

    def waitnoecho(self, timeout=-1):
        '''This waits until the terminal ECHO flag is set False. This returns
        True if the echo mode is off. This returns False if the ECHO flag was
        not set False before the timeout. This can be used to detect when the
        child is waiting for a password. Usually a child application will turn
        off echo mode when it is waiting for the user to enter a password. For
        example, instead of expecting the "password:" prompt you can wait for
        the child to set ECHO off::

            p = pexpect.spawn('ssh user@example.com')
            p.waitnoecho()
            p.sendline(mypassword)

        If timeout==-1 then this method will use the value in self.timeout.
        If timeout==None then this method to block until ECHO flag is False.
        '''

        if timeout == -1:
            timeout = self.timeout
        if timeout is not None:
            end_time = time.time() + timeout
        while True:
            if not self.getecho():
                return True
            if timeout < 0 and timeout is not None:
                return False
            if timeout is not None:
                timeout = end_time - time.time()
            time.sleep(0.1)

    def getecho(self):
        '''This returns the terminal echo mode. This returns True if echo is
        on or False if echo is off. Child applications that are expecting you
        to enter a password often set ECHO False. See waitnoecho(). '''

        attr = termios.tcgetattr(self.child_fd)
        if attr[3] & termios.ECHO:
            return True
        return False

    def setecho(self, state):
        '''This sets the terminal echo mode on or off. Note that anything the
        child sent before the echo will be lost, so you should be sure that
        your input buffer is empty before you call setecho(). For example, the
        following will work as expected::

            p = pexpect.spawn('cat') # Echo is on by default.
            p.sendline('1234') # We expect see this twice from the child...
            p.expect(['1234']) # ... once from the tty echo...
            p.expect(['1234']) # ... and again from cat itself.
            p.setecho(False) # Turn off tty echo
            p.sendline('abcd') # We will set this only once (echoed by cat).
            p.sendline('wxyz') # We will set this only once (echoed by cat)
            p.expect(['abcd'])
            p.expect(['wxyz'])

        The following WILL NOT WORK because the lines sent before the setecho
        will be lost::

            p = pexpect.spawn('cat')
            p.sendline('1234')
            p.setecho(False) # Turn off tty echo
            p.sendline('abcd') # We will set this only once (echoed by cat).
            p.sendline('wxyz') # We will set this only once (echoed by cat)
            p.expect(['1234'])
            p.expect(['1234'])
            p.expect(['abcd'])
            p.expect(['wxyz'])
        '''

        self.child_fd
        attr = termios.tcgetattr(self.child_fd)
        if state:
            attr[3] = attr[3] | termios.ECHO
        else:
            attr[3] = attr[3] & ~termios.ECHO
        # I tried TCSADRAIN and TCSAFLUSH, but
        # these were inconsistent and blocked on some platforms.
        # TCSADRAIN would probably be ideal if it worked.
        termios.tcsetattr(self.child_fd, termios.TCSANOW, attr)

    def _log(self, s, direction):
        if self.logfile is not None:
            self.logfile.write(s)
            self.logfile.flush()
        second_log = self.logfile_send if (direction=='send') else self.logfile_read
        if second_log is not None:
            second_log.write(s)
            second_log.flush()

    def read_nonblocking(self, size=1, timeout=-1):
        '''This reads at most size characters from the child application. It
        includes a timeout. If the read does not complete within the timeout
        period then a TIMEOUT exception is raised. If the end of file is read
        then an EOF exception will be raised. If a log file was set using
        setlog() then all data will also be written to the log file.

        If timeout is None then the read may block indefinitely.
        If timeout is -1 then the self.timeout value is used. If timeout is 0
        then the child is polled and if there is no data immediately ready
        then this will raise a TIMEOUT exception.

        The timeout refers only to the amount of time to read at least one
        character. This is not effected by the 'size' parameter, so if you call
        read_nonblocking(size=100, timeout=30) and only one character is
        available right away then one character will be returned immediately.
        It will not wait for 30 seconds for another 99 characters to come in.

        This is a wrapper around os.read(). It uses select.select() to
        implement the timeout. '''

        if self.closed:
            raise ValueError('I/O operation on closed file.')

        if timeout == -1:
            timeout = self.timeout

        # Note that some systems such as Solaris do not give an EOF when
        # the child dies. In fact, you can still try to read
        # from the child_fd -- it will block forever or until TIMEOUT.
        # For this case, I test isalive() before doing any reading.
        # If isalive() is false, then I pretend that this is the same as EOF.
        if not self.isalive():
            # timeout of 0 means "poll"
            r, w, e = self.__select([self.child_fd], [], [], 0)
            if not r:
                self.flag_eof = True
                raise EOF('End Of File (EOF). Braindead platform.')
        elif self.__irix_hack:
            # Irix takes a long time before it realizes a child was terminated.
            # FIXME So does this mean Irix systems are forced to always have
            # FIXME a 2 second delay when calling read_nonblocking? That sucks.
            r, w, e = self.__select([self.child_fd], [], [], 2)
            if not r and not self.isalive():
                self.flag_eof = True
                raise EOF('End Of File (EOF). Slow platform.')

        r, w, e = self.__select([self.child_fd], [], [], timeout)

        if not r:
            if not self.isalive():
                # Some platforms, such as Irix, will claim that their
                # processes are alive; timeout on the select; and
                # then finally admit that they are not alive.
                self.flag_eof = True
                raise EOF('End of File (EOF). Very slow platform.')
            else:
                raise TIMEOUT('Timeout exceeded.')

        if self.child_fd in r:
            try:
                s = os.read(self.child_fd, size)
            except OSError:
                # Linux does this
                self.flag_eof = True
                raise EOF('End Of File (EOF). Exception style platform.')
            if s == b'':
                # BSD style
                self.flag_eof = True
                raise EOF('End Of File (EOF). Empty string style platform.')

            s = self._coerce_read_string(s)
            self._log(s, 'read')
            return s

        raise ExceptionPexpect('Reached an unexpected state.')

    def read(self, size=-1):
        '''This reads at most "size" bytes from the file (less if the read hits
        EOF before obtaining size bytes). If the size argument is negative or
        omitted, read all data until EOF is reached. The bytes are returned as
        a string object. An empty string is returned when EOF is encountered
        immediately. '''

        if size == 0:
            return self.string_type()
        if size < 0:
            # delimiter default is EOF
            self.expect(self.delimiter)
            return self.before

        # I could have done this more directly by not using expect(), but
        # I deliberately decided to couple read() to expect() so that
        # I would catch any bugs early and ensure consistant behavior.
        # It's a little less efficient, but there is less for me to
        # worry about if I have to later modify read() or expect().
        # Note, it's OK if size==-1 in the regex. That just means it
        # will never match anything in which case we stop only on EOF.
        cre = re.compile(self._coerce_expect_string('.{%d}' % size), re.DOTALL)
        # delimiter default is EOF
        index = self.expect([cre, self.delimiter])
        if index == 0:
            ### FIXME self.before should be ''. Should I assert this?
            return self.after
        return self.before

    def readline(self, size=-1):
        '''This reads and returns one entire line. The newline at the end of
        line is returned as part of the string, unless the file ends without a
        newline. An empty string is returned if EOF is encountered immediately.
        This looks for a newline as a CR/LF pair (\\r\\n) even on UNIX because
        this is what the pseudotty device returns. So contrary to what you may
        expect you will receive newlines as \\r\\n.

        If the size argument is 0 then an empty string is returned. In all
        other cases the size argument is ignored, which is not standard
        behavior for a file-like object. '''

        if size == 0:
            return self.string_type()
        # delimiter default is EOF
        index = self.expect([b'\r\n', self.delimiter])
        if index == 0:
            return self.before + b'\r\n'
        else:
            return self.before

    def __iter__(self):
        '''This is to support iterators over a file-like object.
        '''
        return iter(self.readline, self.string_type())

    def readlines(self, sizehint=-1):
        '''This reads until EOF using readline() and returns a list containing
        the lines thus read. The optional 'sizehint' argument is ignored.
        Remember, because this reads until EOF that means the child
        process should have closed its stdout. If you run this method on
        a child that is still running with its stdout open then this
        method will block until it timesout.'''

        lines = []
        while True:
            line = self.readline()
            if not line:
                break
            lines.append(line)
        return lines

    def write(self, s):
        '''This is similar to send() except that there is no return value.
        '''

        self.send(s)

    def writelines(self, sequence):
        '''This calls write() for each element in the sequence. The sequence
        can be any iterable object producing strings, typically a list of
        strings. This does not add line separators. There is no return value.
        '''

        for s in sequence:
            self.write(s)

    def send(self, s):
        '''Sends string ``s`` to the child process, returning the number of
        bytes written. If a logfile is specified, a copy is written to that
        log. '''

        time.sleep(self.delaybeforesend)

        s = self._coerce_send_string(s)
        self._log(s, 'send')

        return self._send(s)

    def _send(self, s):
        return os.write(self.child_fd, s)

    def sendline(self, s=''):
        '''Wraps send(), sending string ``s`` to child process, with os.linesep
        automatically appended. Returns number of bytes written. '''

        n = self.send(s)
        n = n + self.send(self.linesep)
        return n

    def sendcontrol(self, char):

        '''Helper method that wraps send() with mnemonic access for sending control
        character to the child (such as Ctrl-C or Ctrl-D).  For example, to send
        Ctrl-G (ASCII 7, bell, '\a')::

            child.sendcontrol('g')

        See also, sendintr() and sendeof().
        '''

        char = char.lower()
        a = ord(char)
        if a >= 97 and a <= 122:
            a = a - ord('a') + 1
            return self.send(self._chr(a))
        d = {'@': 0, '`': 0,
            '[': 27, '{': 27,
            '\\': 28, '|': 28,
            ']': 29, '}': 29,
            '^': 30, '~': 30,
            '_': 31,
            '?': 127}
        if char not in d:
            return 0
        return self.send(self._chr(d[char]))

    def sendeof(self):

        '''This sends an EOF to the child. This sends a character which causes
        the pending parent output buffer to be sent to the waiting child
        program without waiting for end-of-line. If it is the first character
        of the line, the read() in the user program returns 0, which signifies
        end-of-file. This means to work as expected a sendeof() has to be
        called at the beginning of a line. This method does not send a newline.
        It is the responsibility of the caller to ensure the eof is sent at the
        beginning of a line. '''

        ### Hmmm... how do I send an EOF?
        ###C  if ((m = write(pty, *buf, p - *buf)) < 0)
        ###C      return (errno == EWOULDBLOCK) ? n : -1;
        #fd = sys.stdin.fileno()
        #old = termios.tcgetattr(fd) # remember current state
        #attr = termios.tcgetattr(fd)
        #attr[3] = attr[3] | termios.ICANON # ICANON must be set to see EOF
        #try: # use try/finally to ensure state gets restored
        #    termios.tcsetattr(fd, termios.TCSADRAIN, attr)
        #    if hasattr(termios, 'CEOF'):
        #        os.write(self.child_fd, '%c' % termios.CEOF)
        #    else:
        #        # Silly platform does not define CEOF so assume CTRL-D
        #        os.write(self.child_fd, '%c' % 4)
        #finally: # restore state
        #    termios.tcsetattr(fd, termios.TCSADRAIN, old)
        if hasattr(termios, 'VEOF'):
            char = ord(termios.tcgetattr(self.child_fd)[6][termios.VEOF])
        else:
            # platform does not define VEOF so assume CTRL-D
            char = 4
        self.send(self._chr(char))

    def sendintr(self):

        '''This sends a SIGINT to the child. It does not require
        the SIGINT to be the first character on a line. '''

        if hasattr(termios, 'VINTR'):
            char = ord(termios.tcgetattr(self.child_fd)[6][termios.VINTR])
        else:
            # platform does not define VINTR so assume CTRL-C
            char = 3
        self.send(self._chr(char))

    def eof(self):

        '''This returns True if the EOF exception was ever raised.
        '''

        return self.flag_eof

    def terminate(self, force=False):

        '''This forces a child process to terminate. It starts nicely with
        SIGHUP and SIGINT. If "force" is True then moves onto SIGKILL. This
        returns True if the child was terminated. This returns False if the
        child could not be terminated. '''

        if not self.isalive():
            return True
        try:
            self.kill(signal.SIGHUP)
            time.sleep(self.delayafterterminate)
            if not self.isalive():
                return True
            self.kill(signal.SIGCONT)
            time.sleep(self.delayafterterminate)
            if not self.isalive():
                return True
            self.kill(signal.SIGINT)
            time.sleep(self.delayafterterminate)
            if not self.isalive():
                return True
            if force:
                self.kill(signal.SIGKILL)
                time.sleep(self.delayafterterminate)
                if not self.isalive():
                    return True
                else:
                    return False
            return False
        except OSError:
            # I think there are kernel timing issues that sometimes cause
            # this to happen. I think isalive() reports True, but the
            # process is dead to the kernel.
            # Make one last attempt to see if the kernel is up to date.
            time.sleep(self.delayafterterminate)
            if not self.isalive():
                return True
            else:
                return False

    def wait(self):

        '''This waits until the child exits. This is a blocking call. This will
        not read any data from the child, so this will block forever if the
        child has unread output and has terminated. In other words, the child
        may have printed output then called exit(), but, the child is
        technically still alive until its output is read by the parent. '''

        if self.isalive():
            pid, status = os.waitpid(self.pid, 0)
        else:
            raise ExceptionPexpect('Cannot wait for dead child process.')
        self.exitstatus = os.WEXITSTATUS(status)
        if os.WIFEXITED(status):
            self.status = status
            self.exitstatus = os.WEXITSTATUS(status)
            self.signalstatus = None
            self.terminated = True
        elif os.WIFSIGNALED(status):
            self.status = status
            self.exitstatus = None
            self.signalstatus = os.WTERMSIG(status)
            self.terminated = True
        elif os.WIFSTOPPED(status):
            # You can't call wait() on a child process in the stopped state.
            raise ExceptionPexpect('Called wait() on a stopped child ' +
                    'process. This is not supported. Is some other ' +
                    'process attempting job control with our child pid?')
        return self.exitstatus

    def isalive(self):

        '''This tests if the child process is running or not. This is
        non-blocking. If the child was terminated then this will read the
        exitstatus or signalstatus of the child. This returns True if the child
        process appears to be running or False if not. It can take literally
        SECONDS for Solaris to return the right status. '''

        if self.terminated:
            return False

        if self.flag_eof:
            # This is for Linux, which requires the blocking form
            # of waitpid to # get status of a defunct process.
            # This is super-lame. The flag_eof would have been set
            # in read_nonblocking(), so this should be safe.
            waitpid_options = 0
        else:
            waitpid_options = os.WNOHANG

        try:
            pid, status = os.waitpid(self.pid, waitpid_options)
        except OSError:
            err = sys.exc_info()[1]
            # No child processes
            if err.errno == errno.ECHILD:
                raise ExceptionPexpect('isalive() encountered condition ' +
                        'where "terminated" is 0, but there was no child ' +
                        'process. Did someone else call waitpid() ' +
                        'on our process?')
            else:
                raise err

        # I have to do this twice for Solaris.
        # I can't even believe that I figured this out...
        # If waitpid() returns 0 it means that no child process
        # wishes to report, and the value of status is undefined.
        if pid == 0:
            try:
                ### os.WNOHANG) # Solaris!
                pid, status = os.waitpid(self.pid, waitpid_options)
            except OSError as e:
                # This should never happen...
                if e.errno == errno.ECHILD:
                    raise ExceptionPexpect('isalive() encountered condition ' +
                            'that should never happen. There was no child ' +
                            'process. Did someone else call waitpid() ' +
                            'on our process?')
                else:
                    raise

            # If pid is still 0 after two calls to waitpid() then the process
            # really is alive. This seems to work on all platforms, except for
            # Irix which seems to require a blocking call on waitpid or select,
            # so I let read_nonblocking take care of this situation
            # (unfortunately, this requires waiting through the timeout).
            if pid == 0:
                return True

        if pid == 0:
            return True

        if os.WIFEXITED(status):
            self.status = status
            self.exitstatus = os.WEXITSTATUS(status)
            self.signalstatus = None
            self.terminated = True
        elif os.WIFSIGNALED(status):
            self.status = status
            self.exitstatus = None
            self.signalstatus = os.WTERMSIG(status)
            self.terminated = True
        elif os.WIFSTOPPED(status):
            raise ExceptionPexpect('isalive() encountered condition ' +
                    'where child process is stopped. This is not ' +
                    'supported. Is some other process attempting ' +
                    'job control with our child pid?')
        return False

    def kill(self, sig):

        '''This sends the given signal to the child application. In keeping
        with UNIX tradition it has a misleading name. It does not necessarily
        kill the child unless you send the right signal. '''

        # Same as os.kill, but the pid is given for you.
        if self.isalive():
            os.kill(self.pid, sig)

    def _pattern_type_err(self, pattern):
        raise TypeError('got {badtype} ({badobj!r}) as pattern, must be one'
                        ' of: {goodtypes}, pexpect.EOF, pexpect.TIMEOUT'\
                        .format(badtype=type(pattern),
                                badobj=pattern,
                                goodtypes=', '.join([str(ast)\
                                    for ast in self.allowed_string_types])
                                )
                        )

    def compile_pattern_list(self, patterns):

        '''This compiles a pattern-string or a list of pattern-strings.
        Patterns must be a StringType, EOF, TIMEOUT, SRE_Pattern, or a list of
        those. Patterns may also be None which results in an empty list (you
        might do this if waiting for an EOF or TIMEOUT condition without
        expecting any pattern).

        This is used by expect() when calling expect_list(). Thus expect() is
        nothing more than::

             cpl = self.compile_pattern_list(pl)
             return self.expect_list(cpl, timeout)

        If you are using expect() within a loop it may be more
        efficient to compile the patterns first and then call expect_list().
        This avoid calls in a loop to compile_pattern_list()::

             cpl = self.compile_pattern_list(my_pattern)
             while some_condition:
                ...
                i = self.expect_list(clp, timeout)
                ...
        '''

        if patterns is None:
            return []
        if not isinstance(patterns, list):
            patterns = [patterns]

        # Allow dot to match \n
        compile_flags = re.DOTALL
        if self.ignorecase:
            compile_flags = compile_flags | re.IGNORECASE
        compiled_pattern_list = []
        for idx, p in enumerate(patterns):
            if isinstance(p, self.allowed_string_types):
                p = self._coerce_expect_string(p)
                compiled_pattern_list.append(re.compile(p, compile_flags))
            elif p is EOF:
                compiled_pattern_list.append(EOF)
            elif p is TIMEOUT:
                compiled_pattern_list.append(TIMEOUT)
            elif isinstance(p, type(re.compile(''))):
                compiled_pattern_list.append(p)
            else:
                self._pattern_type_err(p)
        return compiled_pattern_list

    def expect(self, pattern, timeout=-1, searchwindowsize=-1):

        '''This seeks through the stream until a pattern is matched. The
        pattern is overloaded and may take several types. The pattern can be a
        StringType, EOF, a compiled re, or a list of any of those types.
        Strings will be compiled to re types. This returns the index into the
        pattern list. If the pattern was not a list this returns index 0 on a
        successful match. This may raise exceptions for EOF or TIMEOUT. To
        avoid the EOF or TIMEOUT exceptions add EOF or TIMEOUT to the pattern
        list. That will cause expect to match an EOF or TIMEOUT condition
        instead of raising an exception.

        If you pass a list of patterns and more than one matches, the first
        match in the stream is chosen. If more than one pattern matches at that
        point, the leftmost in the pattern list is chosen. For example::

            # the input is 'foobar'
            index = p.expect(['bar', 'foo', 'foobar'])
            # returns 1('foo') even though 'foobar' is a "better" match

        Please note, however, that buffering can affect this behavior, since
        input arrives in unpredictable chunks. For example::

            # the input is 'foobar'
            index = p.expect(['foobar', 'foo'])
            # returns 0('foobar') if all input is available at once,
            # but returs 1('foo') if parts of the final 'bar' arrive late

        After a match is found the instance attributes 'before', 'after' and
        'match' will be set. You can see all the data read before the match in
        'before'. You can see the data that was matched in 'after'. The
        re.MatchObject used in the re match will be in 'match'. If an error
        occurred then 'before' will be set to all the data read so far and
        'after' and 'match' will be None.

        If timeout is -1 then timeout will be set to the self.timeout value.

        A list entry may be EOF or TIMEOUT instead of a string. This will
        catch these exceptions and return the index of the list entry instead
        of raising the exception. The attribute 'after' will be set to the
        exception type. The attribute 'match' will be None. This allows you to
        write code like this::

                index = p.expect(['good', 'bad', pexpect.EOF, pexpect.TIMEOUT])
                if index == 0:
                    do_something()
                elif index == 1:
                    do_something_else()
                elif index == 2:
                    do_some_other_thing()
                elif index == 3:
                    do_something_completely_different()

        instead of code like this::

                try:
                    index = p.expect(['good', 'bad'])
                    if index == 0:
                        do_something()
                    elif index == 1:
                        do_something_else()
                except EOF:
                    do_some_other_thing()
                except TIMEOUT:
                    do_something_completely_different()

        These two forms are equivalent. It all depends on what you want. You
        can also just expect the EOF if you are waiting for all output of a
        child to finish. For example::

                p = pexpect.spawn('/bin/ls')
                p.expect(pexpect.EOF)
                print p.before

        If you are trying to optimize for speed then see expect_list().
        '''

        compiled_pattern_list = self.compile_pattern_list(pattern)
        return self.expect_list(compiled_pattern_list,
                timeout, searchwindowsize)

    def expect_list(self, pattern_list, timeout=-1, searchwindowsize=-1):

        '''This takes a list of compiled regular expressions and returns the
        index into the pattern_list that matched the child output. The list may
        also contain EOF or TIMEOUT(which are not compiled regular
        expressions). This method is similar to the expect() method except that
        expect_list() does not recompile the pattern list on every call. This
        may help if you are trying to optimize for speed, otherwise just use
        the expect() method.  This is called by expect(). If timeout==-1 then
        the self.timeout value is used. If searchwindowsize==-1 then the
        self.searchwindowsize value is used. '''

        return self.expect_loop(searcher_re(pattern_list),
                timeout, searchwindowsize)

    def expect_exact(self, pattern_list, timeout=-1, searchwindowsize=-1):

        '''This is similar to expect(), but uses plain string matching instead
        of compiled regular expressions in 'pattern_list'. The 'pattern_list'
        may be a string; a list or other sequence of strings; or TIMEOUT and
        EOF.

        This call might be faster than expect() for two reasons: string
        searching is faster than RE matching and it is possible to limit the
        search to just the end of the input buffer.

        This method is also useful when you don't want to have to worry about
        escaping regular expression characters that you want to match.'''

        if (isinstance(pattern_list, self.allowed_string_types) or
                pattern_list in (TIMEOUT, EOF)):
            pattern_list = [pattern_list]

        def prepare_pattern(pattern):
            if pattern in (TIMEOUT, EOF):
                return pattern
            if isinstance(pattern, self.allowed_string_types):
                return self._coerce_expect_string(pattern)
            self._pattern_type_err(pattern)

        try:
            pattern_list = iter(pattern_list)
        except TypeError:
            self._pattern_type_err(pattern_list)
        pattern_list = [prepare_pattern(p) for p in pattern_list]
        return self.expect_loop(searcher_string(pattern_list),
                timeout, searchwindowsize)

    def expect_loop(self, searcher, timeout=-1, searchwindowsize=-1):

        '''This is the common loop used inside expect. The 'searcher' should be
        an instance of searcher_re or searcher_string, which describes how and
        what to search for in the input.

        See expect() for other arguments, return value and exceptions. '''

        self.searcher = searcher

        if timeout == -1:
            timeout = self.timeout
        if timeout is not None:
            end_time = time.time() + timeout
        if searchwindowsize == -1:
            searchwindowsize = self.searchwindowsize

        try:
            incoming = self.buffer
            freshlen = len(incoming)
            while True:
                # Keep reading until exception or return.
                index = searcher.search(incoming, freshlen, searchwindowsize)
                if index >= 0:
                    self.buffer = incoming[searcher.end:]
                    self.before = incoming[: searcher.start]
                    self.after = incoming[searcher.start: searcher.end]
                    self.match = searcher.match
                    self.match_index = index
                    return self.match_index
                # No match at this point
                if (timeout is not None) and (timeout < 0):
                    raise TIMEOUT('Timeout exceeded in expect_any().')
                # Still have time left, so read more data
                c = self.read_nonblocking(self.maxread, timeout)
                freshlen = len(c)
                time.sleep(0.0001)
                incoming = incoming + c
                if timeout is not None:
                    timeout = end_time - time.time()
        except EOF:
            err = sys.exc_info()[1]
            self.buffer = self.string_type()
            self.before = incoming
            self.after = EOF
            index = searcher.eof_index
            if index >= 0:
                self.match = EOF
                self.match_index = index
                return self.match_index
            else:
                self.match = None
                self.match_index = None
                raise EOF(str(err) + '\n' + str(self))
        except TIMEOUT:
            err = sys.exc_info()[1]
            self.buffer = incoming
            self.before = incoming
            self.after = TIMEOUT
            index = searcher.timeout_index
            if index >= 0:
                self.match = TIMEOUT
                self.match_index = index
                return self.match_index
            else:
                self.match = None
                self.match_index = None
                raise TIMEOUT(str(err) + '\n' + str(self))
        except:
            self.before = incoming
            self.after = None
            self.match = None
            self.match_index = None
            raise

    def getwinsize(self):

        '''This returns the terminal window size of the child tty. The return
        value is a tuple of (rows, cols). '''

        TIOCGWINSZ = getattr(termios, 'TIOCGWINSZ', 1074295912)
        s = struct.pack('HHHH', 0, 0, 0, 0)
        x = fcntl.ioctl(self.child_fd, TIOCGWINSZ, s)
        return struct.unpack('HHHH', x)[0:2]

    def setwinsize(self, rows, cols):

        '''This sets the terminal window size of the child tty. This will cause
        a SIGWINCH signal to be sent to the child. This does not change the
        physical window size. It changes the size reported to TTY-aware
        applications like vi or curses -- applications that respond to the
        SIGWINCH signal. '''

        # Some very old platforms have a bug that causes the value for
        # termios.TIOCSWINSZ to be truncated. There was a hack here to work
        # around this, but it caused problems with newer platforms so has been
        # removed. For details see https://github.com/pexpect/pexpect/issues/39
        TIOCSWINSZ = getattr(termios, 'TIOCSWINSZ', -2146929561)
        # Note, assume ws_xpixel and ws_ypixel are zero.
        s = struct.pack('HHHH', rows, cols, 0, 0)
        fcntl.ioctl(self.fileno(), TIOCSWINSZ, s)

    def interact(self, escape_character=chr(29),
            input_filter=None, output_filter=None):

        '''This gives control of the child process to the interactive user (the
        human at the keyboard). Keystrokes are sent to the child process, and
        the stdout and stderr output of the child process is printed. This
        simply echos the child stdout and child stderr to the real stdout and
        it echos the real stdin to the child stdin. When the user types the
        escape_character this method will stop. The default for
        escape_character is ^]. This should not be confused with ASCII 27 --
        the ESC character. ASCII 29 was chosen for historical merit because
        this is the character used by 'telnet' as the escape character. The
        escape_character will not be sent to the child process.

        You may pass in optional input and output filter functions. These
        functions should take a string and return a string. The output_filter
        will be passed all the output from the child process. The input_filter
        will be passed all the keyboard input from the user. The input_filter
        is run BEFORE the check for the escape_character.

        Note that if you change the window size of the parent the SIGWINCH
        signal will not be passed through to the child. If you want the child
        window size to change when the parent's window size changes then do
        something like the following example::

            import pexpect, struct, fcntl, termios, signal, sys
            def sigwinch_passthrough (sig, data):
                s = struct.pack("HHHH", 0, 0, 0, 0)
                a = struct.unpack('hhhh', fcntl.ioctl(sys.stdout.fileno(),
                    termios.TIOCGWINSZ , s))
                global p
                p.setwinsize(a[0],a[1])
            # Note this 'p' global and used in sigwinch_passthrough.
            p = pexpect.spawn('/bin/bash')
            signal.signal(signal.SIGWINCH, sigwinch_passthrough)
            p.interact()
        '''

        # Flush the buffer.
        self.write_to_stdout(self.buffer)
        self.stdout.flush()
        self.buffer = self.string_type()
        mode = tty.tcgetattr(self.STDIN_FILENO)
        tty.setraw(self.STDIN_FILENO)
        if PY3:
            escape_character = escape_character.encode('latin-1')
        try:
            self.__interact_copy(escape_character, input_filter, output_filter)
        finally:
            tty.tcsetattr(self.STDIN_FILENO, tty.TCSAFLUSH, mode)

    def __interact_writen(self, fd, data):
        '''This is used by the interact() method.
        '''

        while data != b'' and self.isalive():
            n = os.write(fd, data)
            data = data[n:]

    def __interact_read(self, fd):
        '''This is used by the interact() method.
        '''

        return os.read(fd, 1000)

    def __interact_copy(self, escape_character=None,
            input_filter=None, output_filter=None):

        '''This is used by the interact() method.
        '''

        while self.isalive():
            r, w, e = self.__select([self.child_fd, self.STDIN_FILENO], [], [])
            if self.child_fd in r:
                try:
                    data = self.__interact_read(self.child_fd)
                except OSError as e:
                    # The subprocess may have closed before we get to reading it
                    if e.errno != errno.EIO:
                        raise
                if output_filter:
                    data = output_filter(data)
                if self.logfile is not None:
                    self.logfile.write(data)
                    self.logfile.flush()
                os.write(self.STDOUT_FILENO, data)
            if self.STDIN_FILENO in r:
                data = self.__interact_read(self.STDIN_FILENO)
                if input_filter:
                    data = input_filter(data)
                i = data.rfind(escape_character)
                if i != -1:
                    data = data[:i]
                    self.__interact_writen(self.child_fd, data)
                    break
                self.__interact_writen(self.child_fd, data)

    def __select(self, iwtd, owtd, ewtd, timeout=None):

        '''This is a wrapper around select.select() that ignores signals. If
        select.select raises a select.error exception and errno is an EINTR
        error then it is ignored. Mainly this is used to ignore sigwinch
        (terminal resize). '''

        # if select() is interrupted by a signal (errno==EINTR) then
        # we loop back and enter the select() again.
        if timeout is not None:
            end_time = time.time() + timeout
        while True:
            try:
                return select.select(iwtd, owtd, ewtd, timeout)
            except select.error:
                err = sys.exc_info()[1]
                if err.args[0] == errno.EINTR:
                    # if we loop back we have to subtract the
                    # amount of time we already waited.
                    if timeout is not None:
                        timeout = end_time - time.time()
                        if timeout < 0:
                            return([], [], [])
                else:
                    # something else caused the select.error, so
                    # this actually is an exception.
                    raise

##############################################################################
# The following methods are no longer supported or allowed.

    def setmaxread(self, maxread):

        '''This method is no longer supported or allowed. I don't like getters
        and setters without a good reason. '''

        raise ExceptionPexpect('This method is no longer supported ' +
                'or allowed. Just assign a value to the ' +
                'maxread member variable.')

    def setlog(self, fileobject):

        '''This method is no longer supported or allowed.
        '''

        raise ExceptionPexpect('This method is no longer supported ' +
                'or allowed. Just assign a value to the logfile ' +
                'member variable.')

##############################################################################
# End of spawn class
##############################################################################

class spawnu(spawn):
    """Works like spawn, but accepts and returns unicode strings.

    Extra parameters:

    :param encoding: The encoding to use for communications (default: 'utf-8')
    :param errors: How to handle encoding/decoding errors; one of 'strict'
                   (the default), 'ignore', or 'replace', as described
                   for :meth:`~bytes.decode` and :meth:`~str.encode`.
    """
    if PY3:
        string_type = str
        allowed_string_types = (str, )
        _chr = staticmethod(chr)
        linesep = os.linesep
    else:
        string_type = unicode
        allowed_string_types = (unicode, )
        _chr = staticmethod(unichr)
        linesep = os.linesep.decode('ascii')
    # This can handle unicode in both Python 2 and 3
    write_to_stdout = sys.stdout.write

    def __init__(self, *args, **kwargs):
        self.encoding = kwargs.pop('encoding', 'utf-8')
        self.errors = kwargs.pop('errors', 'strict')
        self._decoder = codecs.getincrementaldecoder(self.encoding)(errors=self.errors)
        super(spawnu, self).__init__(*args, **kwargs)

    @staticmethod
    def _coerce_expect_string(s):
        return s

    @staticmethod
    def _coerce_send_string(s):
        return s

    def _coerce_read_string(self, s):
        return self._decoder.decode(s, final=False)

    def _send(self, s):
        return os.write(self.child_fd, s.encode(self.encoding, self.errors))


class searcher_string(object):

    '''This is a plain string search helper for the spawn.expect_any() method.
    This helper class is for speed. For more powerful regex patterns
    see the helper class, searcher_re.

    Attributes:

        eof_index     - index of EOF, or -1
        timeout_index - index of TIMEOUT, or -1

    After a successful match by the search() method the following attributes
    are available:

        start - index into the buffer, first byte of match
        end   - index into the buffer, first byte after match
        match - the matching string itself

    '''

    def __init__(self, strings):

        '''This creates an instance of searcher_string. This argument 'strings'
        may be a list; a sequence of strings; or the EOF or TIMEOUT types. '''

        self.eof_index = -1
        self.timeout_index = -1
        self._strings = []
        for n, s in enumerate(strings):
            if s is EOF:
                self.eof_index = n
                continue
            if s is TIMEOUT:
                self.timeout_index = n
                continue
            self._strings.append((n, s))

    def __str__(self):

        '''This returns a human-readable string that represents the state of
        the object.'''

        ss = [(ns[0], '    %d: "%s"' % ns) for ns in self._strings]
        ss.append((-1, 'searcher_string:'))
        if self.eof_index >= 0:
            ss.append((self.eof_index, '    %d: EOF' % self.eof_index))
        if self.timeout_index >= 0:
            ss.append((self.timeout_index,
                '    %d: TIMEOUT' % self.timeout_index))
        ss.sort()
        ss = list(zip(*ss))[1]
        return '\n'.join(ss)

    def search(self, buffer, freshlen, searchwindowsize=None):

        '''This searches 'buffer' for the first occurence of one of the search
        strings.  'freshlen' must indicate the number of bytes at the end of
        'buffer' which have not been searched before. It helps to avoid
        searching the same, possibly big, buffer over and over again.

        See class spawn for the 'searchwindowsize' argument.

        If there is a match this returns the index of that string, and sets
        'start', 'end' and 'match'. Otherwise, this returns -1. '''

        first_match = None

        # 'freshlen' helps a lot here. Further optimizations could
        # possibly include:
        #
        # using something like the Boyer-Moore Fast String Searching
        # Algorithm; pre-compiling the search through a list of
        # strings into something that can scan the input once to
        # search for all N strings; realize that if we search for
        # ['bar', 'baz'] and the input is '...foo' we need not bother
        # rescanning until we've read three more bytes.
        #
        # Sadly, I don't know enough about this interesting topic. /grahn

        for index, s in self._strings:
            if searchwindowsize is None:
                # the match, if any, can only be in the fresh data,
                # or at the very end of the old data
                offset = -(freshlen + len(s))
            else:
                # better obey searchwindowsize
                offset = -searchwindowsize
            n = buffer.find(s, offset)
            if n >= 0 and (first_match is None or n < first_match):
                first_match = n
                best_index, best_match = index, s
        if first_match is None:
            return -1
        self.match = best_match
        self.start = first_match
        self.end = self.start + len(self.match)
        return best_index


class searcher_re(object):

    '''This is regular expression string search helper for the
    spawn.expect_any() method. This helper class is for powerful
    pattern matching. For speed, see the helper class, searcher_string.

    Attributes:

        eof_index     - index of EOF, or -1
        timeout_index - index of TIMEOUT, or -1

    After a successful match by the search() method the following attributes
    are available:

        start - index into the buffer, first byte of match
        end   - index into the buffer, first byte after match
        match - the re.match object returned by a succesful re.search

    '''

    def __init__(self, patterns):

        '''This creates an instance that searches for 'patterns' Where
        'patterns' may be a list or other sequence of compiled regular
        expressions, or the EOF or TIMEOUT types.'''

        self.eof_index = -1
        self.timeout_index = -1
        self._searches = []
        for n, s in zip(list(range(len(patterns))), patterns):
            if s is EOF:
                self.eof_index = n
                continue
            if s is TIMEOUT:
                self.timeout_index = n
                continue
            self._searches.append((n, s))

    def __str__(self):

        '''This returns a human-readable string that represents the state of
        the object.'''

        #ss = [(n, '    %d: re.compile("%s")' %
        #    (n, repr(s.pattern))) for n, s in self._searches]
        ss = list()
        for n, s in self._searches:
            try:
                ss.append((n, '    %d: re.compile("%s")' % (n, s.pattern)))
            except UnicodeEncodeError:
                # for test cases that display __str__ of searches, dont throw
                # another exception just because stdout is ascii-only, using
                # repr()
                ss.append((n, '    %d: re.compile(%r)' % (n, s.pattern)))
        ss.append((-1, 'searcher_re:'))
        if self.eof_index >= 0:
            ss.append((self.eof_index, '    %d: EOF' % self.eof_index))
        if self.timeout_index >= 0:
            ss.append((self.timeout_index, '    %d: TIMEOUT' %
                self.timeout_index))
        ss.sort()
        ss = list(zip(*ss))[1]
        return '\n'.join(ss)

    def search(self, buffer, freshlen, searchwindowsize=None):

        '''This searches 'buffer' for the first occurence of one of the regular
        expressions. 'freshlen' must indicate the number of bytes at the end of
        'buffer' which have not been searched before.

        See class spawn for the 'searchwindowsize' argument.

        If there is a match this returns the index of that string, and sets
        'start', 'end' and 'match'. Otherwise, returns -1.'''

        first_match = None
        # 'freshlen' doesn't help here -- we cannot predict the
        # length of a match, and the re module provides no help.
        if searchwindowsize is None:
            searchstart = 0
        else:
            searchstart = max(0, len(buffer) - searchwindowsize)
        for index, s in self._searches:
            match = s.search(buffer, searchstart)
            if match is None:
                continue
            n = match.start()
            if first_match is None or n < first_match:
                first_match = n
                the_match = match
                best_index = index
        if first_match is None:
            return -1
        self.start = first_match
        self.match = the_match
        self.end = self.match.end()
        return best_index


def which(filename):

    '''This takes a given filename; tries to find it in the environment path;
    then checks if it is executable. This returns the full path to the filename
    if found and executable. Otherwise this returns None.'''

    # Special case where filename contains an explicit path.
    if os.path.dirname(filename) != '':
        if os.access(filename, os.X_OK):
            return filename
    if 'PATH' not in os.environ or os.environ['PATH'] == '':
        p = os.defpath
    else:
        p = os.environ['PATH']
    pathlist = p.split(os.pathsep)
    for path in pathlist:
        ff = os.path.join(path, filename)
        if os.access(ff, os.X_OK):
            return ff
    return None


def split_command_line(command_line):

    '''This splits a command line into a list of arguments. It splits arguments
    on spaces, but handles embedded quotes, doublequotes, and escaped
    characters. It's impossible to do this with a regular expression, so I
    wrote a little state machine to parse the command line. '''

    arg_list = []
    arg = ''

    # Constants to name the states we can be in.
    state_basic = 0
    state_esc = 1
    state_singlequote = 2
    state_doublequote = 3
    # The state when consuming whitespace between commands.
    state_whitespace = 4
    state = state_basic

    for c in command_line:
        if state == state_basic or state == state_whitespace:
            if c == '\\':
                # Escape the next character
                state = state_esc
            elif c == r"'":
                # Handle single quote
                state = state_singlequote
            elif c == r'"':
                # Handle double quote
                state = state_doublequote
            elif c.isspace():
                # Add arg to arg_list if we aren't in the middle of whitespace.
                if state == state_whitespace:
                    # Do nothing.
                    None
                else:
                    arg_list.append(arg)
                    arg = ''
                    state = state_whitespace
            else:
                arg = arg + c
                state = state_basic
        elif state == state_esc:
            arg = arg + c
            state = state_basic
        elif state == state_singlequote:
            if c == r"'":
                state = state_basic
            else:
                arg = arg + c
        elif state == state_doublequote:
            if c == r'"':
                state = state_basic
            else:
                arg = arg + c

    if arg != '':
        arg_list.append(arg)
    return arg_list

# vi:set sr et ts=4 sw=4 ft=python :
